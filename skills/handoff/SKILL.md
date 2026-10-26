---
name: handoff
description: Use when handing a multi-turn task to another AI agent tool — handoff, 交接, 换 Agent, switching from one tool to Cursor/Claude/GPT/Codex mid-task, or finishing work that came from a handoff package (cleanup rules).
---

# Handoff

## Overview

Create a minimal, temporary handoff package so another AI agent can continue a multi-turn task without losing context.

**Core principle: the package answers one question — "what does the next agent need to keep going?"** Everything else is noise.

Two channels carry the same package. Only its location and its cleanup differ:

| | **Cloud (opt-in)** | **Local directory (default)** |
|---|---|---|
| Lives in | an object-storage bucket at `<prefix><theme>/` | `<dir>/handoff-<theme>/` on this disk |
| Reaches | any machine or agent holding the same credentials | only an agent that can read this disk |
| Needs | network + credentials at both ends | nothing |

The cloud channel ships **off** (`provider = none` in `references/config.md`). Out of the box every handoff is a local directory. Turn cloud on only if you have a Cloudflare R2 (or compatible) bucket and want packages to cross machines.

Choose the channel first (see *Channel Selection*), then follow that channel's section. **One package, one channel — never both.**

When every task named in the package is done, the **receiving agent deletes it**: cloud → every object under the prefix; local → the whole directory. If it cannot reach the location, it asks the user to delete it.

## When to Use

- User explicitly asks for a handoff / 交接 / 切换 Agent
- User is about to switch to a different AI tool (Cursor, Claude, GPT, Codex, etc.) to continue the current task
- A multi-turn task is mid-flight and needs to survive a tool switch
- The cloud channel is unreachable (offline, revoked token, receiving tool can't read the bucket) and the package must still happen

**Do NOT use when:**
- The user just wants to save notes for themselves (tell them to keep personal notes instead)
- No actual tool switch is happening

**Explicit request always wins.** If the user explicitly asks for a handoff on an already-completed task, proceed — the package serves as a final state summary. Note in the `Goal` section that the task is complete. The receiving agent still deletes the package after absorbing it.

## Channel Selection

Decide this before writing anything. The default is probe-first — one API call, and never guess a channel. The only skip is an explicit request for a local package (see the last rules in this section).

**Step 1 — probe the cloud path.**

```bash
python3 <this skill>/scripts/r2.py check
```

Read-only LIST of the configured prefix, ~1 s. Exit 0 = `cloud ok:`. Exit 2 = cloud disabled in config (`provider = none`) → go straight to *Channel B*, no question. Exit 1 prints a failure kind: `config`, `auth`, `network`, `account/bucket`, `server`, `http`, `api`.

**No Python on the box?** Probe with curl instead — take `api_base`, `bucket`, `prefix` and the token from `references/config.md`:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer <token>" \
  "<api_base>/<bucket>/objects?prefix=<prefix>&per_page=1"
```

`200` → reachable · `400`/`403` → `auth` · `000` → `network` · `404` → `account/bucket`. If neither Python nor curl exists, treat the cloud channel as unreachable — do not assume it works.

**Step 2 — check the receiver, not just yourself.** Object storage is usually private and has no public URL, so "reachable" needs both ends:

- **Agent on this machine with shell access** (Cursor, Codex, another CLI tool) → it runs the same `scripts/r2.py` with the same credentials → reachable. A same-machine tool is *not* a reason to go local.
- **Browser tool, or another machine without the credentials** → it cannot GET the package, however green the probe here → not reachable.

Cloud counts as reachable only when **both ends** can reach it.

**Step 3 — decide.**

- **Both ends reachable → cloud.** Proceed into *Channel A*. Do not ask the user which channel; the answer is cloud.
- **Not reachable → stop and ask the user**, with both options in one message plus the probe's failure line:
  - **local package** — write the package to a directory on this machine (*Channel B*)
  - **fix the cloud path** — diagnose and fix now, then use *Channel A*

  Quote the failure kind so the user can judge: `auth` and `account/bucket` are usually a 2-minute config fix; `network` may be a proxy or an offline machine; `server` is not worth waiting for.

**Never silently downgrade to local.** The channel decides where the package lives and who can read it — the user must know which one they got.

**Ask once.** Channel choice, theme, and (in Channel B) target directory can all go in a single message. Do not run three rounds of questions.

**An explicit ask for a local package wins.** If the user says they want it as a folder on disk (moving it to another machine, handing it over by hand), skip the probe and use *Channel B* — no argument, no "cloud would be better".

**If the user delegates the decision** ("you decide"), take the local package and say so in one line: it is the option that cannot fail for lack of credentials or network.

**If the chosen channel breaks mid-flight** (token revoked, network dies, machine goes offline), do not patch a half-finished package. Delete whatever landed, then either retry once the cause is cleared or rebuild in the other channel — and say in one line which copy you deleted. One live copy at a time.

## Channel A — Cloud (opt-in)

### Setup (one time)

Skip this section entirely if you left `provider = none`.

1. Create a bucket, and an API token with object read/write on that bucket.
2. Fill the `handoff-config` block in `references/config.md`: `provider = cloudflare-r2`, `account_id`, `bucket`, `prefix`, and the token (or export the environment variable named by `token_env` instead of storing it).
3. `python3 scripts/r2.py check` must print `cloud ok:`.

Bundled files:

- `references/config.md` — **the only config source**: provider, endpoint, account, token, bucket, prefix, default local dir
- `references/r2.md` — REST shapes, MIME table, probe/troubleshooting playbook
- `scripts/r2.py` — `check` / `ls` / `get` / `put` / `rm`, reading every value from `config.md` (refuses keys outside the configured prefix, percent-encodes keys)

### Destination and naming

- **Bucket**: the configured `bucket`. Never write handoffs into a bucket you did not configure.
- **Prefix**: the configured `prefix` + `<theme>/` (shipped default `handoff/<theme>/`) — flat, one theme per package.
- **Theme**: theme name only — no date, no slug, no extra prefixes (including no leading `handoff-`).
- **The theme is chosen by the user, not you.** If the user did not specify one:
  1. Ask directly: "What should the handoff be called?"
  2. If they want suggestions, propose 2-3 candidates based on the current task
  3. Never invent a theme name silently — always confirm before uploading

**Structural rules vs a literal name from the user.** No date, no slug, no leading `handoff-` are defaults you enforce. If the user hands you a name that violates them (`handoff-blog-20260707`), propose the nearest legal name (`blog`) and confirm in one question — never silently rewrite a name they typed. If they insist, use their name: it still sits under the configured prefix, which is the only hard boundary. One clarification, then drop it.

**Reading the rest of this document:** `handoff/` stands for the configured `prefix`. If `config.md` says otherwise, config wins and this prose is stale — fix the prose (Markdown only, never the script).

**Examples of correct keys:**

- `handoff/blog-seo/notes.md`
- `handoff/bugfix-login/notes.md`
- `handoff/refactor-auth/notes.md`

**Examples of wrong keys:**

- `handoff/handoff-blog-seo/notes.md` (theme must not start with `handoff-`)
- `handoff/blog-seo-20260707/` (has date)
- any key outside the configured prefix

### Staging and upload

1. Optionally stage files in a scratch directory (`mktemp -d` is fine — what matters is the uploaded keys, not the staging path).
2. Upload every package file with keys `<prefix><theme>/<filename>`. Set the correct `Content-Type` (e.g. `text/markdown; charset=utf-8` for `notes.md`).
3. Verify what landed: `scripts/r2.py ls <theme>` must list every intended key. The package counts as created only then — a half-finished upload is worse than none, so delete the strays before retrying.
4. Local scratch is disposable after a successful upload.
5. Tell the user: bucket, prefix, and done.

## Channel B — Local directory

Use when the cloud probe failed or is disabled, the receiving tool cannot read the bucket, or the user asked for a folder outright.

### Location and naming

- **Location**: if `local_root` is set in `references/config.md`, use it and say so. Otherwise ask the user — detect the OS and offer:

  | OS | Suggestions |
  |----|-------------|
  | **macOS** | `~/Desktop` · `~/Downloads` · `~/Documents` |
  | **Windows** | `%USERPROFILE%\Desktop` · `%USERPROFILE%\Downloads` · `%USERPROFILE%\Documents` |
  | **Linux / WSL** | `~/Desktop` (if it exists) · `~/Downloads` · `~/` |

- **Format**: `handoff-<theme>` — the `handoff-` prefix lives here because a bare directory name carries no channel marker. No date, no slug, no nesting under another parent.
- **Theme**: same rule as cloud — plain theme, chosen by the user, never invented silently.

**Correct:** `~/Desktop/handoff-blog-seo/`
**Wrong:** `~/Desktop/handoffs/blog-seo/` (nested) · `~/Desktop/handoff-blog-seo-20260707/` (dated) · `~/Desktop/_handoff/blog-seo/` (nested)

### Create

1. `mkdir <chosen-path>/handoff-<theme>/`
2. Write `notes.md` there
3. Add non-narrative attachments only if justified, referenced from `notes.md`
4. Confirm the file exists and reads back before handing over

### Delivery

State which case applies — the package is useless if it never reaches the other side:

- **Agent on this machine** (Cursor, another CLI tool) → hand over the absolute path. Done.
- **Browser tool** (ChatGPT web, a chat UI with no shell) → it cannot read the disk. The user pastes the `notes.md` body into that tool and attaches extra files by hand. The package is built for exactly this: one narrative file that carries everything.
- **Agent on another machine** → the user moves the directory themselves (on WSL, prefer a path the other side can open, e.g. `/mnt/c/Users/<username>/Desktop`). There is no shared storage to fall back on.

## Receiving and cleanup (either channel)

The receiver may never have seen this skill — everything it needs must be inside `notes.md`. Its job:

1. Locate the package: `scripts/r2.py ls <theme>` for cloud, or open the directory the user named.
2. Read `notes.md` first, then any sibling file it references (cloud: fetch from the same prefix).
3. Do the work named in Goal / open items.
4. When **all tasks named in the package are done**, delete it: `scripts/r2.py rm <theme>` for cloud, the whole `handoff-<theme>/` directory for local (the environment's trash command beats `rm -rf` where one exists).
5. Say in one line that the package was removed.

**If the receiver cannot reach the package location** (browser tool, another machine), deleting is impossible: ask the user to delete it instead, and never report it as removed.

**Done means:** Goal satisfied and every open item closed (or explicitly dropped with user agreement). Do not delete mid-flight.

## The notes.md

Use this exact structure. Do not add sections. Do not rename sections. The `Cleanup` line is the only channel-dependent part — keep the branch that matches the channel and drop the other.

```markdown
# <theme> Handoff

Created: YYYY-MM-DD
Triggered by: user request
Receiving agent: <unspecified / the named tool>

## Goal
<One sentence. If there is a red line that cannot be automated, one more sentence right after.>

## Context
<Traps the next agent will hit, premises it will misread. Only implicit knowledge that cannot be recovered by reading the source files. No obvious background.>

## Current State
- Done: <concrete facts, with file paths>
- Verified: <with a reproducible command>
- Open: <the concrete next steps>

## Handoff Notes
<What the receiving agent must know. Direct tone, like a note to a colleague.>

## Cleanup
When every task in this package is done, delete <cloud: all objects under the configured prefix for this theme | local: this directory handoff-<theme>/>; if the receiver cannot reach that location, the user deletes it.
```

### Writing principles

**Write less, not more.** A 20-line notes.md that nails the essentials beats a 200-line one padded with background. The next agent can read source files — don't copy their contents into notes.md.

**Reference, don't duplicate.** When mentioning files the receiver can reach, write durable paths or URLs. Do not paste file contents, diffs, or code into notes.md. The only exception: a short inline snippet (< 5 lines) that illustrates a non-obvious point.

**State the implicit.** The highest-value content in Context and Handoff Notes is the stuff that ISN'T in the code: design decisions and their rationale, traps, conventions, "don't touch X because Y".

**No section is mandatory if empty.** If there is nothing to say in Context, write `<none>` rather than padding. Cleanup is never empty — it always names the exact thing to delete, and who deletes it when the receiver can't.

## What NOT to Do

These are the failure modes observed in testing. Avoid them:

1. **Do not create narrative-redundant files.** No `README.md`, no `todo.md`, no `summary.md`, no `diff.patch`. They duplicate notes.md in another package. The only valid extra files are non-narrative content (executable scripts, structured data, long logs) — and each must be referenced in notes.md.

2. **Do not copy or snapshot source files** that the receiver can already reach. Reference paths only. The time window between handoff and the next agent picking up is short; source files will not change.

3. **Do not write operating instructions for the receiving agent.** notes.md is a state snapshot, not a tutorial. The next agent knows how to do its job — it just doesn't know the state of THIS task. The Cleanup section only records the delete duty already defined by this skill.

4. **Do not add a date to the package name** (`<prefix><theme>/` or `handoff-<theme>/`). The package is temporary and will be deleted. Dating implies archival; this is not an archive.

5. **Do not ask more than necessary.** If the user gave enough context in the trigger message, proceed. Only ask when genuinely blocked. A missing theme is always worth asking; a missing location is worth asking only in Channel B.

6. **Do not treat this as session memory or identity persistence.** This is task-state transfer, nothing more. Do not write about "who you are" or general preferences — that belongs in agent memory, not here.

7. **Do not write outside the configured bucket and prefix.** No "just this once" keys.

8. **Do not double the channel marker by default.** Cloud keys never start with `handoff-` (the prefix already says it); local directories always do (nothing else says it). `handoff/handoff-x/` and `~/Desktop/x/` are both wrong names by default — if the user insists on their own, theirs wins; the configured prefix is the only hard boundary.

9. **Do not leave copies behind.** When the package's tasks are all done, the receiving agent deletes it — in storage or on disk. If the channel changes mid-flight, delete the old copy in the same breath as creating the new one. One live copy, ever.

10. **Do not silently downgrade to local**, and do not pick a channel the user never chose. Probe result → user's choice → then write. If the user hands you the decision, take local and say which channel you took.

## Lifecycle

1. Probe the cloud channel, pick the channel with the user if it fails
2. Creating agent writes the package to that channel (`<prefix><theme>/` in the bucket, or `handoff-<theme>/` on disk)
3. Receiving agent reads `notes.md` first, finishes the named work
4. Receiving agent deletes the package (prefix objects or directory), then tells the user it was removed — or asks the user to delete it when it cannot reach the location
5. No index, no registry, no archive — each handoff is independent

If another handoff is needed later, the user triggers this skill fresh — a new package, with no reference to the previous one.

## Execution Checklist

### Choosing a channel

1. Run `scripts/r2.py check`; note exit code and failure kind (skip only if the user already asked for a local package)
2. Confirm the receiving agent can reach the same channel
3. Both ends reachable → Channel A, no question. Exit 2 (cloud disabled) → Channel B, no question. Otherwise → ask the user: local package or fix the cloud path

### Creating a package — cloud

1. Confirm theme name with user (ask if not specified)
2. Write `notes.md` in a scratch dir (`mktemp -d` is fine)
3. If any non-narrative content genuinely needs a separate file, add it and reference it in notes.md
4. Upload with `scripts/r2.py put <file> <prefix><theme>/<filename>` (config is bundled; `references/r2.md` has the details)
5. `scripts/r2.py ls <theme>` — every intended key present
6. Tell the user bucket + prefix, and stop

### Creating a package — local

1. Confirm theme name and target directory with user (offer OS-appropriate suggestions)
2. `mkdir <chosen-path>/handoff-<theme>/`, write `notes.md`
3. Add justified attachments, referenced from `notes.md`
4. Tell the user the absolute path and how it reaches the receiver (same-machine path / paste into a browser tool / move to another machine)

### Finishing a package (receiving agent)

1. Confirm Goal and every open item are done (or explicitly dropped with user agreement)
2. Delete the package: `scripts/r2.py rm <theme>` for cloud, delete the directory for local
3. Tell the user the package was removed — or, if it can't reach the location, ask the user to delete it

That is the entire job. No follow-up actions, no verification loops, no "anything else?"
