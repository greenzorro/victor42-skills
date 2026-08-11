# Victor42 · Agent Skills

[![skills.sh](https://skills.sh/b/greenzorro/victor42-skills)](https://skills.sh/greenzorro/victor42-skills)

Agent capability packs — https://skills.victor42.work/

## Install

```bash
# One skill (global)
npx skills add greenzorro/victor42-skills --skill handoff -g

# All skills in this repo
npx skills add greenzorro/victor42-skills -g
```

Skills: `handoff`, `file-image-toolkit`, `poem-six-lens`. Requires [Node.js](https://nodejs.org/) for `npx`.

Detail pages at `skills.victor42.work/<slug>/` also expose a copy-paste install prompt for an AI agent (CLI first; R2 zip as fallback when Node is unavailable).

## Layout

| Path | Role |
|------|------|
| `skills/<name>/` | Skill sources for the [skills CLI](https://github.com/vercel-labs/skills) |
| `data.json` + `scripts/` | Portal content and static page / OG generators |
| `{slug}/index.html` | Generated detail pages (do not edit by hand) |

Maintenance notes: [notes.md](./notes.md).

Created by [Victor42](https://victor42.work/) & [Agent Vik](https://github.com/agent-vik/about-me). MIT licensed.
