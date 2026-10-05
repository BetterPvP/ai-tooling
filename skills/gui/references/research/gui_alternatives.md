# Full-screen custom GUIs without client mods: alternatives to dialogs

Research date: 2026-10-05. Target: Paper 1.21.11 now, 26.x possible. Server resource pack, no client mods.
Target screens: dungeon lobby (card list, detail + leaderboard, party panel with invite/join, bottom action bar) and gacha banner (tab column, hero art, info + progress bars, summon buttons), hover feedback, clickable anywhere.

Confidence tags: [verified] = confirmed in a fetched source. [known] = established community practice / vanilla behaviour I am confident of but did not re-verify with a fetched page this session. [unverified] = plausible, test before relying on it.

## The hard constraint that decides everything

A vanilla client tells the server almost nothing about the pointer. No packet carries mouse position or hover state. What the server can observe:

- Container clicks: slot index + click type (left, right, shift, middle, number key, drop, double-click, click outside = slot -999). [known]
- Head rotation (yaw/pitch) at tick rate, even while mounted. [known]
- Movement keys: since 1.21.2 the client sends a Player Input packet with forward/back/left/right/jump/sneak/sprint, exposed in Paper as `PlayerInputEvent`. [verified] https://jd.papermc.io/paper/1.21.11/org/bukkit/event/player/PlayerInputEvent.html , https://javadocs.packetevents.com/com/github/retrooper/packetevents/wrapper/play/client/WrapperPlayClientPlayerInput.html
- Hotbar slot change (scroll wheel / 1-9), swap hands (F), drop (Q), arm swing (left click), use/interact (right click). [known]
- Text from anvil rename field, sign editor, book editor, chat, dialog text inputs. [known]
- Dialog `custom` / `dynamic/custom` actions and text-component `custom` click events (1.21.6+). [verified] https://minecraft.wiki/w/Dialog , https://minecraft.wiki/w/Text_component_format

The server cannot learn GUI scale, window size, aspect ratio or FOV without a mod (Noxesium exists precisely to send GUI scale to the server, which shows the gap). [verified] https://modrinth.com/mod/Noxesium

So hover feedback must be produced on the client by vanilla rendering rules (slot highlight, item tooltip, dialog button hover, text hover_event), or computed server-side from head rotation (3D menus).

## 1. Inventory menus with full-screen art

### How it works
- Background art is font glyphs in the container title. Negative-space glyphs (the `space` font provider, 1.19+) move the pen left/up so a bitmap glyph much larger than the chest can be drawn starting off the container origin. Production-standard at MCC Island, Origin Realms, Wynncraft-style servers and every ItemsAdder/Nexo/Oraxen "GUI pack" sold on BuiltByBit. [known; marketplace examples verified] https://builtbybit.com/resources/battlepass-gui-ia-nexo-oraxen.29085/updates , https://builtbybit.com/resources/jungle-inventories-ia-nexo-oraxen.94346/ , https://septicuss.notion.site/Resource-Packs-cf80198cd49944128570b33d71053036 (Origin Realms credited for the font-GUI technique)
- Buttons are items in slots with an `item_model` pointing to transparent or decorative models; `tooltip_display` hides tooltips on pure-decor slots; `tooltip_style` (1.21.2+) gives a per-item tooltip background/frame sprite, so each button can have its own styled hover card. [verified for tooltip_style paths] https://minecraft.wiki/w/Data_component_format/tooltip_style , https://builtbybit.com/resources/ntooltip-tooltip-style-manager.104080/
- Hiding the player inventory: send empty items for the player-inventory slots (packet rewrite of WINDOW_ITEMS/SET_SLOT) and draw over the lower half of the container texture; caveat reported: hover highlight on those slots looks off while the tooltip still shows. [verified] https://www.spigotmc.org/threads/is-it-actually-possible-to-hide-the-player-inventory-when-opening-a-gui-not-just-lock-it.717037/ . Alternatively blank the container sprite and the "Inventory" label in the pack (global, or shader-gated). [known]
- Core shaders: the GUI shaders can reposition/scale geometry (e.g. McTsts utilities move GUI parts, include a GUI-scale helper). [verified] https://github.com/McTsts/mc-core-shaders . A shader can detect a marker (title glyph colour, special texture) and re-anchor or re-scale the art to the screen so it fills any window. Same technique your pack already uses for the boss-bar HUD (`Resourcepack/pack/assets/minecraft/shaders/core/rendertype_text.vsh`, low-bit colour signature, clip-space anchoring).

### What it cannot do
- Click hit areas are the vanilla slot rects, computed client-side from the container layout. Moving pixels in a shader does NOT move hit boxes. A 6-row chest + player inventory gives a fixed 9x10 grid of 18 GUI-px cells (~162x~200 GUI px). Every clickable must sit on a cell; a "big button" = several cells with the same item. Clicks outside the window arrive as slot -999 (one extra "background" target). [known]
- Hover: only per-slot. Vanilla draws `container/slot_highlight_back` and `slot_highlight_front` sprites around the hovered slot (1.21.2+), globally styled, not per item. [verified] https://bugs.mojang.com/browse/MC-277202 . Item model definitions have no "hovered" condition, so no item_model swap on hover. [known, medium-high] The only per-button hover visual is the tooltip (custom style + glyph art in lore), which floats at the cursor. Shader-detecting the highlight quad to enlarge it is possible in theory [unverified].
- Text input: none in a chest. Pair with anvil/sign/dialog.
- Live updates: excellent. Slot items update per tick; the title can be re-sent (Paper `InventoryView#setTitle` / open-screen packet) to redraw the art and baked text (progress bars, leaderboard rows as glyph text) without closing. [known]
- GUI-scale: whole screen scales uniformly with GUI scale, so the layout is self-consistent, but art larger than ~176x222 GUI px will clip off-screen at GUI scale 4 on 1080p (480x270 GUI px) or on small windows. Use a shader to scale/anchor, or keep art within ~ 400x250 GUI px. [known]

### Effort
Low-medium for chest-sized art (the project already has font glyph pipelines). Medium-high for shader-scaled full-screen art. Fits an existing inventory menu framework well.

## 2. In-world 3D menus (display entities in front of a locked camera)

### How it works
- Mount the player on an invisible entity (or spectate via camera packet), spawn per-viewer packet-only text/item/block displays (and 1.21.9+ mannequins for party-member figures), read head rotation as the cursor, raycast against button rects for hover, use swing / interact packets for click. [verified] Aurus Menus: "the player is mounted on an invisible camera entity", "fake entities ... spawned via packets", "a floating cursor follows the player's head movement", Paper 1.20+, PacketEvents. https://modrinth.com/mod/aurus-menus . CustomScreenMenu (BuiltByBit): TextDisplay + ItemDisplay, camera-controlled cursor with hover and click. https://builtbybit.com/resources/customscreenmenu.108929/ . DisplayUIEngine (library, small). https://modrinth.com/project/8pGdBoEs
- Interaction entities give native click targets (attack/interact events) without raycasting, but raycasting against your own rects is finer-grained. [known]
- Extra input: scroll wheel via held-slot change (cancel it, treat as scroll), WASD/space/shift via PlayerInputEvent for keyboard navigation, F/Q as hotkeys. [verified for input packet]

### Strengths
- Truly free positioning, real depth, item/block/player models, animation via display interpolation, hover feedback anywhere (server knows the cursor), live updates (text display metadata), per-viewer.
- Hover can drive any visual (glow, scale tween, swap model) because the server computes it.

### Weaknesses
- Cursor = head rotation: camera-steered pointing feels unlike a mouse, and the crosshair is the cursor. Acceptable for a lobby/gacha with big buttons; poor for dense lists.
- FOV and aspect ratio are client settings the server cannot read; edges of a "full-screen" layout drift. Design for a safe central region (about 70 deg FOV equivalent) or counter it in a shader [unverified].
- World behind the menu shows through unless you build a backdrop (big display panel). 26.3 `/posteffect` helps here (blur behind). [verified] https://minecraft.wiki/w/Commands/posteffect
- No text input; latency: hover reacts at tick/ping rate (50 ms + RTT), visible on high ping.
- Effort: high (camera state machine, teardown on disconnect/damage/teleport, per-viewer packets). The project already has scene/prop/cutscene camera infrastructure, which lowers it.

### Production
The big networks (Hypixel, MCC Island, Wynncraft) still ship container menus for most screens; display-entity UIs appear mostly as in-world boards/holograms and cutscene-like set pieces. Marketplace plugins (Aurus, CustomScreenMenu) target lobby/login screens. [known; no first-party write-up found]

## 3. HUD / screen-space UIs via core shaders

### How it works
- Glyphs placed with a huge negative ascent (parked off screen) in boss bar / action bar / title text; the text vertex shader recognises them (colour signature) and moves them to screen anchors in clip space, independent of GUI scale. [verified] HUDEngine (Paper/Folia 1.21.4 to 26.3): https://github.com/Nacvark/HUDEngine ; BetterHud (Bukkit 1.21 to 26.1.x): https://github.com/toxicity188/BetterHud ; SharkMinimap (vanilla minimap via text shader): https://github.com/XPDD34D/SharkMinimap ; your own `rendertype_text.vsh` does exactly this.
- Pair with an input method: scroll wheel (hotbar slot change), WASD (PlayerInputEvent), head rotation as cursor, number keys.

### Verdict
Great for persistent overlays (party frames, timers, progress), carousel-style pickers (scroll to cycle banners), and backdrops. No mouse, no hover by pointer, no text input. GUI-scale robust when anchored in shader. Effort medium. Shader stability risk (see section 6).

## 4. Other vanilla screens repurposed

- **Merchant (villager trade)**: native scrollable left list of up to many offers with hover tooltips and click selection, plus a right panel area. Closest vanilla match to "left list of cards"; the right side is free for title-glyph art. List cells are fixed size/layout. [known]
- **Stonecutter / loom**: scrollable grid of selectable buttons (stonecutter 4 columns), selection reported via container button click; good for icon pickers (banner tabs, cosmetics). [known]
- **Anvil**: the only free text input that live-updates per keystroke (rename field fires PrepareAnvil). Good for search/party-name entry. [known]
- **Sign editor**: 4 short lines of text input via fake sign packet. [known]
- **Book**: pages of text with click_event/hover_event on any span (including `custom` and `show_dialog` since 1.21.6) and glyph art; hover tooltips anywhere text exists. Fixed page size; no live update while open (must re-open). [verified for click events] https://minecraft.wiki/w/Text_component_format
- **Cartography / enchanting / beacon**: fixed, narrow use; little gain.
All are re-textured globally by the pack unless gated by a shader marker; you can make them look custom but the layout is Mojang's. [known]

## 5. Dialogs (for comparison)

- Fixed stacked layout: title, body (plain_message, item), inputs (text, boolean, single_option, number_range), then actions; `multi_action` has `columns`, buttons have `width` (1-1024) and a hover `tooltip`. No X/Y positioning (a recurring feedback request). [verified] https://minecraft.wiki/w/Dialog , https://feedback.minecraft.net/hc/en-us/community/posts/38874467532813-Add-Positioning-X-Y-for-Dialog-UI-Elements , https://feedback.minecraft.net/hc/en-us/community/posts/48148157630221-More-Flexible-Layout-Options-for-Dialogs
- Strengths: real mouse hover and click, real text inputs, sliders, checkboxes, scrolling, scales with GUI scale, server receives inputs as NBT via `dynamic/custom`. Text components support fonts, so glyph art and object sprites (1.21.9 `object` atlas/player components) can decorate bodies. [verified for object component] https://minecraft.wiki/w/Text_component_format
- Weaknesses: no free layout, no live update in place (re-send the dialog), vanilla button chrome (re-texturable globally via widget sprites). No dialog changes found in 1.21.7 to 26.3. [verified absence in wiki history; medium]
- Production: FancyDialogs, DialogWindow, LuxDialogues. https://docs.fancyinnovations.com/fancydialogs/ , https://modrinth.com/plugin/dialogwindow

## 6. 26.x releases (26.1 to 26.3, released 2026-09-15)

- 26.1: item model `transformation` fields on composite/condition/select/etc.; GUI text/items use a separate white lightmap. No new screens. [verified] https://minecraft.wiki/w/Java_Edition_26.1
- 26.2 (2026-06-16): `rendertype_text*` shaders replaced by `core/text` and `core/text_background` with defines (IS_GUI, IS_SEE_THROUGH, IS_GRAYSCALE); depth buffer reversed; experimental Vulkan backend, pack shaders compiled GLSL to SPIR-V with small rewrites; more GUI sprites moved to `position_tex_color`. Any text/HUD shader (including yours) must be ported. [verified] https://minecraft.wiki/w/Java_Edition_26.2 , https://www.mcmiddleearth.com/community/threads/26-2-changelog-5-7-for-the-resource-pack-team.7899/ , https://minecraft.wiki/w/Shader
- 26.3: `/posteffect add|remove|clear <players> <id>` lets the server apply resource-pack post effects (`assets/<ns>/post_effect`) to a player: menu backdrops (blur/darken/vignette) for 3D or HUD menus. OpenGL now compiles via ShaderC (stricter; `#version` must be first line). [verified] https://minecraft.wiki/w/Commands/posteffect , https://minecraft.wiki/w/Shader
- Nothing adds a new server-drivable screen, free-layout dialogs, or pointer reporting. Core-shader overrides remain "not an intended or supported feature". [verified] https://minecraft.wiki/w/Shader

## Comparison

| | Free position | Hover | Click targets | Text input | Live updates | GUI-scale robust | Effort | Production |
|---|---|---|---|---|---|---|---|---|
| 1 Inventory + glyph art (+shader) | Art yes; hits on 18px slot grid only | Per-slot highlight + styled tooltip | 90 slot cells + outside | No | Excellent (items, title re-send) | Good inside ~176x222; shader for bigger | Low-Med (Med-High with shader) | MCCI, Origin Realms, Wynncraft, IA/Nexo packs |
| 2 3D display menus | Full | Anywhere (server computes) | Anywhere | No | Excellent | FOV/aspect dependent | High | Aurus, CustomScreenMenu; lobbies |
| 3 Shader HUD + keys | Full (visual) | No pointer | None (keys/scroll) | No | Good (bossbar/actionbar) | Excellent (clip space) | Medium | HUDEngine, BetterHud, your HUD |
| 4 Merchant/stonecutter/anvil/sign/book | Mojang layout | Native per element | Native widgets | Anvil, sign, book | Merchant/anvil yes, book no | Good | Low | Common |
| 5 Dialog | No | Native buttons | Native | Yes (best) | Re-send only | Good | Low | FancyDialogs etc. |

## Recommendation

- **Dungeon lobby (list, detail + leaderboard, party, action bar): inventory menu with title-glyph art, laid out on the 9x10 slot grid.** Card list = column of slot buttons (pagination/scroll arrows), detail panel and leaderboard = glyph text in the title re-sent on selection, party slots = player-head items, action bar = bottom row. Hover = styled tooltips. Add a core shader only if you want art beyond ~176x222 GUI px. Party name or search entry via anvil or a dialog popup. Confidence: high.
- **Gacha banner: same inventory approach**, hero art in the title, progress bars as glyph strings, tabs as a slot column, summon buttons as multi-slot buttons. If a cinematic summon reveal is wanted, hand off to a short 3D/display-entity sequence (camera + item displays + `/posteffect` on 26.3), not a full 3D menu. Confidence: high for the menu, medium for the reveal.
- **3D display menus**: only for set-piece screens where spectacle beats precision (lobby "hub" selector, character select, reveal animations). Not for dense lists. Confidence: medium.
- **Shader HUD**: persistent overlays and carousel pickers, not primary menus. Confidence: high.
- **Dialogs**: forms, confirmations, settings and any text entry, popped on top of an inventory flow. Confidence: high.
- Migration note: moving to 26.2+ means porting the existing `rendertype_text.vsh` HUD to `core/text` and testing on Vulkan; keep shader-dependent UI optional-degrading. Confidence: high.
