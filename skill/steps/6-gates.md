# Step 6: Gates

CI must be green before the user spends time on the PR. Never ask for a review or merge on a red PR.

1. `gh pr checks <pr> -R mykindos/BetterPvP` shows the state.
2. For a failure, read the log: `gh run view <run-id> -R mykindos/BetterPvP --log-failed`.
3. Fix the cause in the implementation and push. Failing tests mean the code is wrong, since the tests are locked.
4. If a check fails for a reason outside the PR (flaky test, CI outage), tell the user instead of working around it.
