# Step 11: Merged

1. Close the issue with `gh issue close <issue> -R mykindos/BetterPvP -c "Merged in #<pr>."`. `Closes #` only
   closes issues on merges into the default branch, and `<base>` is not it.
2. Move the card to Done with the `backlog` skill.
3. Remove the worktree and branch: remove any `private/` junction inside it first, then
   `git worktree remove .claude/worktrees/<issue>-<slug>` and `git branch -D <issue>-<slug>`. The capital `-D` is
   needed because squash merges leave the branch looking unmerged.
4. If the slice finished a feature, mark its PRD as Shipped and delete its implementation plan
   (see [../docs-standard.md](../docs-standard.md)).
