# Surfaces

Two surfaces, chained freely: an inventory button can open a dialog, and a dialog button can open an inventory.

## Choosing

**The user's choice of surface wins.** If they ask for a dialog, build a dialog, and if they ask for an inventory, build
an inventory. Raise a concern once, with the reason, and then follow their answer. When they have not chosen, recommend
from this table.

| Need | Surface |
| --- | --- |
| Full-screen composed screens: lobbies, banners, hubs, detail pages, side tabs | Dialog (`dialogs.md`) |
| Typing (search, amounts, names), sliders, toggles, option pickers | Dialog |
| Text-heavy screens: details, odds tables, confirmations, rules | Dialog |
| Moving, placing or comparing items, drag, item tooltips on many items | Inventory |
| Values that tick every second while open | Inventory (items update in place). A dialog is re-sent per change |

## Inventory menus

Framework: vendored InvUI in `core/inventory/` plus the BetterPvP layer in `core/menu/`.

- A menu is `extends AbstractGui implements Windowed`, `super(9, rows)`, then `setItem` or a `Structure` with
  `addIngredient`. `Windowed#show(player)` opens it, `getTitle()` supplies the title. Reuse `menu/button/` (back,
  paging, scroll, tabs, filters) and `menu/impl/` (ConfirmationMenu, GuiSelectOne, PagedSingleWindow).
- Menu text uses `Resources.Font.UI`, never an inline font key. Measure it with `UtilFont.componentWidth`, which reads
  the font's own advance table. After changing a pack font, regenerate its table with
  `core/tools/pack_font_advances.py`.
- Items are built with `ItemView` (`utilities/model/item/`). Click lines use `ClickActions` glyphs. Icons are
  `itemModel` keys. `Menu.INVISIBLE_BACKGROUND_ITEM` fills slots that the background art draws over.
- **Textured backgrounds** are glyphs in the title. **No Nexo.** The project is moving off it, so every new or
  restyled menu keeps its art in the resource pack:
  - Register each glyph as a `bitmap` provider in a pack font under `Resourcepack/pack/assets/betterpvp/font/`, with
    its own private-use codepoint. Reference it in Java as that char in that font (`Component.text("\uE...")` with
    the font key inline), never as a `<glyph:...>` or `<shift:...>` tag.
  - Offsets use the space font: `Component.translatable("space.N").font(Resources.Font.SPACE)` and the `FontCanvas`
    helper. Example: `GuiSelectOne`.
  - Menus that still use Nexo tags (`GuiSmelter`, `BuildMenu`, GuiWorkbench and others) are legacy. When a pass
    touches one, move its glyphs into the pack the same way. Their offsets are a useful reference: `-48` for full 9x6
    art, `-8` for art the size of the chest.
- `pack_processor.py`'s `.split` still prints Nexo glyph entries. Before the first split texture in the pack font,
  extend it to write the bitmap providers into the pack font instead (its `font=` key already names the target).
- **Art over 256 px in either axis must be split.** Vanilla font pages are 256x256 and an oversized
  glyph silently renders as nothing. Put a `.split` file next to the texture
  (`Resourcepack/README.md`, "Splitting oversized GUI textures"). The maths: title baseline at `topPos + 13`, slot 0
  inner corner at `(8, 18)`, slots are 18 px apart.
- Title text over a textured background needs its own shift back to the left edge, measured with `UtilFont`.
- Item tooltips can take a custom frame with the `tooltip_style` component.
- Sources: `.aseprite` files sit next to the PNGs in `textures/menu/gui/`. Keep a source for every new texture.

## Dialogs

Themed dialogs are screen files (`docs/core-gui-screens.md`), run by the dialog canvas library in
`core/menu/dialog/` (`docs/core-dialogs.md`). Older plain dialogs (`NameSearchButton`, `CurrencyOfferButton`,
`KitTrade`) use the Paper Dialog API directly.

Why dialogs work the way they do, from the client source, is in `dialogs.md`. Two rules shape every design:

- Backdrop art lives in the title (never clipped) and the canvas in the body (clipped to it). Clickable spots are
  canvas elements with `on_click`, or native buttons in the footer or the grid below the canvas.
- Hover shows as hover art over canvas buttons, tooltips, the hand cursor and the global native button highlight.

Validate everything again on click, because a dialog can sit open while the world changes (`KitTrade` does this).
