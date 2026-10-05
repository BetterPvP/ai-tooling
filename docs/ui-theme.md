# UI theme

Status: Approved
Design System: https://claude.ai/artifact/UQNMB1NX9DdJz5DRxdqjdb
Directions canvas: https://claude.ai/artifact/3qMGQDvkzRP1s6VARyzoR2
Last verified: 2026-10-05

Gilded Vigil. Dark steel panels with a 1 GUI px black outline and bevels, bevelled steel buttons, and one gold accent.
Stylised Minecraft that stays clean and calm, with violet kept for magic content. It replaces the wood and parchment menu
art over time.

## Rules

- Design in GUI px. Mockups draw at GUI scale 3 and are checked at GUI scale 2.
- Every panel, button and tooltip has a 1 GUI px outline. Raised things get a bevel, wells get the reverse bevel.
- Gold marks the one primary action, the selection, header trim and progress. One primary action per screen.
- Violet is for magic content only (spells, enchantments, attunement, runes), never for chrome.
- The Legendary tag shares the gold family with the accent. Accepted.
- No gradients, soft shadows or rounded corners.
- Big and calm by default. Dense only where the content is a table or list the player compares.
- Menu art lives in the resource pack, never Nexo.

## Type

Menu text uses `Resources.Font.UI`, which is `betterpvp:rpg`. Every themed menu reads it from there, so switching back to
vanilla is a one-line change, and layouts must fit both fonts.

- Letters come from the RPG bitmaps (Latin, accented Latin, Cyrillic).
- Digits render in the vanilla font, so numbers stay readable.
- Anything else falls back to `minecraft:default` (Arabic, Japanese, Korean, Chinese).

`UtilFont` measures text in the font it is drawn in, using `font/rpg_advances.bin` for `betterpvp:rpg`. Regenerate it
with `core/tools/pack_font_advances.py` whenever `rpg.json` or its textures change.

## Palette

| Token | Hex | Use |
| --- | --- | --- |
| outline | `#0C0B10` | Outline of every panel, button, tooltip |
| surface-0 | `#12141C` | Wells: slots, tracks, inputs |
| surface-1 | `#1A1E2B` | Header bands |
| surface-2 | `#232838` | Panel body |
| surface-3 | `#2C3244` | Raised rows, hover ground |
| bevel-hi / bevel-lo | `#3A4258` / `#161A24` | Panel bevel |
| ink / ink-muted / ink-disabled | `#EEF0F5` / `#A3AABD` / `#6B7183` | Text |
| steel / steel-hi / steel-lo | `#5C6375` / `#838B9E` / `#343946` | Normal button, light text on it |
| steel-hover | `#6E768A` | Hovered normal button |
| tag-ink | `#14161D` | Text on tags |
| accent / accent-hi / accent-lo | `#F2B33D` / `#FFE6A0` / `#C2611A` | Gold |
| accent-title | `#FFD36B` | Titles and item names |
| arcane / arcane-hi / arcane-lo | `#A77BFF` / `#D9C6FF` / `#6A3FD0` | Magic content |
| success / danger | `#7BD88F` / `#E5484D` | States |
| rarity common / uncommon / rare / legendary | `#C9CED9` / `#7BD88F` / `#6FA8FF` / `#FFC23D` | Tags |

The full set with usage notes is in the Design System tokens.

## Sounds

Custom sounds in the pack, not made yet: open, close, click, confirm, error, page turn. Use vanilla stand-ins until then
and list them here.

## Components

| Component | Texture | Font and codepoint | Code |
| --- | --- | --- | --- |
| Panel | `textures/font/ui/dialog_test_panel_*.png` (test only) | `betterpvp:ui` `U+E000`, `U+E001` | `DialogCanvas` backdrop |
| Button, gold | `textures/font/ui/button_gold.png`, `button_gold_pressed.png` | `betterpvp:ui` `U+E004`, `U+E007` | `CanvasElement.pressed` |
| Button, hover rim | `textures/font/ui/dialog_test_confirm_hover.png` (per position) | `betterpvp:ui` `U+E008` | `CanvasElement.hover` |
| Button, steel (canvas) | `textures/font/ui/button_steel.png` | `betterpvp:ui` `U+E005` | `DialogCanvas.art` |
| Button, native | `minecraft:textures/gui/sprites/widget/button*.png` | | `DialogButton` |
| Slot | not built | | |
| Tooltip | not built | | |
| Tag | not built | | |
| Tab | `textures/font/ui/tab.png`, `tab_selected.png` (not in the Design System yet) | `betterpvp:ui` `U+E002`, `U+E003` | `DialogCanvas.art` |
| List row | not built | | |
| Progress bar | not built | | |

All art is drawn by `Resourcepack/tools/gui/theme_art.py`. Codepoints are fixed. `U+E006` is retired.

## Screens

| Screen | Canvas | Status |
| --- | --- | --- |
| Skill menus (`/build`: class select, builds, skill editor) | https://claude.ai/artifact/2J6pBCSRXCMqhxTVbYvTVF | Wireframes |
