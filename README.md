# AI tooling

Claude Code skills and tools for BetterPvP, shared across machines and the team.

## Install

Needs Python 3.12+ and the GitHub CLI logged in (`gh auth status`).

```bash
git clone https://github.com/BetterPvP/ai-tooling.git
python ai-tooling/install.py <path to the BetterPvP checkout>
```

This links everything into the checkout's `.claude/` folder, adds the hooks to `.claude/settings.json`, and keeps
it all out of the checkout's git. Run it again after pulling.

## Layout

| Folder | Becomes | Holds |
|---|---|---|
| `skills/<name>/` | `.claude/skills/<name>` | a skill, with `SKILL.md` at its root |
| `tools/<name>/` | `.claude/<name>` | scripts, plus an optional `settings.json` with hooks and permissions |

Edits made in the checkout's `.claude/` land in this repo. Commit them here.

## What's here

- **pipeline**: the delivery pipeline. Start it with `/pipeline` in Claude Code. See
  [tools/pipeline/README.md](tools/pipeline/README.md) for its setup.
