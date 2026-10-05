# Step 1: Slice

Turn a feature, PRD or bug report into slices the user can review one at a time.

1. Read the PRD or request. If there is none, ask the user what the feature is for before slicing.
2. Use the `to-issues` skill to propose vertical slices. Each slice:
   - is playable or observable on its own, end to end, not "the data layer" then "the UI"
   - fits in about 400 changed non-test lines. Estimate it from the files it touches
   - depends only on slices before it
3. Show the user the list with titles, one-line goals and size estimates. They pick, merge or split.
4. File each approved slice with `python .claude/pipeline/pipeline.py file-issue --title "..." --body-file <file>`.
   It creates the issue, puts it on the board from `config.json` as TODO, and takes it off projects that auto-add
   new issues. Never use `gh issue create` directly. Leave the acceptance criteria for step 2 unless the user gave them.

When the user starts a slice, create its worktree and branch:

```bash
git fetch origin <base>
git worktree add .claude/worktrees/<issue>-<slug> -b <issue>-<slug> origin/<base>
```

Move its card to In progress.
