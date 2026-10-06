---
name: gui
description: >
  Designs and builds polished player-facing GUIs (inventory menus and dialog screens) with the user reviewing every
  stage: theme, brief, wireframe alternatives, hi-fi mockup on a Claude Design canvas, textures, code, playtest. Owns
  the project's visual theme and sets it up on first use. Use when the user runs /gui, asks to design, build, redesign
  or restyle a menu, GUI, dialog or screen, asks what a screen should look like, or wants to set or change the UI
  theme.
---

# /gui <screen>

Every decision goes to the user on an AskUserQuestion card. Never pass a stage the user has not approved. When you
show options, always show at least two real alternatives and say which one you would pick and why in one line.

Read before starting: `docs/ui-theme.md` (the visual theme and its implementation map), `docs/ui-style.md` (text,
colour of messages, lore rules), `references/surfaces.md` (what inventories and dialogs can and cannot do), and for
any dialog `docs/core-gui-screens.md` (how dialog screens are built: screen files, the schema, actions, the pack
generator) and `references/dialogs.md` (why the client limits what they can do).

## 0. Theme

- `docs/ui-theme.md` missing, or its Status is not Approved: run theme setup (`references/theme.md`) first, then come
  back. The user can also ask for it on its own ("set up the theme", "change the theme").
- Otherwise read its Design System link (`Artifact` read of `project/README.md` and `project/tokens.json`) and use it
  for everything below. If the screen needs a component the theme lacks, design it in this pass and add it at step 8.

## 1. Brief

Gather, from the user and the code, and confirm in one card (Use this · Change):

- What the screen is for, who opens it, from where (NPC, item, command, another menu).
- What it shows (real data, with the largest realistic values) and what the player can do.
- Live data that changes while it is open.
- Surface: inventory, dialog, or both chained. If the user named one, that is the surface, even when another seems
  easier. Otherwise recommend one from `references/surfaces.md` and say why. Dialogs are the first choice for
  composed, full-screen screens: a screen file (`docs/core-gui-screens.md`) places art and click regions anywhere,
  which inventories cannot.

If the screen exists, read its code and show what it looks like now (ask the user for a screenshot).

## 2. References (only when the user has no picture in mind)

Find 4 to 6 real examples of comparable screens (other servers, games, Dribbble or Pinterest game UI) with WebSearch,
and open the best in the browser pane. Group them into 2 or 3 directions, name each, and ask which to follow. Do not
copy another server's art. Use references for layout and feel only.

## Designing a dialog

A dialog is a screen file (`docs/core-gui-screens.md`). Every design, from the first wireframe, is built only from
what a screen file can express. Check each layout against this list before showing it, and name on the canvas the
element each part becomes (`button`, `repeat`, `switch` and so on).

- **Click targets** are of two kinds. Canvas elements: `text`, `button` and `icon` anywhere on the canvas, each with
  its own `on_click` and tooltip. Their hit area is the drawn glyphs, so a button is its art plus its label. Native
  buttons: 20 px tall, only the footer `exit` or the `buttons` grid below the canvas. Prefer canvas buttons for tabs,
  cards, slots and in-panel buttons. Use native buttons for close, back and confirm bars.
- **Hover**: a canvas button can show hover art pinned over it (`"hover": "rim"` or another hover style), which
  replaces its tooltip. Other elements show a tooltip. Native buttons use the theme's highlighted sprite. Pressed art
  (`"pressed": true`) shows for a moment after a click.
- **Tabs and states** are a `switch` on a state key, with buttons that `set` it. Lists are a `repeat` with a `max`.
  Repeated parts are components (`use`).
- **Animation**: an `icon` with `frames` and `fps` loops on the client. Anything else that changes does so by
  re-rendering after an action.
- **Size**: a full-screen dialog is a canvas of up to 460x189, the most a 480x270 screen (GUI scale 4 at 1080p)
  shows without scrolling. Taller fails the build: a scrolled body moves away from its hover art. The art (panel,
  wells, cards) is `box` elements in the canvas, so it moves with the canvas at every GUI scale.
- **Proportions**: in game the 1 px outline is inside a box, in the mockups it is outside, so an in-game size is the
  mockup size plus 2. Start from a `panel_header` box at y 5 (a 22 px header band): the title text at y 13 and 16 px
  tabs at y 9, centred in the band on the row after the box, the tabs right after the title. Tabs and buttons take
  `"width": "auto"` (padding 5 for tabs, 6 for buttons) in a row with `"cell": ["auto", h]`, so they size to their text
  in each language. Buttons are 20 px tall, wells and cards sit 8 px in from the panel edge.
- **Backdrop** art goes in the title, behind the canvas, and is never clipped or clickable. It only lines up while the
  canvas is at most 174 px tall, and its boxes may not overlap. Use it only for small screens.
- **Inputs** (text, toggles, sliders, choices) sit below the canvas, in a column. They cannot go inside the art.
- **Text** leaves room for the longest translation (German and Russian run about 30% longer), since an element wider
  than the canvas fails. Arabic and CJK text snaps to 9 px rows.
- **Live values** update by re-sending the screen, which resets scroll. Design screens that do not scroll.
- **Draw order**: lower 9 px rows draw over higher ones. Within one row, overlapping pieces draw in no fixed order, so
  anything drawn over a box starts on a later row than the box (tabs at y 9 over a panel at y 0, text at y 45 over a
  well at y 36). The pack build fails on a layout that breaks this.

## 3. Wireframes

Create one Claude Design canvas per screen (Design type, title `GUI: <screen>`), following `references/mockups.md`.
Draw 2 or 3 low-fidelity layouts that differ in structure, not colour: what is primary, where navigation lives, how
much fits. Grey boxes, real labels, real data, true game scale. For a dialog, every alternative follows "Designing a
dialog" above. Ask the user to pick or mix, and invite comments on the
canvas. Read canvas comments before every revision.

## 4. Hi-fi mockup

- **Dialogs**: write the screen file itself, in the module's `src/main/resources/gui/`, with the chosen layout and the
  theme's styles. Generate its preview with `build_gui.py --previews` (`docs/core-gui-screens.md`) and show it with
  SendUserFile. The preview is the hi-fi mockup, drawn with the real art and font. Write a variant state into a copy of
  the file to preview other states (a second tab, an error, a full list). Revise the file until approved.
- **Inventories**: add a hi-fi artboard of the chosen layout in the theme: tokens, real pack textures uploaded as
  assets, the pixel font, hover and pressed states, an empty state and the largest-data state.

Loop with the user (Approve · Change) until approved. Keep rejected versions so the history stays visible.

## 5. Asset plan

List every texture and glyph the screen needs, marking which exist already (search the pack first) and which are new.
For new art:

- Only repeatable pipeline steps go in `Resourcepack/tools/`. A script that generates something once runs from the
  scratchpad and is not committed.
- Dialog art comes from styles, hover styles and sprites (`docs/core-gui-screens.md`, Pack generation). A new look is a
  nine-slice PNG in the pack's `assets/betterpvp/textures/gui/styles/`, drawn from the Design System tokens, never code
  and never a hand-placed glyph. One PNG serves every size. Icons go in `assets/betterpvp/textures/gui/icons/`, hover styles in `gui/hover/`.
- Other art: draw it with a reusable generator in `Resourcepack/tools/gui/` (Python, Pillow) driven by the theme
  tokens, so panels, buttons and frames stay consistent. Extend an existing generator before writing a new one.
- Render a composite preview PNG at game scale (the mockup rebuilt from the real textures) and show it with
  SendUserFile next to the hi-fi artboard. Ask: Approve · Change.

Before committing to a dialog technique not yet proven in game, run the spike in `references/dialogs.md`.

## 6. Implement

- Code follows the house rules and the menu patterns in `references/surfaces.md`. A dialog is its approved screen
  file plus the Java that opens it (`GuiScreens.open`) and binds its actions. Shared actions, components, element
  types and text styles go in `GuiRegistry`. A screen built in Java declares its art in `gui/assets/*.json`. Add a
  test that the screen loads and validates. Text goes through `Translations` in all 12 locales and follows
  `docs/ui-style.md`.
- Regenerate the pack art with `build_gui.py` after any screen file change, and before every deploy.
- Textures and their glyphs go in the resource pack, never Nexo (`references/surfaces.md`). Rebuild the pack with
  `pack_processor.py`.
- Compile, then `./gradlew shadowJar`.

## 7. Playtest

Ask: Deploy to ClansTest-1 · I will test it myself · Not yet. Never test in game yourself. Ask the user for a
screenshot at GUI scale 2 and 3 and compare it with the approved mockup. List every visible difference, fix the ones
the user picks, repeat.

## 8. Record

- New or changed components (a button style, a tab strip, a list row) go into the Design System with a preview, and
  into the implementation map in `docs/ui-theme.md` (texture path, glyph id, Java helper).
- A rule the user stated during review ("never more than two accent colours in one screen") goes into the theme
  README and `docs/ui-theme.md`.
- Commit `docs/ui-theme.md` and any skill changes in ai-tooling. Commit plugin and pack changes to their active
  branches. Open a PR only when the user asks.
