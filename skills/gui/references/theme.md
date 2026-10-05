# Theme setup

The theme is the project's visual language for every GUI. It lives in two places that never overlap:

- A **Design System** artifact (Claude Design): the look. Tokens, the pixel font, component previews, do and do not
  examples, the mood references. This is what mockups build on.
- **`docs/ui-theme.md`** (ai-tooling): the link to that system, the rules in short, and the implementation map from
  each component to its texture, glyph id and Java helper. This is what code and later sessions read first.

## Steps

1. **Seed from what exists.** Read the brand logo (steel and gold knight helm, `A:\Projects\BetterPvP\Logo`), the
   lore canon (Veloran, in Outline), the current menu art in `Resourcepack/pack/assets/betterpvp/textures/menu/gui/`,
   and the colour rules in `docs/ui-style.md`. Tell the user in three lines what the project already implies.
2. **Interview**, a few cards at a time, only what changes the look:
   - Feel: which words fit and which do not (for example heroic, gritty, cosy, arcane, clean, playful).
   - Fit with vanilla: blend into Minecraft's own UI, stylised Minecraft, or a full custom skin.
   - Density: big and calm, or compact and information-rich.
   - Reference games or servers the user likes, and ones they dislike.
3. **Directions.** Propose 3 named directions that genuinely differ (for example "Forged steel and gold", "Parchment
   and ink", "Night-sea glass"). For each, find 3 or 4 real references with WebSearch and open them in the browser
   pane, then draw the same sample on one canvas titled `GUI: Theme directions`: a small 3-row inventory, a dialog with
   two buttons and a list, the button states, and the rarity tags. Same content in each, so only the style differs.
   Ask: pick one, mix, or another round.
4. **Refine** the chosen direction on the same canvas until approved:
   - Palette: surfaces (3 depths), ink (primary, secondary, disabled), 1 or 2 accents, success, warning, danger, and
     the rarity colours. Check every text colour against its surface at 4.5:1.
   - Frame: border width, bevel or flat, corner shape, inner shadow, all in GUI px.
   - Type: the pixel font, title treatment (small caps font, shadow or none), sizes in GUI px.
   - Icons: style and size grid (8, 16).
   - Spacing grid in GUI px, and the panel padding.
   - Controls: button, tab, toggle, list row, progress bar, slot, each with its states.
   - Sounds for click, open, close, error.
5. **Save.** Create the Design System (`Artifact` quickstart with intent `other`, then the Design System type), title
   `BetterPvP UI`. Then write `docs/ui-theme.md` from the template below with Status Approved. Show both to the user.

Changing the theme later follows the same steps from 3, starting from the current system. Changing a single token or
component is a normal revision: update the system and the doc, and list the screens it touches.

## `docs/ui-theme.md` template

```markdown
# UI theme

Status: Approved
Design System: <url>
Last verified: <date>

<One paragraph naming the direction and what it should feel like.>

## Rules

- <Short rules the user stated or approved, for example "One accent per screen".>

## Palette

| Token | Hex | Use |
| --- | --- | --- |

## Components

| Component | Texture | Font and codepoint | Code |
| --- | --- | --- | --- |
| Panel | `textures/menu/gui/theme/panel.png` | `betterpvp:gui` `U+E100` | `ThemePanel` |

## Screens

| Screen | Canvas | Status |
| --- | --- | --- |
```
