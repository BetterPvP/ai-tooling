---
name: doc
description: >
  Drafts a doc from the right template and puts it in its home. Use when the user runs /doc, or asks to write, draft,
  update or clean up a PRD, ADR, implementation plan, system doc or status page.
---

# /doc <type> <topic>

Types: `prd`, `adr`, `plan`, `system`, `status`. The homes, rules and templates are in
`.claude/shared/doc-templates.md`. Read it first and follow it exactly.

## Steps

1. If the type is missing, infer it from the topic and confirm with a card.
2. Gather what the doc needs: the PRD and issues for plans and status pages, the code for a system doc, the user's
   decision for an ADR. Ask with a card for anything only the user knows. Keep it to the questions that change the
   doc.
3. Draft from the template with `Status: Draft`. Stay under the type's cap. If it will not fit, propose child docs.
4. Show the draft and ask with a card: Save · Change.
5. Save it in its home:
   - PRD, status page, lore: Outline, Document Hub, under the area's index page.
   - ADR, plan: Outline, Engineering.
   - System doc: ai-tooling `docs/<module>-<subsystem>.md`, committed and pushed in ai-tooling.

   Use the `outline-scribe` agent or the outline tools for Outline.
6. Ask with a card: Mark Approved · Leave as Draft.

To update an existing doc, read it, change only what the topic needs, and bump "Last verified".
