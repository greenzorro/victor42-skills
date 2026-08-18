#!/usr/bin/env python3
"""Create or update one secret Gist from a Markdown source file."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.github.com"
TOKEN_NAMES = (
    "COGNITION_SHAPER_GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
)
CUSTOM_TOKEN_PATTERN = re.compile(r"GITHUB_[A-Z0-9_]+_TOKEN")


class GistSyncError(RuntimeError):
    """Raised when the presentation-layer sync cannot be verified."""


def parse_env_file(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    if not path.is_file():
        raise GistSyncError(f"Environment file does not exist: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def discover_env_file(explicit_path: Path | None) -> Path | None:
    if explicit_path is not None:
        return explicit_path.expanduser()

    configured_path = os.environ.get("COGNITION_SHAPER_ENV_FILE")
    if configured_path:
        return Path(configured_path).expanduser()

    search_roots = (Path.cwd(), Path(__file__).resolve().parent)
    checked: set[Path] = set()
    for root in search_roots:
        for directory in (root, *root.parents):
            if directory in checked:
                continue
            checked.add(directory)
            candidate = directory / ".env"
            if candidate.is_file():
                return candidate
    return None


def resolve_token(
    env_file: Path | None,
    token_env: str | None,
) -> tuple[str, str]:
    file_values = parse_env_file(discover_env_file(env_file))
    available = dict(file_values)
    available.update(os.environ)

    if token_env:
        value = available.get(token_env)
        if not value:
            raise GistSyncError(f"Token variable is not set: {token_env}")
        return value, token_env

    for name in TOKEN_NAMES:
        value = available.get(name)
        if value:
            return value, name

    custom_tokens = {
        name: value
        for name, value in available.items()
        if value and CUSTOM_TOKEN_PATTERN.fullmatch(name)
    }
    if len(custom_tokens) == 1:
        name, value = next(iter(custom_tokens.items()))
        return value, name
    if len(custom_tokens) > 1:
        names = ", ".join(sorted(custom_tokens))
        raise GistSyncError(
            f"Multiple custom GitHub token variables found ({names}); "
            "select one with --token-env"
        )

    joined = ", ".join(TOKEN_NAMES)
    raise GistSyncError(
        f"No GitHub token found; expected one of {joined}, "
        "or select a custom GITHUB_*_TOKEN variable with --token-env"
    )


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cognition-shaper-gist-sync",
        }

    def request_json(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = dict(self.headers)
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{API_ROOT}{endpoint}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read()
            try:
                message = json.loads(body).get("message", "unknown GitHub error")
            except (json.JSONDecodeError, AttributeError):
                message = "unknown GitHub error"
            raise GistSyncError(f"GitHub API returned HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise GistSyncError(f"GitHub API connection failed: {exc.reason}") from exc

        if not body:
            return {}
        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise GistSyncError("GitHub API returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise GistSyncError("GitHub API returned an unexpected response shape")
        return result

    def request_text(self, url: str) -> str:
        request = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise GistSyncError(f"Could not read Gist raw content: {exc}") from exc


def normalize_gist_id(value: str) -> str:
    candidate = value.rstrip("/").rsplit("/", 1)[-1]
    if not re.fullmatch(r"[0-9a-fA-F]+", candidate):
        raise GistSyncError("Invalid Gist ID or URL")
    return candidate


def remote_content(
    client: GitHubClient,
    gist: dict[str, Any],
    filename: str,
) -> str:
    files = gist.get("files")
    if not isinstance(files, dict) or filename not in files:
        raise GistSyncError(f"Synced Gist does not contain {filename}")
    file_data = files[filename]
    if not isinstance(file_data, dict):
        raise GistSyncError("Gist file metadata has an unexpected shape")
    if file_data.get("truncated"):
        raw_url = file_data.get("raw_url")
        if not isinstance(raw_url, str):
            raise GistSyncError("Truncated Gist file has no raw URL")
        return client.request_text(raw_url)
    content = file_data.get("content")
    if not isinstance(content, str):
        raise GistSyncError("Gist file has no text content")
    return content


def sync(args: argparse.Namespace) -> dict[str, str]:
    source: Path = args.source
    if not source.is_file():
        raise GistSyncError(f"Source file does not exist: {source}")
    content = source.read_text(encoding="utf-8")
    filename = args.filename or source.name
    if "/" in filename or "\\" in filename:
        raise GistSyncError("Gist filename must not contain path separators")

    token, token_source = resolve_token(args.env_file, args.token_env)
    client = GitHubClient(token)
    identity = client.request_json("GET", "/user").get("login")
    if not isinstance(identity, str):
        raise GistSyncError("Could not identify the GitHub token owner")

    files = {filename: {"content": content}}
    if args.gist_id:
        gist_id = normalize_gist_id(args.gist_id)
        gist = client.request_json(
            "PATCH",
            f"/gists/{gist_id}",
            {"description": args.description, "files": files},
        )
        action = "updated"
    else:
        gist = client.request_json(
            "POST",
            "/gists",
            {
                "description": args.description,
                "public": False,
                "files": files,
            },
        )
        gist_id = gist.get("id")
        if not isinstance(gist_id, str):
            raise GistSyncError("Created Gist response did not include an ID")
        action = "created"

    verified = client.request_json("GET", f"/gists/{gist_id}")
    if remote_content(client, verified, filename) != content:
        raise GistSyncError("Remote Gist content does not match the source file")

    html_url = verified.get("html_url")
    if not isinstance(html_url, str):
        raise GistSyncError("Verified Gist response did not include a URL")
    return {
        "action": action,
        "gist_id": gist_id,
        "html_url": html_url,
        "filename": filename,
        "identity": identity,
        "token_source": token_source,
        "verified": "true",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update one secret Gist and verify exact content.",
    )
    parser.add_argument("source", type=Path, help="Markdown source-of-truth file")
    parser.add_argument("--gist-id", help="Existing Gist ID or URL; omit to create")
    parser.add_argument("--filename", help="Filename shown in the Gist")
    parser.add_argument(
        "--description",
        default="Cognition Shaper living surface",
        help="Gist description",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help=(
            "Optional dotenv file; otherwise use COGNITION_SHAPER_ENV_FILE "
            "or discover .env from the current/script directory ancestry"
        ),
    )
    parser.add_argument(
        "--token-env",
        help=(
            "Token variable to use when the dotenv file contains multiple "
            "custom GITHUB_*_TOKEN values"
        ),
    )
    return parser


def main() -> int:
    try:
        result = sync(build_parser().parse_args())
    except (GistSyncError, OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
