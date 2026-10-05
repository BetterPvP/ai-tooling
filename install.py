"""Installs the pipeline into a BetterPvP checkout.

Links the checkout's `.claude/skills/pipeline` and `.claude/pipeline` to this repo (junctions on Windows, symlinks
elsewhere), merges the hooks and permissions from hooks.json into `.claude/settings.json`, and keeps the links out
of git. Safe to run again.

    python install.py <path to the BetterPvP checkout>
"""
import json
import os
import pathlib
import subprocess
import sys

KIT = pathlib.Path(__file__).resolve().parent
LINKS = {
    pathlib.Path(".claude/skills/pipeline"): KIT / "skill",
    pathlib.Path(".claude/pipeline"): KIT / "scripts",
}
EXCLUDES = ["/.claude/skills/pipeline", "/.claude/pipeline", "/.claude/pipeline-state.json"]


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
    print(f"linked  {path} -> {target}")


def merge_settings(settings_path):
    wanted = json.loads((KIT / "hooks.json").read_text(encoding="utf-8"))
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    for rule in wanted["permissions"]["allow"]:
        if rule not in allow:
            allow.append(rule)
    hooks = settings.setdefault("hooks", {})
    for event, groups in wanted["hooks"].items():
        kept = [g for g in hooks.get(event, [])
                if not any(".claude/pipeline/pipeline.py" in h["command"] for h in g.get("hooks", []))]
        hooks[event] = kept + groups
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"merged  hooks into {settings_path}")


def exclude(checkout):
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=checkout,
                            capture_output=True, text=True, check=True).stdout.strip()
    path = pathlib.Path(common) / "info" / "exclude"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    missing = [e for e in EXCLUDES if e not in lines]
    if missing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines + ["# claude-pipeline"] + missing) + "\n", encoding="utf-8")
    print(f"ok      git excludes in {path}")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    checkout = pathlib.Path(sys.argv[1]).resolve()
    if not (checkout / "settings.gradle.kts").exists():
        sys.exit(f"{checkout} does not look like the BetterPvP checkout.")
    for rel, target in LINKS.items():
        link(checkout / rel, target)
    merge_settings(checkout / ".claude" / "settings.json")
    exclude(checkout)
    print("\nDone. Add the lines from README.md, section 'CLAUDE.md', to the checkout's CLAUDE.md.")


if __name__ == "__main__":
    main()
