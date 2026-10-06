# UI theme

Status: Approved
Design System: https://claude.ai/artifact/UQNMB1NX9DdJz5DRxdqjdb
Directions canvas: https://claude.ai/artifact/3qMGQDvkzRP1s6VARyzoR2 (the Limestone kit and layouts are the last row)
Last verified: 2026-10-06

Limestone. Pale stone panels with a dark 1 GUI px outline and bevels, a header band one step darker than the panel,
white buttons and one green accent for the primary action. Stylised Minecraft that is light and calm, and fills the
screen. It replaces Gilded Vigil and the wood and parchment menu art over time.

## Rules

- Design in GUI px. Screen mockups are drawn at GUI scale 4 on a 1080p screen (480 x 270 GUI px, what Auto picks).
  Design System previews draw at GUI scale 3.
- Full-screen dialogs use a canvas of up to 460 x 189 GUI px, centred, with the native Close button in the footer. The
  art is `box` elements in the canvas, starting with a `panel_header` box and the title in its header band. In-game
  sizes are the mockup sizes plus 2, since the outline sits inside a box in game and outside it in the mockups.
- Tabs and buttons size to their label (`"width": "auto"`), per language.
- Every panel, button, tab, well, bar and tooltip has a 1 GUI px outline. Raised things get a bevel, wells get the
  reverse bevel, pressed flips it.
- The header band is one step darker than the panel, with dark text. Never a dark title bar.
- Green marks the one primary action and the selected tab. The lighter green outlines the selection and fills progress.
  One primary action per screen.
- Gold is only the coin. Violet is only magic content (spells, enchantments, attunement, runes). Neither is chrome.
- Sizes are free per screen. Every style is a nine-slice, so buttons, tabs, arrows and panels take any size.
- There is no default layout. Each screen picks from the components (list and card, card grid, showcase, table, action
  bar) or adds its own built from these rules.
- Every text colour passes 4.5:1 on its surface.
- No gradients, soft shadows or rounded corners.
- Menu art lives in the resource pack, never Nexo.

## Type

Menu text uses `Resources.Font.UI`, which is `betterpvp:rpg`, at one size. Hierarchy comes from colour and placement.
Every themed menu reads the font from there, so switching back to vanilla is a one-line change, and layouts must fit
both fonts.

- Letters come from the RPG bitmaps (Latin, accented Latin, Cyrillic).
- Numbers render in the vanilla font.
- Anything else falls back to `minecraft:default` (Arabic, Japanese, Korean, Chinese).

`UtilFont` measures text in the font it is drawn in, using `font/rpg_advances.bin` for `betterpvp:rpg`. Regenerate it
with `core/tools/pack_font_advances.py` whenever `rpg.json` or its textures change.

## Coins, tags and portraits

- An amount is the number in the vanilla font, then the coin texture `betterpvp:font/hud/coin.png` (14 x 13), centred
  on each other and never split. Never the word "coins".
- Rarity tags use the `ItemRarity` colours and names, all six. Small caps on a flat fill, 7 GUI px tall. Dark text on
  Common, Uncommon and Legendary, white on Rare, Epic and Mythical. They need new tag art in the pack. The existing
  `font/tags/*.png` glyphs stay for item lore.
- Portrait slots are sizes only (16, 14, 12 GUI px, or a picture frame). The fill is not fixed: placeholders now, shader
  heads or 3D rigs later.

## Palette

| Token | Hex | Use |
| --- | --- | --- |
| outline | `#1F2124` | Outline of everything |
| panel / panel-hi / panel-lo | `#D9D7D2` / `#F2F1EE` / `#ABA8A1` | Panel body and bevel |
| header / header-hi / header-lo | `#C6C3BC` / `#D6D3CD` / `#A6A39C` | Header band |
| well / well-shade / well-light | `#C4C1BA` / `#A6A39C` / `#E2E0DB` | Lists, tables, action bars, slots, progress track |
| raised / raised-hi / raised-lo | `#E8E6E1` / `#FFFFFF` / `#B9B6AF` | Rows, cards, tabs, frames |
| button / button-hover / button-pressed | `#F2F1EE` / `#FFFFFF` / `#D6D3CD` | Normal button |
| disabled | `#B9B6AF` | Disabled button face |
| placeholder | `#8E8B85` | Dashed empty slot |
| ink / ink-muted / ink-disabled / ink-on-accent | `#2A2C30` / `#4A4C51` / `#6E6B65` / `#FFFFFF` | Text |
| accent / accent-hi / accent-lo | `#3C8423` / `#5FA83A` / `#2A5E16` | Primary button, selected tab, selection outline, progress |
| accent-rim / accent-pressed / accent-tint | `#86CC5E` / `#2E6E1A` / `#D9EBC9` | Primary hover and pressed, selected ground |
| coin / coin-hi / coin-lo | `#F2B33D` / `#FFD36B` / `#C2611A` | Coin art only |
| danger / arcane | `#A61B1B` / `#5B2FC0` | Refusals, magic content |
| rarity common / uncommon / rare / epic / legendary / mythical | `#76D134` / `#4D9E15` / `#4A67FF` / `#8714B4` / `#EDA909` / `#E60B00` | Tags |

The full set with usage notes is in the Design System tokens.

## Sounds

Custom sounds in the pack, not made yet: open, close, click, confirm, error, page turn. Use vanilla stand-ins until then
and list them here.

## Components

Dialog styles are nine-slice PNGs in `Resourcepack/pack/assets/betterpvp/textures/gui/styles/` (hover styles in
`gui/hover/`), drawn from the tokens above. `build_gui.py` stretches each to the size a screen asks for, so one PNG
serves every size.

| Component | Texture | Font and codepoint | Code |
| --- | --- | --- | --- |
| Panel | style `panel`, `panel_header` (22 px header band) | generated per screen | `"box": "panel_header"` at y 5 |
| Header band | style `header` | generated per screen | `"box": "header"` |
| Well | style `well` | generated per screen | `"box": "well"` |
| Raised (row, card, frame) | style `raised` | generated per screen | `"box": "raised"` |
| Selected (row, card, slot) | style `selected` | generated per screen | `"box": "selected"` |
| Button, normal | style `normal`, `normal.pressed` | generated per screen | `"button": "normal"` |
| Button, primary | style `primary`, `primary.pressed` | generated per screen | `"button": "primary"`, `"label_style": "on_primary"` |
| Button, disabled | style `disabled` | generated per screen | `"button": "disabled"` |
| Hover | hover styles `light` (normal buttons, tabs) and `rim` (primary) | generated per spot | `"hover": "light"`, `"hover": "rim"` |
| Tab | styles `tab`, `tab_selected` with pressed art | generated per screen | `"selected_style": "tab_selected"`, `"selected_label_style": "on_primary"`, `"hover": "light"`, `"selected_hover": "rim"` |
| Progress bar | styles `track`, `fill` | generated per screen | two `box` elements |
| Button, native | `minecraft:textures/gui/sprites/widget/button*.png` from `theme_art.py`, a darker stone so vanilla white labels read | | `"exit"`, `"buttons"`, white label |
| Amount (coin) | `betterpvp:font/hud/coin.png` | `betterpvp:hud/center` `U+E001` | |
| Text styles | | | `GuiRegistry`: `body`, `muted`, `value`, `title`, `error`, `on_primary` |
| Tag | not built (needs a small tag font) | | |
| Placeholder | not built | | |
| Tooltip | not built | | |

`theme_art.py` holds no theme art. It writes the vanilla button and tooltip sprites and encodes hover glyphs.
Hand-placed `betterpvp:ui` glyphs `U+E000` to `U+E008` are retired.

## Screens

| Screen | Canvas | Status |
| --- | --- | --- |
| Skill menus (`/build`: class select, builds, skill editor) | https://claude.ai/artifact/2J6pBCSRXCMqhxTVbYvTVF | Wireframes, Gilded Vigil, needs Limestone |
