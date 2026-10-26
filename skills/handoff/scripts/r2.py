#!/usr/bin/env python3
"""Handoff channel client — Cloudflare R2 by default.

    r2.py check                     probe the cloud channel (exit 0 = usable)
    r2.py ls  <主题>                list objects under <prefix><主题>/
    r2.py get <key> [dest]          download one object (dest default: stdout)
    r2.py put <local-file> <key>    upload one object (Content-Type from suffix)
    r2.py rm  <主题>                delete every object under <prefix><主题>/

Every value — provider, endpoint, account, token, bucket, prefix — is read from
`../references/config.md`. Reusing this skill elsewhere is a Markdown edit; this
file needs no changes.

Keys must sit under the configured `prefix`; anything else is refused, so a typo
can never wipe the rest of the bucket.

Exit codes: 0 ok · 1 failure · 2 cloud disabled in config (`provider = none`).
Env overrides for troubleshooting: CF_TOKEN, CF_ACCOUNT_ID.
"""

import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "config.md")
)
BEGIN_MARK, END_MARK = "<!-- handoff-config", "-->"

DEFAULTS = {
    "provider": "cloudflare-r2",
    "api_base": "https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets",
    "account_id": "",
    "token_env": "CF_TOKEN",
    "token": "",
    "bucket": "handoff",
    "prefix": "handoff/",
}

MIME = {
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".json": "application/json",
    ".sh": "text/x-shellscript; charset=utf-8",
    ".py": "text/x-python; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".pdf": "application/pdf",
}


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config(path=CONFIG_PATH):
    """Read the `key = value` block in references/config.md; ignore prose."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die(f"cannot read config {path}: {e}")
    cfg = dict(DEFAULTS)
    if BEGIN_MARK in text:
        body = text.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0]
        for line in body.splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip().strip('"').strip("'")
    return cfg


CONFIG = load_config()
PROVIDER = CONFIG["provider"].strip().lower()
DISABLED = PROVIDER in ("none", "off", "disabled")
BUCKET = CONFIG["bucket"].strip() or DEFAULTS["bucket"]
_raw_prefix = CONFIG["prefix"].strip()
PREFIX_ROOT = "" if _raw_prefix in ("", "/") else _raw_prefix
if PREFIX_ROOT and not PREFIX_ROOT.endswith("/"):
    PREFIX_ROOT += "/"
ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID") or CONFIG["account_id"].strip()
TOKEN = os.environ.get(CONFIG["token_env"].strip() or "CF_TOKEN") or CONFIG["token"].strip()
API = (
    CONFIG["api_base"].strip().rstrip("/").format(account_id=ACCOUNT_ID)
    + f"/{BUCKET}/objects"
)


def require_cloud():
    """Refuse storage commands when the channel cannot possibly work."""
    if DISABLED:
        print(f"cloud disabled: provider = {PROVIDER} in references/config.md", file=sys.stderr)
        sys.exit(2)
    if not TOKEN:
        die(f"no token: set token in references/config.md or export {CONFIG['token_env'] or 'CF_TOKEN'}")
    if not ACCOUNT_ID:
        die("account_id empty in references/config.md")


def check_key(key):
    if PREFIX_ROOT and not key.startswith(PREFIX_ROOT):
        die(f"key must start with {PREFIX_ROOT!r} (got {key!r})")

def request(method, url, data=None, content_type=None):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        die(f"HTTP {e.code} on {method} {url}\n{body}")
    except urllib.error.URLError as e:
        die(f"network error on {method} {url}: {e.reason}")


def object_url(key):
    return f"{API}/{urllib.parse.quote(key, safe='/')}"


def list_keys(prefix):
    """All keys under prefix, following R2's cursor pagination."""
    keys, cursor = [], None
    while True:
        params = {"prefix": prefix, "per_page": "1000"}
        if cursor:
            params["cursor"] = cursor
        url = f"{API}?{urllib.parse.urlencode(params)}"
        _, body = request("GET", url)
        result = json.loads(body)
        if not result.get("success"):
            die(f"list failed: {body.decode('utf-8', 'replace')}")
        keys += [o["key"] for o in result.get("result", [])]
        info = result.get("result_info") or {}
        cursor = info.get("cursor")
        if not info.get("is_truncated") or not cursor:
            return keys


def cmd_check():
    """Read-only probe: can this machine reach the bucket with these credentials?

    Prints one diagnosis line and returns a process exit code. Failure kinds are
    what the caller branches on: disabled / config / auth / network /
    account/bucket / server / api.
    """
    if PROVIDER in ("none", "off", "disabled"):
        print(f"cloud FAIL disabled: provider = {PROVIDER} in references/config.md")
        return 2
    if not TOKEN:
        print(f"cloud FAIL auth: no token (token empty in references/config.md, ${CONFIG['token_env']} unset)")
        return 1
    if not ACCOUNT_ID:
        print("cloud FAIL config: account_id empty in references/config.md")
        return 1

    url = f"{API}?{urllib.parse.urlencode({'prefix': PREFIX_ROOT, 'per_page': '1'})}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"}, method="GET")
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        codes = set()
        try:
            codes = {err.get("code") for err in (json.loads(detail).get("errors") or [])}
        except (json.JSONDecodeError, AttributeError):
            pass
        if e.code in (401, 403) or codes & {9106, 10000}:
            kind = "auth"  # token revoked, mistyped, or missing R2 permission
        elif e.code == 404 and codes & {7003, 10006}:
            kind = "account/bucket"  # wrong account id, or the bucket does not exist
        elif e.code == 404:
            kind = "key"  # object missing
        elif e.code == 429 or e.code >= 500:
            kind = "server"  # Cloudflare-side throttling or outage
        else:
            kind = "http"
        print(f"cloud FAIL {kind}: HTTP {e.code} listing {BUCKET}/{PREFIX_ROOT}")
        print(f"  {detail}")
        return 1
    except urllib.error.URLError as e:
        print(f"cloud FAIL network: {e.reason}")
        return 1

    ms = int((time.time() - started) * 1000)
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        print("cloud FAIL api: non-JSON response")
        return 1
    if not result.get("success"):
        print(f"cloud FAIL api: {str(result.get('errors'))[:300]}")
        return 1
    print(f"cloud ok: {BUCKET}/{PREFIX_ROOT} reachable ({ms} ms)")
    return 0


def cmd_ls(theme):
    prefix = f"{PREFIX_ROOT}{theme}/"
    keys = list_keys(prefix)
    if not keys:
        print(f"(empty) {prefix}")
        return
    for k in keys:
        print(k)


def cmd_get(key, dest):
    check_key(key)
    _, body = request("GET", object_url(key))
    if dest == "-":
        sys.stdout.buffer.write(body)
    else:
        with open(dest, "wb") as f:
            f.write(body)
        print(f"wrote {len(body)} bytes to {dest}", file=sys.stderr)


def cmd_put(local, key):
    check_key(key)
    if not os.path.isfile(local):
        die(f"no such file: {local}")
    ext = os.path.splitext(local)[1].lower()
    content_type = MIME.get(ext) or mimetypes.guess_type(local)[0] or "application/octet-stream"
    with open(local, "rb") as f:
        data = f.read()
    request("PUT", object_url(key), data=data, content_type=content_type)
    print(f"uploaded {len(data)} bytes -> {BUCKET}/{key} ({content_type})")


def cmd_rm(theme):
    prefix = f"{PREFIX_ROOT}{theme}/"
    keys = list_keys(prefix)
    if not keys:
        print(f"(nothing to delete) {prefix}")
        return
    for k in keys:
        request("DELETE", object_url(k))
        print(f"deleted {k}")
    print(f"{len(keys)} object(s) removed from {prefix}")


def main(argv):
    if len(argv) < 2:
        die(__doc__)
    cmd = argv[1]
    if cmd == "check" and len(argv) == 2:
        sys.exit(cmd_check())
    elif cmd == "ls" and len(argv) == 3:
        require_cloud()
        cmd_ls(argv[2])
    elif cmd == "get" and 3 <= len(argv) <= 4:
        require_cloud()
        cmd_get(argv[2], argv[3] if len(argv) == 4 else "-")
    elif cmd == "put" and len(argv) == 4:
        require_cloud()
        cmd_put(argv[2], argv[3])
    elif cmd == "rm" and len(argv) == 3:
        require_cloud()
        cmd_rm(argv[2])
    else:
        die(__doc__)


if __name__ == "__main__":
    main(sys.argv)
