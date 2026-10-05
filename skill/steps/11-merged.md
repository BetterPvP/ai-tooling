# Step 11: Merged

1. Move the card to Done with the `backlog` skill. The issue closes through `Closes #<issue>`.
2. Remove the worktree and branch: remove any `private/` junction inside it first, then
   `git worktree remove .claude/worktrees/<issue>-<slug>` and `git branch -d <issue>-<slug>`.
3. If the slice finished a feature, mark its PRD as Shipped and delete its implementation plan
   (see [../docs-standard.md](../docs-standard.md)).
