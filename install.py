"""Installs this repo's tooling into a project checkout. Safe to run again.

    python install.py <checkout>

- skills/<name>   -> <checkout>/.claude/skills/<name>
- agents/         -> <checkout>/.claude/agents
- shared/         -> <checkout>/.claude/shared
- tools/<name>    -> <checkout>/.claude/<name>, its settings.json merged into .claude/settings.json and its git-hooks/
                     copied into the checkout's git hooks
- docs/           -> <checkout>/docs

Every link is kept out of the checkout's git. A real folder already at a link's place is left alone and reported.
"""
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent


def link(path, target):
    """Links path to target. Returns False when a real folder or file is in the way."""
    if path.exists() and path.resolve() == target:
        print(f"ok      {path}")
        return True
    if path.is_symlink() or path.is_junction():
        path.unlink()
    elif path.exists():
        print(f"skipped {path}: a real folder is there. Move what it holds into {target}, delete it, run again.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], check=True, capture_output=True)
    else:
        path.symlink_to(target, target_is_directory=True)
    print(f"linked  {path}")
    return True


def merge_settings(settings_path, tool, fragment):
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    allow += [rule for rule in fragment.get("permissions", {}).get("allow", []) if rule not in allow]
    hooks = settings.setdefault("hooks", {})
    marker = f".claude/{tool}/"
    for event in list(hooks):
        hooks[event] = [g for g in hooks[event] if not any(marker in h["command"] for h in g.get("hooks", []))]
        if not hooks[event]:
            del hooks[event]
    for event, groups in fragment.get("hooks", {}).items():
        hooks[event] = hooks.get(event, []) + groups
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"merged  {tool} hooks into {settings_path}")


def git_dir(checkout):
    return pathlib.Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                       cwd=checkout, capture_output=True, text=True, check=True).stdout.strip())


def install_git_hook(checkout, hook):
    """Copies a hook in, unless a hook not installed by this repo is already there."""
    target = git_dir(checkout) / "hooks" / hook.name
    if target.exists() and "ai-tooling" not in target.read_text(encoding="utf-8", errors="ignore"):
        print(f"skipped {target}: a hook is already there. Call {hook} from it yourself.")
        return
    target.write_bytes(hook.read_bytes())
    target.chmod(0o755)
    print(f"hooked  {target}")


def exclude(checkout, paths):
    path = git_dir(checkout) / "info" / "exclude"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    missing = [p for p in paths if p not in lines]
    if missing:
        path.write_text("\n".join(lines + ["# ai-tooling"] + missing) + "\n", encoding="utf-8")
    print("ok      git excludes")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    checkout = pathlib.Path(sys.argv[1]).resolve()
    claude = checkout / ".claude"
    excludes = []
    for skill in sorted(p for p in (REPO / "skills").glob("*") if p.is_dir()):
        link(claude / "skills" / skill.name, skill)
        excludes.append(f"/.claude/skills/{skill.name}")
    for name, place in (("agents", claude / "agents"), ("shared", claude / "shared"), ("docs", checkout / "docs")):
        if (REPO / name).is_dir():
            link(place, REPO / name)
            excludes.append("/" + place.relative_to(checkout).as_posix())
    for tool in sorted(p for p in (REPO / "tools").glob("*") if p.is_dir()):
        link(claude / tool.name, tool)
        excludes.append(f"/.claude/{tool.name}")
        fragment = tool / "settings.json"
        if fragment.exists():
            merge_settings(claude / "settings.json", tool.name, json.loads(fragment.read_text(encoding="utf-8")))
        for hook in sorted((tool / "git-hooks").glob("*")):
            install_git_hook(checkout, hook)
    exclude(checkout, excludes)


if __name__ == "__main__":
    main()
