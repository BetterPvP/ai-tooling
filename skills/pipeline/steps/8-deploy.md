# Step 8: Deploy for the playtest

Only when the user asks. Never run in-game tests yourself.

1. From the slice's worktree: `./gradlew shadowJar`.
2. `python .claude/pipeline/deploy.py` uploads the jars that ClansTest-1 already runs from `build/`, restarts the
   server and waits for it to report running. Staff setup on ClansTest-1 (op, ranks, items) goes through the panel
   console API, as allowed in the user's global instructions.
3. Tell the user it is live and list the `[play]` ACs they need to check.
4. When they say how each went, tick the ones that passed in the PR body (`gh pr edit <n> --body-file`). Ask
   about any AC they did not mention. A failed AC goes back to step 2.

When a playtest fails, the user adds or changes an AC (step 2), and the fix goes through steps 3 to 6 again.
