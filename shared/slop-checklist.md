# Slop checklist

Code that compiles but should not exist. Used by the slop-reviewer agent, `/build`, `/cleanup`, and in human review.

- Code nothing calls, or that only tests call
- Interfaces, factories, registries or config keys nobody asked for
- Null checks, `Optional` wrapping and try/catch for cases that cannot happen
- `catch (Exception e)` that logs and carries on
- Helpers that duplicate an existing util
- Comments that narrate the code or its history
- Classes that only forward calls to another class
- Classes that do several unrelated jobs
- Wiring hidden in base classes
- Player-facing text not going through `Translations`
- Magic numbers that should be config, or config that should be a literal
- Tests that assert nothing real, or only that a mock was called
- Names that do not match `CONTEXT.md`
- Docs describing a design the code does not have

If you cannot say in one sentence why a class exists, it goes.

Report each finding as `file:line`, what is wrong, and a concrete failure or cost. At most ten, most important first.
