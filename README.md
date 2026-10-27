# Victor42 · Agent Skills

Agent capability packs — https://skills.victor42.work/

## Install

```bash
# One skill (global)
npx skills add greenzorro/victor42-skills --skill handoff -g

# All skills in this repo
npx skills add greenzorro/victor42-skills -g
```

Skills: `handoff`, `file-image-toolkit`, `china-travel-data`, `poem-six-lens`, `cognition-shaper`. Requires [Node.js](https://nodejs.org/) for `npx`.

Detail pages at `skills.victor42.work/<slug>/` also expose a copy-paste install prompt for an AI agent (CLI first; R2 zip as fallback when Node is unavailable).

## Layout

| Path | Role |
|------|------|
| `skills/<name>/` | Skill sources for the [skills CLI](https://github.com/vercel-labs/skills) |
| `data.json` + `scripts/` | Portal content and static page / OG generators |
| `index.html` | Catalog page; embeds a static prerender of the catalog (synced with `data.json` by hand) so no-JS crawlers see full content |
| `{slug}/index.html` | Generated detail pages (do not edit by hand) |

Maintenance notes: [notes.md](./notes.md).

Created by [Victor42](https://victor42.work/) & [Agent Vik](https://github.com/agent-vik/about-me). MIT licensed.
