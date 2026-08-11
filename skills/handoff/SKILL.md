---
name: handoff
description: Use when transitioning a multi-turn task to another AI agent tool — handoff, 交接, 换 Agent, 切换 Claude/GPT/Cursor. Triggers only on explicit user request to create a handoff package. Use when the user says "做个交接", "给我一个 handoff", "我要换 Agent 了", or otherwise indicates they want to pass the current task state to a different agent tool.
---

# Handoff

## Overview

Create a minimal, temporary handoff package that lets another AI agent continue a multi-turn task without losing context.

**Core principle: the handoff package answers one question — "what does the next agent need to keep going?"** Everything else is noise.

## When to Use

- User explicitly asks for a handoff / 交接 / 切换 Agent
- User is about to switch to a different AI tool (Cursor, Claude, GPT, Codex, etc.) to continue the current task
- A multi-turn task is mid-flight and needs to survive a tool switch

**Do NOT use when:**
- The user just wants to save notes for themselves (tell them to use a notebook)
- No actual tool switch is happening

**Explicit request always wins.** If the user explicitly asks for a handoff on an already-completed task, proceed — the package serves as a final state summary. Note in the `Goal` section that the task is complete.

## What to Produce

One directory. `notes.md` is always required and is the entry point.

```
<chosen-path>/handoff-<主题>/
├── notes.md          (always)
└── <other-files>     (only when justified, see below)
```

**Default to notes.md only.** Add a separate file only when a piece of content is *non-narrative by nature* — i.e., it's consumed as a tool or dataset, not read as prose. Legitimate cases:

- **Executable scripts** (`verify.sh`, `repro.py`) the receiving agent should run directly
- **Structured data** (CSV samples, JSON configs, test matrices) the receiving agent will *parse programmatically* — not a short list of paths or names, which stay inline in notes.md
- **Long logs / stack traces** (> 30 lines) that would break notes.md's reading flow

Every extra file must be **referenced and explained** inside notes.md (what it is, when to use it). An unreferenced orphan file is a violation.

**Copy into the handoff directory, or reference the original path?** Decide by where the source lives:

- Source in an ephemeral location (a temp directory, `/tmp/`, or scratch space) → **copy in**. The path will go stale.
- Source in a project repo or persistent storage → **reference the absolute path**. Don't duplicate.

**Never create these** — they're narrative redundancy, the same information as notes.md in a different package:
- `README.md`, `todo.md`, `summary.md`, `changelog.md`
- `paths.txt`, `index.json`
- `diff.patch` / `changes.diff` (use git directly; reference the commit/branch in notes.md)

### Directory location and naming

- **Location**: ask the user where to put the handoff package. Detect the current OS and recommend common locations (see table below). Let the user pick one or specify a custom path.
- **Format**: `handoff-<主题>` — no date, no slug, no extra prefixes
- **主题 is chosen by the user, not you.** If the user did not specify a theme:
  1. Ask the user directly: "交接主题叫什么？"
  2. If they want suggestions, propose 2-3 candidates based on the current task
  3. Never invent a theme name silently — always confirm before creating the directory

**Recommended locations by OS:**

Detect the current OS first, then present 2-3 of these options to the user:

| OS | Recommended locations |
|----|-----------------------|
| **macOS** | `~/Desktop` (桌面) · `~/Downloads` (下载) · `~/Documents` (文档) |
| **Windows** | `C:\Users\<username>\Desktop` (桌面) · `C:\Users\<username>\Downloads` (下载) · `C:\Users\<username>\Documents` (文档) |
| **Linux / WSL** | `~/Desktop` (桌面，若存在) · `~/Downloads` (下载) · `~/` (家目录) |

If the user does not pick from the recommendations, ask them to specify a directory. **Never silently invent a location** — always confirm before creating the directory.

**Examples of correct paths:**
- `~/Desktop/handoff-blog-seo/`
- `~/Downloads/handoff-bugfix-login/`
- `~/Documents/handoff-refactor-auth/`

**Examples of wrong paths:**
- `~/Desktop/handoffs/blog-seo/` (nested)
- `~/Desktop/handoff-blog-seo-20260707/` (has date)
- `~/Desktop/_handoff/blog-seo/` (nested under parent)

## The notes.md

Use this exact structure. Do not add sections. Do not rename sections.

```markdown
# <主题> Handoff

Created: YYYY-MM-DD
Triggered by: 用户主动触发
Receiving agent: <未指定 / 用户指定的工具>

## Goal
<一句话目标。如果存在不可自动化的红线，紧跟一句说明。>

## Context
<下一个 Agent 会踩的坑、会误解的前提。只写不读源文件就无从得知的隐性知识。不写显而易见的背景。>

## Current State
<分三类，每类用列表：>
- 已完成：<具体的事实，带文件路径>
- 已验证：<带可复现命令>
- 待办：<明确的下一步>

## Handoff Notes
<写给接手 Agent 的关键注意事项。语气直接，像给同事留便签。>

## Cleanup
用户手动删除本目录。
```

### Writing principles

**Write less, not more.** A 20-line notes.md that nails the essentials beats a 200-line one padded with background. The next agent can read source files — don't copy their contents into notes.md.

**Reference, don't duplicate.** When mentioning files, write absolute paths. Do not paste file contents, diffs, or code into notes.md. The only exception: a short inline snippet (< 5 lines) that illustrates a non-obvious point.

**State the implicit.** The highest-value content in Context and Handoff Notes is the stuff that ISN'T in the code: design decisions and their rationale, traps, conventions, "don't touch X because Y".

**No section is mandatory if empty.** If there is nothing to say in Context, write `<无>` rather than padding. An empty Cleanup section never happens — it always says the same thing.

## What NOT to Do

These are the failure modes observed in testing. Avoid them:

1. **Do not create narrative-redundant files.** No `README.md`, no `todo.md`, no `summary.md`, no `diff.patch`. They duplicate notes.md in another package. The only valid extra files are non-narrative content (executable scripts, structured data, long logs) — and each must be referenced in notes.md.

2. **Do not copy or snapshot source files.** Reference paths only. The time window between handoff and the next agent picking up is short; source files will not change.

3. **Do not write operating instructions for the receiving agent.** notes.md is a state snapshot, not a tutorial. The next agent knows how to do its job — it just doesn't know the state of THIS task.

4. **Do not add a date to the directory name.** The directory is temporary and will be deleted. Dating implies archival; this is not an archive.

5. **Do not ask more than necessary.** If the user gave enough context in the trigger message, proceed. Only ask when genuinely blocked. When the theme name or location is missing, that is always worth asking.

6. **Do not treat this as session memory or identity persistence.** This is task-state transfer, nothing more. Do not write about "who you are" or general preferences — that belongs in agent memory, not here.

## Lifecycle

This skill only creates the handoff package. It does not:

- Delete it (user does this manually when the receiving agent is done)
- Track it (no index, no registry)
- Link it to previous or future handoffs (each is independent)
- Archive it when complete (user just deletes the directory)

If the receiving agent later needs to hand off again, the user triggers this skill fresh — a brand new `handoff-<主题>/` is created, with no reference to the previous one.

## Execution Checklist

When triggered:

1. Confirm theme name with user (ask if not specified)
2. Ask user where to put the handoff package; detect OS and recommend 2-3 common locations (桌面 / 下载 / 文档); let the user pick or specify a custom path
3. Create `<chosen-path>/handoff-<主题>/`
4. Write `<chosen-path>/handoff-<主题>/notes.md` using the template above
5. If any non-narrative content (scripts, data, logs) genuinely needs a separate file, add it and reference it in notes.md
6. Tell the user the path and stop

That is the entire job. Five steps. No follow-up actions, no verification loops, no "anything else?"
