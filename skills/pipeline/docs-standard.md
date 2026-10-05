# Docs standard

## Where each doc lives

| Type | Home | Holds | Cap |
|---|---|---|---|
| PRD | Outline, Document Hub | what players get and why, numbered requirements | 2 pages |
| Status page | Outline, Document Hub, under its PRD | checklists of progress and team needs | short |
| ADR | Outline, Engineering | one decision, its context and consequences | 1 page |
| Plan | Outline, Engineering | phases mapped to issues | deleted when done |
| System doc | `docs/<module>-<subsystem>.md` | how the code works now | 300 lines |

Lore and balance docs stay in the Document Hub. They are the only docs written in the game's fiction.

## Rules

- Every doc starts with a header: Status (Draft, Approved, Shipped, Superseded), Owner, Last verified (date, and
  commit for system docs).
- One topic per doc. Over its cap, split it into child docs.
- Each fact lives in one place. Link to it, never copy it.
- Status (checklists, progress) stays out of design docs.
- Titles are "Area: topic". No version numbers in titles.
- Plain short sentences in the present tense, describing the end state. No em-dashes or semicolons.
- Each Outline area has one index page linking its docs.
- An approved ADR is never edited. A new ADR supersedes it.
- A plan is deleted once its last PR merges. A shipped PRD is marked Shipped.
- Use the `outline-scribe` agent for Outline writes.

## Templates

PRD:

```
Status: Draft · Owner: <name> · Last verified: <date>

## Problem
## Player goals
## Requirements
R1 ...
## Out of scope
## Open questions
## Links
```

ADR:

```
Status: Approved · Date: <date>

## Context
## Decision
## Consequences
```

Plan:

```
Status: Active · PRD: <link>

## Phases
1. <issue link>
```

System doc:

```
Status: Approved · Last verified: <date>, <commit>

## Purpose
## Main types
## How it works
## Extending it
## Gotchas
```

Status page:

```
PRD: <link>

## Done
## In progress
## Needs from the team
```
