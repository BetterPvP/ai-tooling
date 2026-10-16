# Working in BetterPvP

Minecraft plugin suite for a clan PvP network (Paper, Java 21, Gradle, Guice, jOOQ). The project itself is explained in
`docs/ARCHITECTURE.md`. Read it when you need the module map, the build, or how a framework piece works. This file is
how to work here.

## Finding your way

- The module you touch loads its own `CLAUDE.md`. Subsystem write-ups live in `docs/` (listed in `docs/ARCHITECTURE.md`).
  Read the relevant one before changing that subsystem.
- Look up Java symbols with the `intellij` MCP tools (find usages, symbol search, rename) before text search. They
  understand imports and overloads. Fall back to Grep if IntelliJ isn't running.
- Issues, cycles and design docs live in Itsaplan (CLANS project, Itsaplan MCP). Check an initiative's linked docs
  before redesigning something it covers.
- For library behaviour (Paper, Adventure, PacketEvents, jOOQ), use the `paper-researcher` agent or Context7 rather than
  guessing from memory.
- Use the domain terms in `CONTEXT.md` instead of inventing new ones.

## How to work

1. **Act or ask.** When the task is clear, do it end to end. When a choice changes the outcome (API shape, a game rule,
   naming other code depends on), ask first. Never hand back stubs, TODOs for the user, or exercises.
2. **Branch.** Work on the active branch, or the one the user names. Only cut a new branch or worktree when asked.
3. **Verify.** A Stop hook compiles the modules you changed and reports errors. Fix them before finishing. A
   PostToolUse hook flags convention breaks in new code. Fix those too unless one is a genuine exception.
4. **Review.** Before opening a PR, run the `convention-reviewer` agent on the branch and resolve what it finds.
5. **Build.** After a code task, run `./gradlew shadowJar` for the whole suite so `build/` holds a matching set of JARs.
   Skip it for doc-only changes.
6. **Playtesting is the user's.** Never run in-game tests yourself. An Itsaplan issue gets its playtest server when
   it moves to the Playtest column. Deploy to ClansTest-1 only when asked, then tell the user it is ready.
7. **Ship.** Commit and push to the active branch. Open a PR (with the `commit-and-pr` skill) only when the user asks
   for one. The user reviews and merges.
8. **Clean up.** When work in a worktree you created is committed and on the active branch (merged in or pushed),
   remove it with `git worktree remove <path>` and delete its branch with `git branch -d <branch>`. Remove any
   `private/` junction inside it first. Never remove a worktree with uncommitted changes, or one you didn't create.
9. **Track.** For Itsaplan issues, follow the issue's agent prompt for columns, branch and PR. For camps work, update
   the Itsaplan docs "Camps: what we need from the team" and "Camps: features and what's missing" at the end of each
   pass. The Planner agent drafts cycles from them.

## Rules

The code and writing rules live in the ai-tooling repo, linked here:

@.claude/shared/house-rules.md

Keep replies to the user short. No insight boxes.

## Boundaries

- The repo is public and squash-merges. Nothing from `private/` goes into it. `private/` commits go to its own repo.
- New code and writing rules go in ai-tooling `shared/house-rules.md`. Other rules go in this file or a module
  `CLAUDE.md`, not in memory.
