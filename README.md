# AI tooling

Claude Code tooling and system docs for BetterPvP, shared across machines and the team.

![Delivery flow](delivery-flow.png)

The editable diagram is at https://draw.brauw.dev/editor/1402245d-a973-49f7-b884-d83ee368f510. Update
`delivery-flow.png` with an export when it changes.

## Install

Needs Python 3.12+ and the GitHub CLI logged in (`gh auth status`).

```bash
git clone https://github.com/BetterPvP/ai-tooling.git
python ai-tooling/install.py <path to the BetterPvP checkout>
```

This links everything into the checkout and keeps it out of the checkout's git. Run it again after pulling. Then make
sure the checkout's `CLAUDE.md` imports the house rules with the line `@.claude/shared/house-rules.md`.

## Layout

| Folder | Becomes | Holds |
|---|---|---|
| `skills/<name>/` | `.claude/skills/<name>` | `/cleanup`, `/gui` and the project skills |
| `agents/` | `.claude/agents` | `slop-reviewer`, `convention-reviewer` and the project agents |
| `shared/` | `.claude/shared` | house rules, slop checklist, `project.json`, `deploy.py` |
| `tools/<name>/` | `.claude/<name>` | scripts, plus an optional `settings.json` (Claude hooks) and `git-hooks/` |
| `docs/` | `docs/` | the system docs |

Edits made through the checkout land in this repo. Commit them here.

## Config

`shared/project.json` sets the repo, the base branch (change `base` when the season branch changes) and the PR size
limit. Issues, cycles and planning live in Itsaplan (plan.brauw.dev).

For deploys, set `PTERODACTYL_API_KEY`, or sign in to the 1Password CLI with access to
`op://Claude/pterodactyl-betterpvp/credential`.
