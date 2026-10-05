# Custom full-screen GUIs built on server dialogs (1.21.6+): research notes

Date: 2026-10-05. Confidence: H = verified in decompiled client code or official changelog, M = strong inference from code / several sources, L = guess or single weak source.

## 0. Method and evidence quality

- Web search (standard + extended) across Spigot, Paper docs, Modrinth, BuiltByBit, GitHub, Reddit, minecraft.wiki, datapack.wiki and Chinese communities turned up **no public write-up, open-source pack or showcase video** of the "Dungeon Selection" / "gacha banner" style screens. Servers building these keep the technique private. Public dialog plugins (DialogWindow, KaMenu, FancyDialogs, DialogMaster, CustomDialogs, UniDialog, DialogMenu, ServerChangelogs) all use stock dialog widgets with no resource-pack art.
- So the layout and mechanics below come mainly from **decompiling the 1.21.11 client** (Mojang-mapped jar from the local fabric-loom cache, Vineflower). Files: `net/minecraft/client/gui/screens/dialog/*`, `components/{AbstractButton,AbstractStringWidget,FocusableTextWidget,MultiLineTextWidget,StringWidget,ScrollableLayout}`, `layouts/HeaderAndFooterLayout`, `multiplayer/ClientCommonPacketListenerImpl`. Decompiled sources: `scratchpad/dlgsrc`, `scratchpad/src2`, `scratchpad/src3`.

## 1. Who does it / public resources

| Resource | What it is | Relevance |
|---|---|---|
| https://minecraft.wiki/w/Dialog | Format reference, limits, history | Field limits (H) |
| https://minecraft.wiki/w/Java_Edition_1.21.6 | Dialog intro changelog | Quick Actions, pause additions, config phase (H) |
| https://docs.papermc.io/paper/dev/dialogs/ | Paper Dialog API (Paper 1.21.7+) | showDialog/closeDialog, PlayerCustomClickEvent, DialogAction.customClick, config-phase dialogs (H) |
| https://modrinth.com/project/UQlHFPHe "No Dialog Warning" | Client mod that removes the warning button, 1.21.6 to 26.3 | Shows the warning can't be removed server-side (H) |
| https://skinmc.net/index.php/project/hides-warning-botton | Resource pack that blanks `warning_button.png` | Pack-based hiding (H) |
| https://www.spigotmc.org/resources/dummydialoguesnpc.138959/ | NPC dialogue plugin that generates a font-glyph background pack, measures text width per glyph | Same font-glyph art technique, though not clearly on the dialog screen (M) |
| https://builtbybit.com/resources/dialogmaster-fully-custom-dialogs.111119/ | Paid "fully custom dialogs", 1.21.8+, "no resource pack" | Stock widgets only, judging by its description (L, page returned 403) |
| https://www.spigotmc.org/resources/...kamenu...133736/ | YAML dialog menus, Geyser forms | Stock widgets (H) |
| https://github.com/chunkzero/window | TypeScript→font+shader UI compiler (Minestom, 26.2) | Same art pipeline, but for container titles and HUD, not dialogs (H) |
| https://github.com/brikster/glyphs | Adventure/creative glyph library for absolutely positioned bitmap textures | A building block for dialog art (M) |
| https://github.com/AmberWat/NegativeSpaceFont | Negative-space font | Building block (H) |
| https://github.com/McTsts/Minecraft-Shaders-Wiki | Core shader reference | For shader tricks (H) |

## 2. Screen anatomy (1.21.11 client code, H)

`DialogScreen` uses a `HeaderAndFooterLayout`:
- **Header** (33 px tall): a horizontal `LinearLayout`, spacing 10, centred. It holds `StringWidget(title)` and then the 20x20 warning `ImageButton`. The title StringWidget has **no maxWidth**, so it is never clipped or ellipsised and is drawn **without a scissor**.
- **Body**: a vertical `LinearLayout` (spacing 10, centred horizontally) holding bodies, then inputs, then (multi_action) the action-button grid. It is wrapped in a `ScrollableLayout`. Its container is content width + 20 wide, its height is `min(contentHeight, screenH - header - footer)`, and **it is scissored to that rectangle**. Body top = `min(header + 30, screenH - footer - contentHeight)`, so with short content it sits at y = 63.
- **Footer** (33 px, or 5 px for multi_action without `exit_action`): notice/confirmation buttons in a horizontal row with spacing 8, or the multi_action `exit_action` button. Not scissored, anchored to the bottom.
- Draw order follows widget order: header title, then body, then footer, then the warning button last (M on exact layering under the 1.21.6+ GuiRenderState batching).
- Background: `renderBlurredBackground` (player's Menu Background Blur option) plus `textures/gui/inworld_menu_background.png`, which every in-world menu shares.
- Everything is in GUI-scaled pixels. Screen width and height vary with window size and GUI scale. Title art is anchored top-centre, body art body-top-centre, footer art bottom-centre.

## 3. Drawing panel art (how to position freely)

- **Font glyphs (bitmap providers with large `height` and custom `ascent`) plus negative/space advances** are the only way to draw arbitrary art on a dialog without mods (M, inferred; it is the universal technique for container-title GUIs and the code allows it here).
- **Title is the best canvas** (H, from code): unclipped, not scissored, drawn first (behind everything), centred at the top. One title Component can hold several glyphs, each moved by ascent (vertical, but a bitmap glyph's ascent must be <= height) and by space/negative-space advances (horizontal). This works for a full-screen backdrop such as the dungeon list frame, centre panel or party panel.
- **plain_message bodies** (width 1..1024, default 200) render as a centred `FocusableTextWidget` with 4 px padding and a fixed 9 px line height. Glyph art in a body draws outside its own box but is **clipped to the scroll container**. The container is as tall as the body's line count (lines*9 + 8), so tall art needs padding lines (`\n`) or it gets cut. Make the content fit the screen exactly or a scrollbar appears (H on clipping, M on the workaround).
- **Text shadow**: titles and body text draw with the default shadow. Set `shadow_color: 0` on art components (1.21.4+ text style) (M).
- **item body**: renders an ItemStack. width/height (1..256) set the box but per the wiki the item does not scale. Oversized item models (`oversized_in_gui`, 1.21.6+ item model definitions) might allow big 3D/2D art in a slot (L, untested). `show_tooltip: false` hides the hover tooltip.
- **`object` text component (1.21.9+)**: `{"type":"object","atlas":...,"sprite":...}` draws any atlas sprite inline, but always at 8x8. In 1.21.9 it gained `object: "player"` (player heads), and in 26.1 a `fallback` field. Useful for small icons (party member heads, item icons) without font entries (H, wiki 1.21.9 / 26.1 changelogs).
- **Core shaders**: no public dialog-specific shader found. Possible with `rendertype_text` / GUI pipelines (colour-keyed glyph vertices) but unsupported and brittle across versions (L).

## 4. Clickable buttons

- **Native action buttons** are vanilla `Button`s: fixed 20 px height, width 1..1024, sprites `widget/button`, `widget/button_highlighted`, `widget/button_disabled`. **These sprites are shared with every vanilla button**, so retexturing them reskins the whole game (H).
- Button label = any Component, so font glyphs work. The label is drawn through `renderScrollingStringOverContents` with a 2 px margin. If the label's advance width fits, it is drawn centred. If it is wider, it is scissored and scrolls. So **a label with near-zero net advance (glyph plus negative space) can draw art bigger than the button** (M, the exact unclipped behaviour of `acceptScrollingWithDefaultCenter` when it fits was not traced).
- **Placement**: multi_action buttons go in a grid (`columns`, default 2) with 2 px spacing. Each cell is centred and a short last row is centred. Buttons sit after bodies and inputs inside the scroll body. Free placement isn't possible, so "side buttons" are faked with column grids of mixed widths, or with clickable text instead (H on grid, M on approach).
- **Clickable text segments in bodies** (H): plain_message (and an item body's description) set `setComponentClickHandler(style -> dialogScreen.runAction(clickEvent))`. Any `click_event` on any text segment, including glyph art, runs as a dialog action (`custom`, `show_dialog`, `run_command`, `open_url`, `copy_to_clipboard`, ...) and then honours `after_action`. **This is the free-positioning click mechanism**: a glyph button anywhere inside a body (left column, right column) with its own click_event. Hit-testing uses glyph advance boxes on the 9 px text line (`ClickableStyleFinder`), not the drawn pixels (M). Because of that, a tall glyph is clickable only on its baseline row unless you stack several clickable lines.
- **Title text is not clickable** (StringWidget is not active and has no click handler) (H).
- Side effect: clicking a non-clickable part of a plain_message focuses it, and the focused widget draws a white outline around the body box (`renderOutline` when focused) (H). See MC-299873, "selection boxes of plain messages can get cut off", fixed 1.21.9.

## 5. Hover effects

- Native buttons: only the global `widget/button_highlighted` sprite. The label gets no hover style (`HoveredTextEffects.NONE`). Per-button `tooltip` (any Component, so glyphs work) shows on hover/focus (H).
- Body text: `hover_event` (show_text / show_item / show_entity) tooltips work on hover (`HoveredTextEffects.TOOLTIP_AND_CURSOR`). Since 1.21.9 the cursor changes to a hand over clickable segments (option "Allow Cursor Changes") (H).
- No hover-state *art swap* exists for text segments. A per-element visual hover would need the tooltip as the "highlight", or a shader trick (L). Hover over input labels gained hover_event support in 1.21.11 (MC-298405 fixed) (H).

## 6. Warning button and vanilla title

- The warning button can't be removed server-side (H). It is placed right of the title, centred together: x = (W - (titleAdvance + 30))/2 + titleAdvance + 10. If it would fall off-screen, `makeSureWarningButtonIsInBounds` moves it to (width-40, 5), the top-right (H). So **the title's net advance positions the warning button**: a huge advance pushes it to the top-right corner, a tuned one parks it over a frame decoration (M).
- Hiding: a resource pack overriding `textures/gui/sprites/dialog/warning_button{,_highlighted,_disabled}.png` with transparent pixels. **These sprites are used only by dialogs**, so this is safe. The button stays clickable (opens the "custom screen" confirm, which can disconnect) (H). Client mod alternative: "No Dialog Warning".
- "Vanilla title": the title is just a Component. Make it the art glyph string (or empty text plus glyphs). There is no other title chrome. Header and footer separators are not drawn on dialog screens (no `renderHeaderSeparator` call found in DialogScreen) (M).
- Background blur: depends on the player's blur setting. `inworld_menu_background.png` is global (every in-world menu).

## 7. Live updates

- Sending a new dialog (`show_dialog` packet / `Audience#showDialog`) while one is open **replaces the screen**: a new `DialogScreen` is built, and the previous non-dialog screen is kept as return target (H). There's no partial update or patch API (Paper docs, H).
- Rebuilding loses scroll position, focus and text/slider/checkbox state unless the server re-sends them as `initial` values. Mouse position is preserved (no re-grab), and the blur re-renders each frame, so swaps are instant with no animation (M). Expect a one-frame relayout and nothing else. Hover tooltips restart.
- `after_action: none` with a `custom` click: the client calls `setScreen(this)` after sending, which re-runs `init()` and rebuilds widgets from the dialog data. Inputs reset to their initial values (M).
- Use `wait_for_response` for a "loading" screen until the server answers with a new dialog.

## 8. Limits, bugs, version differences

- Widths: buttons, plain_message, inputs 1..1024. Item 1..256. Text input height 1..512. Defaults: button 150, message 200 (H, wiki).
- Fixed 20 px button height, 9 px text line, 10 px spacing between body elements, 2 px grid gaps (H).
- Body is scissored and scrolls. Title and footer are not (H).
- Everything is in GUI-scale pixels, so art must tolerate different screen sizes and GUI scales (H).
- Bug fixes after 1.21.6 (from wiki "fixes" tables): 1.21.9 fixed MC-297898 (dialog opening clears chat), MC-299548 (run_command dialog actions fail when chat hidden), MC-299873 (plain message selection boxes cut off) and MC-300457 (dialog unescapable with signed-chat run_command). 1.21.11 fixed MC-298405 (hover_event in input labels) and MC-299876 (boolean label shade). 26.1 fixed MC-303344 (item tooltips in dialogs shown when not hovered) (H).
- 1.21.9 added the `object` text component (atlas sprites 8x8, player heads), cursor shape changes, and the Server Code of Conduct screen (a separate vanilla screen) (H).
- 26.1: `object` gained `fallback`. Player-head objects are not allowed in MOTD (H).
- 26.2, 26.3, 26.4 snapshots 1-2: **no dialog format, layout or warning changes found** in the wiki version pages (H for "not listed"). 26.2 added Friends-UI sprites, which are unrelated.
- Core shader overrides are officially unsupported, and uniforms became uniform blocks in 1.21.6 (H).
- Paper Dialog API exists from Paper 1.21.7. Use `Audience#closeDialog()` (H).
