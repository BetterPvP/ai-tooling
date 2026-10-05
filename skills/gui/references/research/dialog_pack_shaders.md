# Server resource pack vs. dialog screen rendering (1.21.6 to 26.x, no client mods)

Confidence tags: **[H]** verified in the 1.21.11 client jar (Mojang-mapped, `~/.gradle/caches/fabric-loom/.../minecraft-clientonly-1.21.11...jar`, disassembled with `javap`) or in our own pack. **[M]** documented by the wiki or community but not checked in code. **[L]** inference or community folklore.

The server runs Paper **1.21.11** (`settings.gradle.kts`). Our pack declares `pack_format 81`. That number belongs to **26.1 snapshot 7 to 10**, not to 1.21.11 (format 75.0). A 1.21.11 client shows the pack as "made for a newer version" but still loads it. **[M]** ([Pack format](https://minecraft.wiki/w/Pack_format))

## 0. What our pack does today

- Only `assets/minecraft/shaders/core/rendertype_text.vsh` is overridden (`#version 150`; no `.fsh`). **[H]**
  - It gates on orthographic projection (`ProjMat[3][3] > 0.5`) and on `guiY < 120` (the top strip).
  - It reads a low-3-bit colour signature: LEFT `(5,2,5)` = `0xFDFAFD` and RIGHT `(5,2,6)` = `0xFDFAFE`.
  - It shifts marked glyphs by one clip half-width, plus an inset of `2px * ProjMat[0][0]`.
  - It also does a rainbow hue for exact colour `0xE6FFFE`, using `GameTime`.
- Sprite overrides already present: `widget/button`, `button_disabled` and `button_highlighted` (200x20, `nine_slice` border 7, vanilla uses border 3). There are also many container, HUD and advancement sprites. **[H]**
- The README's ".split" tool exists because glyph images over 256x256 vanish. See section 5. The README's explanation of the cause is only half right.

## 1. Which shader programs draw GUI elements (1.21.6+)

The 1.21.6 rework replaced immediate-mode GUI drawing with a render-state tree (`GuiRenderState` → `GuiRenderer`). It uses `RenderPipeline`s, strata and `blurBeforeThisStratum()`. [NeoForge 1.21.6 primer](https://docs.neoforged.net/primer/docs/1.21.6). **[H]**

Pipeline to shader mapping, read from `RenderPipelines.class` (1.21.11). **[H]**

| Pipeline | Shader program | Used for |
|---|---|---|
| `pipeline/gui`, `gui_invert`, `gui_text_highlight` | `core/gui` (POSITION_COLOR, no sampler) | `fill`/`fillGradient`: the in-inventory dark gradient, text selection highlight, chat background |
| `pipeline/gui_textured`, `gui_textured_premultiplied_alpha`, `gui_opaque_textured_background`, `block_screen_effect`, `fire_screen_effect` | `core/position_tex_color` (Sampler0 = GUI atlas or a texture) | every `blitSprite`: buttons, text fields, sliders, checkboxes, scroller, tooltip bg/frame, `popup/background`, the `menu_background` / `inworld_menu_background` tiles, HUD sprites, PiP item/entity results (premultiplied variant) |
| `pipeline/gui_text`, `gui_text_intensity` | `core/rendertype_text`, `core/rendertype_text_intensity` (Sampler0 = font page, Sampler2 = lightmap; the GUI_TEXT snippet adds no depth test and the fog snippet) | all GUI text, **including dialog titles, bodies and button labels** |
| `pipeline/text*` (world) | same `rendertype_text*` programs plus `_see_through` variants | name tags, signs, text displays |
| `pipeline/panorama` | `core/panorama` | title-screen cubemap |
| `entity_outline_blit`, `tracy_blit` | `core/blit_screen` | glowing outline copy |
| post effect `minecraft:blur` | `post/box_blur.fsh` + `core/screenquad.vsh` | menu background blur |

Inputs, from the vanilla 1.21.11 sources. **[H]**

- `DynamicTransforms { mat4 ModelViewMat; vec4 ColorModulator; vec3 ModelOffset; mat4 TextureMat; }`
- `Projection { mat4 ProjMat; }`. In the GUI this is orthographic: `ProjMat[0][0] = 2/guiWidth`, `ProjMat[1][1] = -2/guiHeight`, `[3][3] = 1`.
- `Globals { ivec3 CameraBlockPos; vec3 CameraOffset; vec2 ScreenSize; float GlintAlpha; float GameTime; int MenuBlurRadius; int UseRgss; }`. You get these via `#moj_import <minecraft:globals.glsl>`. `ScreenSize` is in physical pixels, so `ScreenSize.x * ProjMat[0][0] / 2` gives the GUI scale.
- Vertex attributes:
  - `position_tex_color`: `Position, UV0, Color`
  - `gui`: `Position, Color`
  - `rendertype_text`: `Position, Color, UV0, ivec2 UV2`
- In vanilla, `position_tex_color.vsh` and `gui.vsh` hard-copy their uniform blocks. The source comment says "Can't moj_import in things used during startup, when resource packs don't exist". So an override must also inline the blocks, or must only `moj_import` (with the vanilla loading screen still drawn by the vanilla copy). **[H]** for the comment, **[L]** for the consequence.

Can a pack override them?

- `rendertype_text*`, `position_tex_color`, `gui`, `panorama` and the post shaders all load from `assets/minecraft/shaders/` and are pack-replaceable. The wiki warns that core shader replacement "isn't an intended or supported feature and may change at any time". **[M]** ([Shader](https://minecraft.wiki/w/Shader), [McTsts core shader list](https://github.com/McTsts/Minecraft-Shaders-Wiki/blob/main/Core%20Shader%20List.md))
- The McTsts list claims `blit_screen` cannot be overridden. **[L]** It is irrelevant for GUIs anyway.
- 1.21.11 has **no** `IS_GUI` define. GUI vs world text must be told apart by `ProjMat[3][3]`, as our shader does. **[H]**

### Later versions (26.x), for migration

- **26.1** (format 84.0): UI text and items use a separate 1x1 white lightmap. Lightmap-sampling changes touched `rendertype_text.vsh`. Text shaders begin merging into defines. **[M]** ([26.1](https://minecraft.wiki/w/Java_Edition_26.1), [Shader history](https://minecraft.wiki/w/Shader))
- **26.2** (format 88.0): `rendertype_text`, `_see_through`, `_intensity`, `_intensity_see_through`, `text_background` and `text_background_see_through` are **replaced by `core/text` and `core/text_background`**, with defines `IS_GUI`, `IS_SEE_THROUGH` and `IS_GRAYSCALE`. The depth buffer was reversed. New `gui/sprites/friends/*` sprites were added. **[M]** ([26.2](https://minecraft.wiki/w/Java_Edition_26.2), [MCME 26.2 RP changelog](https://www.mcmiddleearth.com/community/threads/26-2-changelog-5-7-for-the-resource-pack-team.7899/))
  - **Our `rendertype_text.vsh` stops applying on 26.2+.** The HUD anchor and the rainbow silently disappear until the logic is ported to `core/text.vsh` (and `#ifdef IS_GUI` can replace the ProjMat test).
  - 26.2 snapshot 2 fixed a softlock when launching with an incompatible core-shader pack (MC-307296). **[M]**
- **26.3** (format 97.1): OIT replaces Improved Transparency, `rendertype_clouds` becomes `clouds`, and `Globals` members were reordered. Always `moj_import globals.glsl` rather than copying it. **[M]**
- **26.4 snapshot 2** (format 99.0): `screenquad.vsh` becomes `screentriangle.vsh`. Any overridden `post_effect/*.json` must follow this. **[M]** ([26.4 snap 2](https://minecraft.wiki/w/Java_Edition_26.4_Snapshot_2))
- I found no wiki mention of new dialog sprites or dialog styling fields after 1.21.6. **[M]**
- I did not download 26.x jars to verify `gui` and `position_tex_color` there.
- Multi-version: use `min_format`/`max_format` and `overlays` in `pack.mcmeta`, with a 1.21.11 overlay holding `rendertype_text.vsh` and a 26.2+ overlay holding `text.vsh`. **[M]** ([Resource pack](https://minecraft.wiki/w/Resource_pack))

## 2. Known shader tricks, and which work on dialogs

| Trick | How | Works on dialog? |
|---|---|---|
| Colour-key markers on text | Low bits or an exact RGB in `Color` (our approach). Adventure strips alpha, so markers must ride on RGB. | **Yes** [H]. Dialog title, body and labels all go through `pipeline/gui_text` → `rendertype_text`. Our current `guiY < 120` gate would need a separate signature for dialog art. |
| Move, scale or anchor glyphs | Edit `gl_Position` in the vsh. Use `ProjMat` or `ScreenSize` for screen-relative anchoring (edge, centre, fraction). Scale around a pivot for a GUI-scale-independent size. | **Yes** [H/M] |
| Stretch one glyph to full screen | Per-corner override using `gl_VertexID % 4` (QUADS, 4 verts per glyph), writing clip coordinates ±1 directly. | Likely **yes** [L]. Common community trick; not verified on 1.21.11. |
| Hide text shadow | Use the `shadow_color: 0` text style (1.21.4+, no shader). In a shader, shadow verts carry colour×0.25 and are offset 1px, so they can be detected and discarded. | **Yes**. Prefer `shadow_color` [M]. Our low-bit signature already fails on shadow colours, so shadows are not re-anchored and stay behind. Kill them. |
| Hide or recolour a specific sprite | `position_tex_color.fsh`: discard texels with a magic alpha or colour (for example α = 254). The vsh can `texture()` Sampler0 at a corner UV to tag a whole quad. | Possible [M/L]. Prefer simply editing the sprite PNG. |
| Detect "this is a dialog" | No screen ID reaches shaders. `inworld_menu_background` is also drawn by the pause menu and options. A dialog only "identifies" itself through marker glyphs it carries. | Only via markers [H] |
| Read `MenuBlurRadius` / `GameTime` | Available in `Globals` | Yes [H] |

Hard limits. **[H]**

- **Scissor.** Shader-moved vertices are still clipped by the element's scissor rectangle:
  - The dialog **body** (`plain_message`, multi_action buttons and inputs) sits inside `ScrollableLayout$Container`, which always `enableScissor`s to the content area between header and footer.
  - Button and title labels are scissored **only when the text is wider than the widget**. `ActiveTextCollector.defaultScrollingHelper` branches on width before `withScissor`. Zero-net-advance labels are never clipped.
- **Draw order.** Each render-state node has `elementStates` (sprites) and then `glyphStates`, so within a node text draws over sprites. Nodes are stacked by CPU-side overlap of `ScreenArea`. A shader-moved glyph keeps its CPU bounds, so order against far-away widgets is decided by its original position. **[H]** for structure, **[L]** for the edge cases.
- **Click areas.** Shaders move pixels, never hit boxes. Buttons are clickable where the vanilla layout put them.

## 3. GUI sprites relevant to dialogs (1.21.11)

What a dialog screen actually uses. **[H]**

- **Background, in world:** `blurBeforeThisStratum()` if the blur option is ≥ 1, then `textures/gui/inworld_menu_background.png`, a tiled 16x16 of `(0,0,0,64)`. It is a plain texture, not an atlas sprite, drawn via position_tex_color. `DialogScreen` doesn't override `isInGameUi()` (false), so the `fillGradient` darkening is not used. There is no header or footer separator, because DialogScreen does not draw them.
- **Buttons** (action buttons, the multi_action list and the footer exit): `widget/button`, `button_highlighted` and `button_disabled`.
- **Warning button** (header, next to the title, 20x20): `dialog/warning_button`, `_highlighted` and `_disabled`. It has no `.mcmeta`, so it stretches.
- **Inputs:**
  - `text` uses `widget/text_field` and `text_field_highlighted` (nine_slice 200x20, border 1). The multiline variant uses `AbstractTextAreaWidget`, which takes the same sprites plus `widget/scroller`.
  - `boolean` uses `widget/checkbox`, `checkbox_highlighted`, `checkbox_selected` and `checkbox_selected_highlighted`.
  - `number_range` uses `widget/slider`, `slider_highlighted`, `slider_handle` and `slider_handle_highlighted`.
  - `single_option` is a CycleButton, so it uses the button sprites.
- **Scroll bar:** `widget/scroller` and `widget/scroller_background`, shown when the body overflows.
- **Tooltips:** `tooltip/background` (nine_slice 100x100, border 9) and `tooltip/frame`. These are used for button tooltips and the warning tooltip.
- `popup/background` is used by PopupScreen, not by dialogs.

Layout facts that matter. **[H]**

- `HeaderAndFooterLayout`, default header and footer 33 px.
- Title row = `StringWidget` + warning button, spacing 10.
- Body = vertical `LinearLayout`, spacing 10, centred, inside a `ScrollableLayout`.
- multi_action, server_links and dialog_list put their buttons **in the body** (`packControlsIntoColumns`). Their exit button and the notice/confirmation buttons go in the **footer**.
- `width` / `button_width` range 1..1024 (default 150 or 200). [Dialog wiki](https://minecraft.wiki/w/Dialog) [M]

`.mcmeta` `gui.scaling` **[M]** ([Resource pack](https://minecraft.wiki/w/Resource_pack))

- `stretch` is the default.
- `tile` and `nine_slice` need `width`/`height`.
- `nine_slice` also needs `border` (an int or `{left,top,right,bottom}`) and takes an optional `stretch_inner` (default false).
- Our button sprites use `nine_slice 200x20 border 7`. **[H]**

Transparent buttons. A fully transparent `widget/button*` PNG is legal: `position_tex_color.fsh` discards α = 0. The label still renders, so glyph art in the label (or behind it) shows through. **[H/M]**

- **This is global.** Every vanilla screen's buttons (pause, options, chat-confirm, etc.) become invisible too.
- Safer options:
  - Use a **marker pixel/alpha in the sprite** plus a `position_tex_color` fsh that drops it only when a condition holds. Hard, because there is no dialog signal.
  - Keep a subtle frame-only sprite.

Per-button looks. There is no per-widget sprite selection for dialog buttons, and `tooltip_style` only exists for item tooltips. Sprites are global per state. **[H]** The per-button look has to come from the **label component**, using a custom-font glyph with zero net advance (so no scissor) plus a colour marker for shader effects.

- Hover: the label does not change with hover. `button_highlighted` is the only hover signal, so give it a global frame or glow drawn under the art.
- Inactive buttons tint labels grey (`0xA0A0A0` multiplies), which breaks exact-colour markers. Low-bit markers survive only if you design for that. **[L]**

## 4. Blur and menu background

- The **client option** "Menu Background Blur" (`getMenuBackgroundBlurriness`, 0 disables) is the player's. **[H]**
- A pack can **neutralise or restyle blur**: override `assets/minecraft/shaders/post/box_blur.fsh` (used only by `post_effect/blur.json`), for example `fragColor = texture(InSampler, texCoord);`. You can also override `post_effect/blur.json` itself; it references `core/screenquad`, renamed to `screentriangle` in 26.4. **[H]** for files, **[M]** for pack-overridability.
  - The blur radius arrives as `MenuBlurRadius` in `Globals`, so a custom fsh can do tint or vignette instead.
  - Blur is screen-wide and identical for pause, options and dialogs. You can't restyle dialogs only.
- The **darkening tile**: replace `textures/gui/inworld_menu_background.png` (and `menu_background.png` for the title screen). Fully transparent removes the dim, and any colour or pattern restyles it. This is also global to in-world menus. **[H]**

## 5. Font tricks inside GUI text

- **Glyph size cap is vanilla.** `FontTexture` is a fixed 256x256 page, and `GlyphStitcher.stitch` returns null when a glyph doesn't fit a fresh page. The wiki: "Glyphs themselves must not be larger than 256×256 pixels." **[H]**
- **The "font atlas resizing" message is from the ImmediatelyFast mod, not vanilla.** IF swaps the 256 constant for `font_atlas_size` (default 1024). It disables that when a pack overrides any shader on its blacklist (`core/text`, and `rendertype_text` on older builds). A pack opts back in with this in `pack.mcmeta`:
  ```json
  "immediatelyfast": { "compatible_features": ["font_atlas_resizing"] }
  ```
  Opting back in only helps IF users. Vanilla players still lose >256 glyphs, so the `.split` approach remains required. **[H]** (source: `RaphiMC/ImmediatelyFast` `MixinMinecraft`, `ImmediatelyFastResourcePackMetadata`, `MixinFontTexture`)
- **Bitmap providers:** `height` (default 8) sets the rendered size in GUI px. Texel scale = `height / cell_height`. `ascent` shifts it vertically. Large heights and negative ascents are used already (`height 256`, `ascent -32768`). **[M]** ([Font](https://minecraft.wiki/w/Font))
- **Negative space:** `space` providers set any advance (negative works), which gives zero-net-advance layouts. **[M]**
- **GUI scale:** one GUI px = `guiScale` physical px, so glyph texels render at `guiScale * height/cell_height` physical px. A 256-texel glyph at `height 256` and GUI scale 3 is 768 physical px. Full-screen art at GUI scale 4 or "auto" can exceed the screen. Re-scale in the vsh with `ScreenSize` and `ProjMat` if a fixed physical size matters. **[H/M]**
- **Shadows:** `shadow_color: 0` on the component (1.21.4+) is cleanest. Shadow vertices are separate quads with darkened colour, so shader detection by colour is possible but brittle. **[M]**

## 6. Recommendation: full-screen custom panel inside a dialog

The most robust path with the existing setup:

1. **Carrier = the dialog `title`.** It sits in the header, outside the body's scroll scissor, and is always drawn. Build the panel as zero-net-advance glyph strips (the existing `.split` pipeline, each source ≤ 256x256) with `shadow_color: 0`. Avoid putting art in `plain_message`: it is scissored to the body area.
2. **New signature**, for example CENTER `(5,2,7)` → `0xFDFAFF`. Leave it **un-gated** by `guiY` (or gate it on a second marker). The vsh offsets marked glyphs from the title's origin to the **screen centre**. Vertically: title baseline ≈ header middle, then shift by `+0.5*guiHeight - headerOffset`. Optionally scale about the centre to fit `ScreenSize`.
3. **Keep native widgets for interaction** and design the art around their deterministic layout:
   - Body content is centred horizontally and sits in the area between the 33 px header and the footer.
   - Buttons have widths you choose (1..1024), plus column count and 10 px spacing.
   - Anchor the art to the screen centre so it lines up across resolutions.
   - Give each button its own look through its label: a zero-advance glyph image with the button's art.
   - Make `widget/button` sprites near-transparent with a thin highlighted frame for hover, accepting the global effect. Alternatively, keep them, restyled to the theme.
   - Hit boxes never move.
4. **Background:** restyle `inworld_menu_background.png`. Optionally make `post/box_blur.fsh` a pass-through or tint. Both are global to in-world menus.
5. **Ship as overlays:** a 1.21.11 overlay (`rendertype_text.vsh`) and a 26.2+ overlay (`core/text.vsh` using `#ifdef IS_GUI`). Set `pack_format` to match the server (75 for 1.21.11), with `min_format`/`max_format`. Add the IF `compatible_features` entry.
6. Do not hide the `dialog/warning_button`. It is the player's disconnect/escape affordance. Restyle it at most.

Risks: core-shader overrides are unsupported and churn every release (26.2 rename, 26.3 Globals reorder, 26.4 screenquad rename). Global sprite changes affect every vanilla screen. Text over 256 px per glyph must stay split.
