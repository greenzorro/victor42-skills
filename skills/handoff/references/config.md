# Configuration

The single source of truth for this skill. Reusing it on another machine, or pointing it at your own storage, means editing the block below — the scripts never change.

```text
<!-- handoff-config
provider   = none
api_base   = https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets
account_id =
token_env  = CF_TOKEN
token      =
bucket     = handoff
prefix     = handoff/
local_root =
-->
```

## Keys

| Key | Meaning | What changes when you edit it |
|-----|---------|-------------------------------|
| `provider` | `cloudflare-r2` or `none` | `none` disables the cloud channel: `check` exits 2 and every package goes local. This is the shipped default |
| `api_base` | REST prefix; `{account_id}` is substituted | Point at a compatible gateway (a different auth scheme would still need script changes — out of scope) |
| `account_id` | Cloudflare account ID | A typo makes `check` report `account/bucket` |
| `token_env` | Name of the environment variable to read the token from | Use your own variable name instead of `CF_TOKEN` |
| `token` | Inline token; the env var wins | Empty means "only the env var". Never commit a real token |
| `bucket` | Bucket name | `check`/`ls`/`put`/`rm` follow it |
| `prefix` | Key prefix, trailing `/` preferred | `packages/` writes to `packages/<theme>/`. Use `/` for the bucket root on a dedicated bucket |
| `local_root` | Default directory for local packages | `~/Desktop` stops the per-handoff question; empty asks each time |

## Rules

1. **Precedence:** environment variable > this file > built-in defaults. `CF_TOKEN` / `CF_ACCOUNT_ID` let you try another credential without editing anything (troubleshooting).
2. **Edit values, not key names.** Text outside the block is ignored; `#` starts a comment inside it.
3. `bucket`, `prefix` and `local_root` must match the prose in `SKILL.md`. After changing them, search `SKILL.md` for the old values — that is a wording-consistency chore, not a code change.
4. **Turning cloud on:** set `provider = cloudflare-r2`, fill `account_id` and `bucket`, supply the token (inline or via `token_env`), then run `scripts/r2.py check` until it prints `cloud ok:`.
5. **Never leave a real token in a shared copy.** For a public release: `provider = none`, `token =` empty.
