"""Installs this repo's skills and tools into a project checkout. Safe to run again.

    python install.py <checkout>

- skills/<name> is linked as <checkout>/.claude/skills/<name>
- tools/<name> is linked as <checkout>/.claude/<name>, and its settings.json (hooks, permissions) is merged into
  <checkout>/.claude/settings.json
- tools/<name>/git-hooks/* are copied into the checkout's git hooks
- every link, and any .claude/*-state.json file, is kept out of the checkout's git
"""
import json
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent


def link(path, target):
    if path.exists() and path.resolve() == target:
        print(f"ok      {path}")
        return
    if path.is_symlink() or path.is_junction():
        path.unlink()
    elif path.exists():
        sys.exit(f"{path} exists and is not a link. Move it away, then run this again.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], check=True, capture_output=True)
    else:
        path.symlink_to(target, target_is_directory=True)
    print(f"linked  {path}")


def merge_settings(settings_path, tool, fragment):
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    allow += [rule for rule in fragment.get("permissions", {}).get("allow", []) if rule not in allow]
    hooks = settings.setdefault("hooks", {})
    marker = f".claude/{tool}/"
    for event, groups in fragment.get("hooks", {}).items():
        kept = [g for g in hooks.get(event, []) if not any(marker in h["command"] for h in g.get("hooks", []))]
        hooks[event] = kept + groups
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
    print(f"ok      git excludes")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    checkout = pathlib.Path(sys.argv[1]).resolve()
    claude = checkout / ".claude"
    excludes = ["/.claude/*-state.json"]
    for skill in sorted(p for p in (REPO / "skills").iterdir() if p.is_dir()):
        link(claude / "skills" / skill.name, skill)
        excludes.append(f"/.claude/skills/{skill.name}")
    for tool in sorted(p for p in (REPO / "tools").iterdir() if p.is_dir()):
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
