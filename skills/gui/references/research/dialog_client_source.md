# Minecraft Java client dialog rendering, from source (1.21.11, with 26.3 and 26.4-snapshot-2 diffs)

## Method

- 1.21.11 client jar remapped with the official Mojang ProGuard mappings (`client.txt` from piston-data, sha1 031a68be...) using SpecialSource 1.11.6 (Maven Central), then decompiled with Vineflower 1.12.0. Decompiled sources are in this scratchpad: `src/` (dialog, GUI, Minecraft, packet listeners), `src2/` (font, render state), `src3/` (StringSplitter), `src4/` (GuiRenderer, GuiRenderState, MouseHandler).
- 26.3 and 26.4-snapshot-2 client jars (piston-data URLs from the launcher jsons) are unobfuscated, so they were decompiled directly into `src263/` and `src264/`.
- Tags: **[src]** = read from decompiled source. **[inf]** = inferred, not read line by line.
- All sizes are GUI-scaled pixels. `Screen.width/height` come from `Window.getGuiScaledWidth/Height()` (`Minecraft.setScreen` calls `screen.init(guiScaledW, guiScaledH)`) [src]. A 1080p window at GUI scale 4 is 480x270, so a width of 1024 is wider than the screen at most scales.

## Class map (1.21.11)

| Purpose | Class |
|---|---|
| Base screen | `net.minecraft.client.gui.screens.dialog.DialogScreen<T>` (inner `WarningScreen extends ConfirmScreen`) |
| notice / confirmation | `SimpleDialogScreen` (registered for `NoticeDialog` and `ConfirmationDialog` in `DialogScreens.bootstrap`) |
| multi_action | `MultiButtonDialogScreen extends ButtonListDialogScreen` |
| dialog_list | `DialogListDialogScreen extends ButtonListDialogScreen` |
| server_links | `ServerLinksDialogScreen extends ButtonListDialogScreen` |
| Buttons and inputs | `DialogControlSet`, `input.InputControlHandlers` |
| Bodies | `body.DialogBodyHandlers` (`PlainMessageHandler`, `ItemHandler`) |
| wait_for_response | `WaitingForResponseScreen` |
| Packet handling | `ClientCommonPacketListenerImpl.showDialog` / `clearDialog` |
| Data and codecs | `net.minecraft.server.dialog.*` (`CommonDialogData`, `CommonButtonData`, `PlainMessage`, `ItemBody`, inputs) |

## 1. Layout

`DialogScreen.init()` [src]:
- `layout = new HeaderAndFooterLayout(this)`. The header and footer are each 33 px high by default.
- Header: `createTitleWithWarningButton()`, a horizontal `LinearLayout` with spacing 10 holding `StringWidget(title)` and the 20x20 warning `ImageButton`. Both are centred horizontally and vertically middle. The header `FrameLayout` centres this row (align 0.5/0.5) inside screen width x 33. The row is 20 high, so the button sits at y=6 and the title text at about y=11 [src math].
- Body: a vertical `LinearLayout` with **spacing 10** and every child centred horizontally. It holds, in order: each `body` element, then each `input` control, then (for button-list dialogs) the packed button grid (`populateBodyElements`).
- The body is wrapped in `ScrollableLayout(minecraft, body, layout.getContentHeight())` and added to the contents frame.
- Footer: `SimpleDialogScreen.updateHeaderAndFooter` adds a horizontal `LinearLayout` with **spacing 8** holding the main action buttons (notice: one; confirmation: yes then no). `ButtonListDialogScreen` puts `exit_action` alone in the footer, or with no `exit_action` sets **footer height to 5**.
- `repositionElements()` sets `bodyScroll.setMaxHeight(contentHeight)`, then `layout.arrangeElements()`, then `makeSureWarningButtonIsInBounds()`. Window resize calls `Screen.resize`, which calls `repositionElements` (no rebuild). So a resize keeps scroll, focus and input values [src].

`HeaderAndFooterLayout.arrangeElements` [src]:
- `contentHeight = screen.height - headerHeight - footerHeight`.
- Header frame: minWidth = screen.width, minHeight = 33, at (0,0). Footer frame: minWidth = screen.width, at y = height - footerHeight, child centred.
- Contents frame: minWidth = screen.width, at `y = min(headerHeight + 30, height - footerHeight - contentsHeight)`. **The body is top-anchored at y=63 when short, not vertically centred.** When tall, it is pushed up so it ends at the footer.
- **Horizontal centring.** `FrameLayout` width = max(minWidth, child width), and the child x is `lerp(0.5, 0, frameW - childW)`. If the child is wider than the screen, frameW = childW and the child sits at **x=0, overflowing to the right**. The same applies to the footer row.

`ScrollableLayout` [src]:
- Container width = content width + 20. The content is placed at container.x + 10, so there are 10 px of slack each side. The scrollbar sits at the container's right edge minus 6.
- Container height = min(content height, max height). Scroll rate is 10 px per wheel notch. The scrollbar shows only when content is taller than the container. The scroller height is clamped to 32..height-8.
- `Container.renderWidget` calls `enableScissor(x, y, x+w, y+h)` and then renders all body widgets. **Everything in the body is clipped to the container rectangle.** That rectangle is exactly the content's height when no scrolling is needed, and content width + 20.
- Keyboard focus auto-scrolls the focused child into view, with a 14 px margin.

Element sizes [src]:
- plain_message: see section 5. Width = `width` field (default 200, range 1..1024 via `Dialog.WIDTH_CODEC`).
- Inputs: text `EditBox(width, 20)`. Multiline: `MultiLineEditBox` with height = `height`, or `min(9*maxLines+8, 512)`, defaulting to 4 lines. With `label_visible` the input is wrapped in `CommonLayouts.labeledElement`: a vertical layout with spacing 4, a `StringWidget` label above the input. Slider: `SliderImpl(width, 20)`. Single option: `CycleButton(width, 20)`. Boolean: `Checkbox`, a 17x17 box (`getBoxSize = 9+8`), then 4 px, then the label (max 2 rows).
- Buttons: width from `CommonButtonData.width` (default 150, 1..1024), height always 20 (the `Button.Builder` default; only `width()` is set).
- No max dialog width or height, and no GUI-scale-aware shrinking. Overflow is horizontal (to the right, with no horizontal scroll) or vertical (with scroll) [src].

## 2. Warning button

- What: `DialogScreen.createWarningButton()` builds an `ImageButton` (20x20) with `WidgetSprites(dialog/warning_button, dialog/warning_button_disabled, dialog/warning_button_highlighted)` (files under `assets/minecraft/textures/gui/sprites/dialog/*.png`, 20x20, no mcmeta). It has tooltip `menu.custom_screen_info.tooltip` ("This is a custom screen. Click here to learn more.") and narration `menu.custom_screen_info.button_narration` [src].
- Click: opens `DialogScreen.WarningScreen`, a `ConfirmScreen` with title `menu.custom_screen_info.title`, body `menu.custom_screen_info.contents`, and buttons "Disconnect" and Back. Disconnect calls `connectionAccess.disconnect(Component.translatable("menu.custom_screen_info.disconnect"))` [src].
- When shown: always, on every DialogScreen. No dialog field, game rule or client option controls it. There is no condition in `init()` [src].
- Position: to the right of the title, 10 px gap. `makeSureWarningButtonIsInBounds()`: if x<0, y<0, x>width-20 or y>height-20, it moves to `(max(0, width-40), min(5, height))`, the top-right corner. An extremely wide (or negative-width) title therefore just moves it there [src].
- Cannot be covered by dialog content. It is added as the **last** renderable (`addRenderableWidget(warningButton)` after everything else). `GuiRenderState.findAppropriateNode` places any later element that intersects earlier ones in a higher node, so the button draws above any body or title glyphs it overlaps [src]. Only deferred tooltips (next stratum) draw above it.
- Tab order: `setTabOrderGroup(-10)`, so it comes first. `Screen.setInitialFocus` focuses the first element only if the last input was keyboard. So keyboard users start focused on the warning button [src for code / inf for the sorting detail].
- **Resource pack options:**
  - Replace the 3 sprites with fully transparent 20x20 PNGs. The button becomes invisible but stays clickable (20x20 hitbox), shows a hand cursor, and still opens the WarningScreen [src: `ImageButton` only blits the sprite].
  - Set `"menu.custom_screen_info.tooltip": ""` in a lang file. `Font.split("")` → `StringSplitter.splitLines` yields no lines for empty text, and `setTooltipForNextFrameInternal` skips empty lists. So no tooltip box draws at all [src for skip-if-empty / inf that `getRemainder()` returns null for empty input].
  - A server resource pack can ship both. Nothing in the client prevents overriding these assets [inf].
- 26.3 / 26.4-snapshot-2: identical code and sprites [src diff].

## 3. Sprites and textures drawn

| Element | Resource (namespace `minecraft`) | Notes |
|---|---|---|
| Background | `Screen.renderBackground`: DialogScreen does not override `isInGameUi()` (false) → `renderBlurredBackground` + `renderMenuBackground` [src] | |
| Blur | Post chain `minecraft:blur` (`assets/minecraft/post_effect/blur.json`, shader `shaders/post/box_blur.fsh`). Applied only if `options.menuBackgroundBlurriness >= 1` (Accessibility > Menu Background Blur, 0..10, default 5) [src] | The client option (player-side) turns it off. A resource pack can override `post_effect/blur.json` or the shader [inf, packs can override post effects] |
| Dim tile | In world: `textures/gui/inworld_menu_background.png` (16x16, tiled 32x32). Without a level: `textures/gui/menu_background.png`, with the panorama behind [src] | Make it transparent in a pack to remove the dark overlay [inf]. This is global to all menus |
| Header/footer separators | Not drawn by DialogScreen (no render override) [src] | |
| Buttons (actions, list buttons, exit) | `widget/button`, `widget/button_highlighted` (hovered OR focused), `widget/button_disabled`. Nine-slice 200x20, border 3 [src + mcmeta] | Same sprites as every vanilla button |
| Warning button | `dialog/warning_button`, `_highlighted`, `_disabled` | |
| Text input | `widget/text_field`, `widget/text_field_highlighted` (focused). Nine-slice 200x20, border 1. Multiline (`AbstractTextAreaWidget`) uses the same pair [src] | |
| Checkbox | `widget/checkbox`, `checkbox_highlighted`, `checkbox_selected`, `checkbox_selected_highlighted` (highlight = focused) [src] | |
| Slider | `widget/slider`, `widget/slider_highlighted`, `widget/slider_handle`, `widget/slider_handle_highlighted` [src] | |
| Cycle button (single_option) | Default button sprites (no custom sprite supplier in dialogs) [src] | |
| Scrollbar | `widget/scroller` (6x32 nine-slice), `widget/scroller_background` [src] | |
| Tooltips | `tooltip/background`, `tooltip/frame`. Item tooltips use the item's `tooltip_style` component: `tooltip/<style>_background` / `_frame` [src] | Per-item custom tooltip art in the item body |
| Focus outline | `GuiGraphics.renderOutline` solid white 1px, no sprite (plain_message and item body when focused) [src] | Cannot be restyled by a pack |

Changing any of these sprites restyles every vanilla menu, not only dialogs. There is no dialog-specific namespace except `dialog/warning_button*` [src].

## 4. Buttons

- Built in `DialogControlSet.createDialogButton`: `Button.builder(label, onPress).width(width)`, plus `.tooltip(Tooltip.create(tooltip))` if present. The height is fixed at 20 [src].
- Placement: footer row (spacing 8, centred, or at x=0 if too wide), or a body grid for multi_action, dialog_list and server_links (section 7).
- Rendering: `Button.Plain.renderContents` calls `renderDefaultSprite` (nine-slice of the button sprites at the widget size, with `alpha`), then the label via `renderScrollingStringOverContents(label, margin 2)` using `textRendererForWidget(this, HoveredTextEffects.NONE)` [src].
  - Label logic, `ActiveTextCollector.defaultScrollingHelper`: textY = `(top + bottom - 9)/2 + 1`, i.e. y+6 for a 20 px button. If `font.width(label) > width - 4`, it renders LEFT-aligned with a **scissor of [x+2, x+w-2] x [y, y+20]** and scrolls back and forth (sinusoidal, period max(overflow*0.5, 3) s). Otherwise it renders **CENTER-aligned at the clamped centre with no extra scissor** [src].
  - So a label whose `font.width` (sum of advances, negative advances included) fits in width-4 is never clipped to the button. Glyphs with large ascent, height or negative-space offsets draw outside the button rectangle [src]. In the footer there is no scissor at all. In body grids the scroll container's scissor applies.
  - Custom fonts: the label is a full `Component`, so a `font` style (custom glyph font) is honoured. You can make a "picture button" by making the sprite transparent via pack (global) or drawing glyph art over it [src for component rendering / inf for pack approach].
  - `HoveredTextEffects.NONE`: **hover and click events inside a button label are ignored** (no tooltip, no cursor change) [src].
- Hover state: `isHovered = containsPointInScissor && in rect`. The highlighted sprite is used when `isHoveredOrFocused()`. Clicking gives the button focus (`ContainerEventHandler.mouseClicked` → `setFocused`). With `after_action: none` the screen instance stays, so **the clicked button stays highlighted** until focus moves [src, persistence inf]. The cursor becomes a pointing hand on hover. The click plays `ui.button.click` [src].
- Tooltip: `Tooltip.create(component)`, wrapped at **170 px**, shown when hovered (or keyboard-focused), with no delay. `MenuTooltipPositioner` places it relative to the widget [src].
- Width > screen: allowed up to 1024. The row frame becomes wider than the screen and starts at x=0 [src].
- Width 1: the nine-slice clamps borders to `min(border, w/2)` = 0, so a 1 px stretched slice of the centre draws. Any label with `font.width > -3` goes to scroll mode with an empty scissor and is invisible. A label with net width <= -3 (negative space) renders centred and unclipped [src]. The hitbox is 1x20.
- Hitbox is always the widget rectangle (width x 20). Glyphs drawn outside it are not clickable [src].

## 5. Text bodies (plain_message)

- `PlainMessageHandler`: `FocusableTextWidget.builder(contents, font).maxWidth(width).alwaysShowBorder(false).backgroundFill(NEVER)`, then `setCentered(true)` and `setComponentClickHandler(style -> runActionOnParent(screen, style))` [src].
- Geometry: widget width = `width`. Text wraps at `width - 8` (padding 4 each side). Height = `9 * lineCount + 8`. Each line is centred at x + width/2 with a **fixed 9 px line pitch**, whatever the font's glyph ascent or height [src]. **No max line count** (`maxRows` unset) and no ellipsis. Overflow scrolls the body.
- Clipping: glyphs are not clipped to the widget, only to the body scroll container's scissor. That rectangle is exactly the body's content height (when not scrolling) and content width + 20. **Large-ascent glyph art on the first line of the first body element is cut off at the top of the body, and the same happens below the last element.** Pad with extra lines or elements, or put the art lower, to make room [src].
- Click events: `AbstractStringWidget.onClick` runs `ClickableStyleFinder` at the mouse point and calls the handler with the first style that has a click event. `runActionOnParent` → `DialogScreen.runAction(Optional.of(click))`, which uses the dialog's `after_action` [src]. Supported: run_command (client-side check; parse, permission or signature issues open a confirm screen: `ClientPacketListener.sendUnattendedCommand`), show_dialog, custom (sends `ServerboundCustomClickActionPacket`), open_url (respects chat-link options, may show ConfirmLinkScreen, dialog stays if no confirm), copy_to_clipboard. `suggest_command` does nothing (`insertText` not overridden). Others log an error [src].
- Hover events: when the widget is hovered, it renders with `TOOLTIP_AND_CURSOR` (click handler set). Each glyph whose rectangle contains the mouse records its style. `show_text` tooltip is wrapped at `max(guiWidth/2, 200)`. `show_item` shows the full item tooltip (with `tooltip_style`). `show_entity` shows only with advanced tooltips on [src].
- Per-character hit test (`ActiveTextCollector.findElementUnderCursor`): first the point must be inside the text's bounds (union of rendered glyph quads, intersected with the scissor). Then each glyph's own rendered rectangle counts (`left/top/right/bottom` of the glyph quad, so ascent and height are honoured). Empty glyphs (space-type providers, including negative space) contribute a 9 px tall, `advance` wide area at the line, but are not part of the bounds [src]. **Both hover and click also require the mouse inside the widget's rectangle** (`isHovered` / `isMouseOver`), so art drawn outside the box is not interactive [src].
- Gotchas:
  - `FocusableTextWidget.active = true`, so every plain_message is focusable by Tab and by mouse click. Clicking anywhere in the box (even on non-clickable text) focuses it and **draws a solid white 1 px outline** around the full box. A vanilla pack cannot disable that outline [src].
  - It is silent: `playDownSound` is overridden empty [src].
- The title (`StringWidget`) has no wrap and no clipping (width = `font.width(title)`, height 9). It is inactive, but hover events in the title still show tooltips (`TOOLTIP_ONLY`). Click events in the title do nothing [src].

## 6. Item body

- `ItemHandler`: `ItemDisplayWidget(mc, 0, 0, width, height, msg, item, show_decorations, show_tooltip)`. `width` and `height` are 1..256 (default 16) [src].
- **The item is not scaled.** `renderItem` draws a normal 16x16 item at the widget's top-left (offset 0,0). `width`/`height` only size the layout box, hover area and focus outline [src].
  - Item models flagged `oversized_in_gui` (`ClientItem.Properties`) take `GuiRenderer`'s `OversizedItemRenderer` picture-in-picture path and can draw beyond 16x16 [src]. They are still subject to the body scissor [inf].
  - A custom `item_model` with large GUI display transforms + `oversized_in_gui` is the way to draw big images [inf].
- Decorations (`show_decorations`): count, durability bar, cooldown overlay via `renderItemDecorations` [src].
- Tooltip (`show_tooltip`): `setTooltipForNextFrame(font, stack, mx, my)` when hovered **or focused**. It shows full item lines, tooltip image and the item's `tooltip_style` sprites [src].
- The widget is active and focusable. Clicking it plays the button click sound (`AbstractWidget.mouseClicked` → `playDownSound`), focuses it and draws a **white outline** [src].
- With `description`: a horizontal `LinearLayout` (spacing 2, vertically middle) of the item widget and a `FocusableTextWidget` (`maxWidth = description.width`, not centred, left-aligned, clickable like plain_message) [src].
- 26.3+: `ItemBody.item` is an `ItemStackTemplate`, turned into a stack with `.create()`. Rendering is unchanged [src].

## 7. dialog_list / multi_action / server_links grids

`DialogScreen.packControlsIntoColumns(buttons, columns)` [src]:
- `GridLayout` with column spacing 2 and row spacing 2. Cells are centred horizontally (vertical alignment is the default top).
- Full rows: element i goes to `(row = i / columns, col = i % columns)`. Column width = max width in that column. Row height = max height (20).
- Leftover elements (n % columns) go into one horizontal `LinearLayout` (spacing 2, centred) spanning all columns in the last row. So a partial last row is centred as a group.
- `columns` is any positive int (default 2). Very large values give one wide row that overflows right.
- `dialog_list`: each button = `CommonButtonData(target.external_title or title, button_width)` with action `show_dialog`. No tooltip [src].
- `multi_action`: each `ActionButton` keeps its own width and tooltip. Columns are uneven if widths differ [src].
- The grid lives inside the scrolling body (after bodies and inputs, with spacing 10) and is clipped by its scissor [src].
- The footer holds `exit_action` (centred), else the footer is 5 px high [src].

## 8. Free positioning, overlap and re-sending

- No negative widths: every width is `intRange(1, 1024)` or `1..256`, and all layout is flow-based (linear, grid, frame). There is no x/y field [src].
- Ways to fake free placement [src mechanics, inf for technique]:
  - Glyph art with negative-space advances and large or offset ascents in titles, labels and plain_messages. It renders outside widget boxes: unclipped in the header and footer, clipped to the scroll rectangle in the body.
  - A button label whose net width fits draws unclipped.
  - Overlaps are drawn in submission order (later on top, via `GuiRenderState` overlap nodes). Within the body, order is: bodies, inputs, grid. Screen-level order comes from `layout.visitWidgets`: header (title) → contents (scroll container) → footer, then the warning button last [src].
  - Hit testing is always the widget rectangle. Overlapping widgets resolve clicks via `getChildAt` (first child in list order whose `isMouseOver` is true) [src for getChildAt, inf for order].
- Empty labels: an empty button label renders nothing. An empty title gives a zero-width title with the warning button centred [src math].
- **Re-sending a dialog while one is open** (`ClientCommonPacketListenerImpl.showDialog`) [src]:
  - If the current screen is a DialogScreen (or a WaitingForResponseScreen), the new dialog's previous screen = the old one's `previousScreen()`. The chain is flattened, not stacked.
  - Then `minecraft.setScreen(new DialogScreen)`: always a **new screen instance**. Old `removed()`, then new `init()` → fresh widgets, **scroll at 0, inputs reset to `initial`, focus cleared** (or the warning button if the last input was keyboard), tooltip timers reset.
  - The mouse is not recentred (`MouseHandler.releaseMouse` only moves the cursor if it was grabbed). There is no transition animation.
  - If the WarningScreen is open, the new dialog silently replaces its return screen.
- `ClientboundClearDialogPacket` → `setScreen(previousScreen)` (or fixes the WarningScreen's return target) [src].

## 9. Keyboard, escape, pause, after_action

- Escape: `Screen.keyPressed`: if `can_close_with_escape` (default true), it calls `onClose()` → `runAction(onCancel action, DialogAction.CLOSE)`. **Escape always goes back to the previous screen, regardless of `after_action`**, after firing the cancel action's click event [src].
  - Cancel action: notice → its `action`. Confirmation → the `no` button's action. List dialogs → `exit_action`'s action [src].
  - With `can_close_with_escape: false`, Escape falls through to the focused widget [src].
- Buttons and click events → `runAction(click, after_action)` [src]:
  - `close` → previous screen.
  - `none` → the same screen instance. `setScreen(this)` re-inits it as reposition only, keeping state [src/inf].
  - `wait_for_response` → `WaitingForResponseScreen(previousScreen)`: title `gui.waitingForResponse.title`. The back button is invisible for 1 s, then counts down "Back (4s)".."(1s)", and is active (Escape works) at 5 s. It is not a pause screen. It is replaced by the next dialog [src].
- `pause` (default true): `isPauseScreen()`. The game only pauses in singleplayer and unpublished worlds (`Minecraft`: `hasSingleplayerServer() && screen.isPauseScreen() && !published`), so there is **no effect on a multiplayer server** [src]. The codec rejects `pause: true` with `after_action: none` [src].
- Tab / Shift+Tab / arrows navigate focus (warning button first, group -10). Enter/Space activates the focused button. Shift+click on a cycle button goes backwards [src].

## Later versions: 26.3 and 26.4-snapshot-2

Diffed decompiled `client/gui/screens/dialog/**` and `server/dialog/**` against 1.21.11 (same file set in all three) [src]:

- **No new dialog types, body types, input types, button options, positioning fields, or warning changes** in 26.3 or 26.4-snapshot-2. The codecs are identical (`CommonDialogData`, `CommonButtonData`, `PlainMessage`, `ItemBody` fields, width ranges 1..1024 / 1..256).
- 26.3 vs 1.21.11:
  - `ItemBody.item` became `ItemStackTemplate` (`.create()` on render).
  - `DialogScreen.repositionElements` now calls `bodyScroll.arrangeElements()` before `setMaxHeight`.
  - `ScrollableLayout` gained `ReserveStrategy`, min height and scrollbar settings. The dialog uses the default `BOTH`, so it still reserves 10 px each side, same geometry.
  - The GUI pipeline was renamed: `render*` → `extract*`, `GuiGraphics` → `GuiGraphicsExtractor`.
  - `Tooltip` gained a `create(message, Optional<TooltipComponent>, style)` overload, but dialogs still call `Tooltip.create(component)`.
  - `minecraft.setScreen` became `minecraft.gui.setScreen`.
  - Button label (`HoveredTextEffects.NONE`, scrolling helper, 9 px line math) and `FocusableTextWidget` behaviour are unchanged (narration additions only). Sprite IDs are unchanged.
- 26.4-snapshot-2 vs 26.3:
  - `WaitingForResponseScreen` uses `setVisible()`.
  - `DialogAction.STREAM_CODEC` uses `ByteBufCodecs.enumCodec`.
  - No other dialog differences. Widget files checked (AbstractButton, Button, FocusableTextWidget, MultiLineTextWidget, AbstractStringWidget, ScrollableLayout, ItemDisplayWidget, StringWidget, ActiveTextCollector, HeaderAndFooterLayout, GridLayout, Tooltip, Screen) are identical. Only AbstractWidget differs.
