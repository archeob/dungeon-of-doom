# Dungeon of Doom — Recreation Changelog

Entries in ascending version order (oldest first).

---

## v0.001 — 2026-03-06
### Initial playable build

- 100×100 dungeon maps with three-tier generation:
  - Floors 1–13: scattered wall pillars (scatter algorithm)
  - Floors 14–27: organic cave shapes (cellular automaton)
  - Floors 28–40: winding single-tile-wide maze (recursive backtracker)
- 9×9 tile viewport centred on player — faithful to original Mac layout
- 96×96 pixel art sprites drawn procedurally; black knight player sprite
- Checkerboard floor pattern for easy navigation; mini-map in stats panel
- Mac Platinum menu bar; Stats panel: HP/Food/XP bars, D&D attributes, equipment
- Message log with fading older messages
- 7 character classes with authentic D&D attributes
- All 22 original monsters defined; full 50-item table; all 26 original Rumors
- Character creation, death and victory overlay screens
- Original Mac key bindings + WASD + arrows + numpad + Vi keys
- Persistent floor maps; basic combat, XP, levelling, food/hunger system
- 1920×1080 HD resolution

---

## v0.002 — 2026-03-06
### Map resize + dungeon generator rewrite

- Map resized to 60×60 tiles based on original screenshot analysis
  (original ~35×35; 60×60 = 2.8× area for HD variety; mini-map 420×420 px at 7px/tile)
- Complete dungeon generator rewrite — rooms carved from solid rock
  - All walls naturally connected; `_fix_wall_islands()` post-process confirmed 0 islands
  - Depth progression: floor 1 ≈ 40% open → floor 40 ≈ 13% open
- Player sprite: black knight with full plate armour, kite shield, raised sword
- FOV rewritten to remove dependency on `neighbours8`

### v0.002 refinement — generator calibration from screenshots
- Recalibrated from pixel analysis of 7 original screenshots (floors 2–8)
  - Original ~40×40 tiles; 60×60 = 1.5× scale
  - Floors 2–8: 29–36% open (mean 33%), 2–5 rooms — minimal early progression
  - Room sizes scaled 1.5×: 13–33 wide, 9–24 tall; corridors 1 tile wide throughout
  - Removed separate maze tier; deep floors use extra winding corridor connections

---

## v0.003 — 2026-03-07
### Stair auto-transition

- Walking onto a stair tile immediately moves to the connected floor (no key needed)
- Blind on stairs: viewport fully black while standing on a stair (atmospheric effect)
- Floor 1 `T_STAIR_UP` preserved: marks the surface entrance; exit blocked without the Orb

---

## v0.004 — 2026-03-07
### Orb exit lock + DDA raycasting FOV

- Stair exit blocked on floor 1 without Orb of Carnos (carrying Orb → PHASE_WIN)
- Real wall-blocked FOV: proper DDA traversal to each tile in radius
  - Wall faces visible; floor behind walls is not; correct in all 8 directions
- Mini-map now shows walked path only (`fov.walked`); `fov.explored` used for reveal-map scroll

---

## v0.101 — 2026-03-07
### Mouse movement + Mac menu bar

- Viewport click-to-move: 8-way directional sectoring, hold-to-repeat (220 ms / 70 ms)
- Menu bar: exact original structure — File | Control | Use | Inventory | Help
  - Mac black-on-white aesthetic; dropdown with shadow; blue selection highlight
  - Full item lists per original including ^ (Ctrl) shortcuts

---

## v0.103 — 2026-03-07
### Save / load system

- JSON format (.dod); seed-based floor regeneration keeps files small
- Saves: player state, log, all floor spawn tables, FOV walked/explored per floor
- File menu wired: New, Open, Close, Save, Save As, Quit — each prompts if dirty
- Ctrl+S shortcut for Save

---

## v0.104 — 2026-03-07
### Title screen + character creation screen

- `TitleScreen`: white bg, "The Dungeon of Doom" in Gothic serif 96 pt, ornamental rule,
  two-column layout (art placeholder + Hall of Fame), four buttons (New/Open/Resume/Quit)
- `CharCreateScreen`: name input, class list with stats panel, stat bars colour-coded
  (green ≥16, red ≤8); full mouse + keyboard support

---

## v0.105 — 2026-03-07
### Visual theme — black on white throughout

- `StatsPanel` fully rewritten: white background, Gothic serif headers, colour-coded bars
- New light-theme constants: `C_LPANEL_BG`, `C_LTEXT`, `C_LTEXT_DIM`, `C_LTEXT_ACCENT`
- Credits: Sébastien Racine added as Producer

---

## v0.106 — 2026-03-07
### Layout overhaul — faithful to the 1985 original

- Ornate viewport border: parchment-cream band (BORD=20 px), outer black frame,
  diamond ornaments — matches the decorative woodcut border of the 1985 Mac original
- Right panel: Gothic serif name box, upper quadrant (420×420 mini-map + stats column),
  lower quadrant ("Information" + 10-message log, newest-first, fading)
- Mini-map: black-on-white; walls = dark grey, floor = black, stairs = triangle indicator

---

## v0.107 — 2026-03-07
### Fraktur headings + panel geometry fixes

- KaTeX Fraktur Bold (`assets/KaTeX_Fraktur-Bold.ttf`) for all display headings;
  buttons retain FreeSerifBold
- `RECT_STATS` corrected: both panels end at `MENU_H + VP_PX = 896 px`
- Map compacted: MM=5 (300×300 px); secondary stats moved below map
- `SCREEN_H = 896 px` (was 1080 px) — 184 px dead strip eliminated

---

## v0.108 — 2026-03-07
### Narrower panel + compact layout

- Panel halved: `STATS_W` 1056→528, `SCREEN_W` 1920→1392
- Map: MM=3 (180×180 px); Gold and Turn indicators removed
- ATK/AC inline with equipment: `ATK +8   Wpn: Long Sword`
- Stats as label + right-aligned value column

---

## v0.201 — 2026-03-07
### Full item system

- Item table (data/items.py): 80 items across 9 categories; identification pools shuffle per run
  (17 potion colours, 14 scroll names, 11 wand materials, 7 ring gems)
- Effects engine: `apply_effect()` resolves all potion/scroll/food/wand effects
  (healing, stat bumps, status flags, targeted wand attacks)
- Inventory overlay: full-screen Mac-style, items grouped by category, letter selection a–t,
  detail pane, identify mode; keyboard + mouse support
- Save/load updated to persist `id_map`, `identified`, `pending_identify`
- Player gains `cloak` slot and status flags (invisible, levitating, resist_fire, etc.)

---

## v0.202 — 2026-03-07
### Inventory mouse interface + bug fixes

- `handle_click()` / `handle_motion()` on `InventoryScreen`; click-outside closes
- E/U/D key conflict fixed; food removal copy/original bug fixed
- Shared helpers: `_inv_use`, `_inv_equip`, `_inv_drop`, `_inv_identify`

---

## v0.203 — 2026-03-07
### Inventory menu, Pickup Mode, bulk-drop, ATK fix

- Combat fix: `attack_bonus` includes weapon enchant; `weapon_damage_range` reads `base_dmg`
- Inventory close button (×), all nine menu items wired, drop-by-category helpers
- Pickup Mode toggle (`game.pickup_mode`); Control menu checkmark updates live

---

## v0.204 — 2026-03-07
### Gothic buttons + rendering fixes

- Inventory buttons: FreeSerifBold, 2 px border; verb labels Drink/Read/Eat/Zap
- Overlay closes immediately after successful use
- Menubar uses DejaVu Sans Mono for checkmarks; ⌘ → ^ (Ctrl) throughout

---

## v0.205 — 2026-03-07
### Equipment slot panel + missile slot

- Inventory right column: item detail (upper) + equipment grid (lower — Weapons/Armor/Rings/Missiles)
- Missile slot `player.equipped["missile"]`; throwing weapons readied via inventory
- Checkmark square fixed (`♦`); equipped-items-listed-twice save/load bug fixed
- "Get an Item" wired to new `pick_up_forced()` method

---

## v0.206 — 2026-03-07
### Wand aiming system (PHASE_WAND_AIM)

- `begin_wand_aim(item)` → `PHASE_WAND_AIM`; direction chosen with arrow/numpad keys
- `fire_wand_at_direction(game, item, dx, dy)`: WIS-based accuracy, deflects 45° on miss
- `_PIERCING_WANDS`: lightning/ice pass through multiple monsters
- `WAND_RAY_COLORS`: each wand has a distinct grey-tone beam
- `game.ray_anim` drives renderer overlay animation

---

## v0.207 — 2026-03-07
### Diamond status indicator + Use menu hotkeys

- Status diamond drawn with `pygame.draw.polygon` (Courier New lacks ♦)
- Use menu Q/R/Z/E shortcuts open `QuickUseScreen` for Drink/Read/Zap/Eat

---

## v0.208 — 2026-03-07
### Enchant identification + fuzzy pickup hints

- Enchant value on item dicts; `+N` suffix after identification
- `_apply_fuzzy_enchant()`: class-based fuzzy hints on pickup
- `_roll_enchant()`: weighted roll (−2 to +3, centred on 0)
- Identify scroll clears fuzzy; `+0?` shown for unconfirmed zero enchant

---

## v0.209 — 2026-03-07
### Throw aiming system (PHASE_THROW_AIM)

- T key → missile overlay → `PHASE_THROW_AIM`
- `throw_item_at_direction()`: DEX accuracy; sling bonus damage
- Rocks: bundle ammo (`throws` counter); darts/spears/Mac Plus: individual (always removed)
- `THROW_ITEM_COLORS` per projectile type

---

## v0.210 — 2026-03-07
### Starting equipment + class expertise

- `_grant_starting_kit()`: each class receives floor-0 gear
- Knight: fuzzy-guesses armour enchant on pickup; Fighter: weapons; Jeweler: rings
- Sage: auto-reads scrolls safely; Wizard: wands never misfire; Alchemist: never drinks harmful potion

---

## v0.211 — 2026-03-07
### Wish system (PHASE_WISH)

- `resolve_wish(game, text)`: parses `[plural] <item name> [+N]`, grants named item
- Wands granted with full charges; enchant > max capped to random(1, max)

---

## v0.212 — 2026-03-08
### Spawn rate rebalance

- Monster density: `n_mon = min(tiles//20, 8 + floor//3)`
- Item spawn rates per category scaled with floor depth; wands floor 5+, rings floor 8+, gems floor 15+

---

## v0.213 — 2026-03-08
### Weapon damage dice + weight/carry system

- `base_dmg` on all weapons (dice notation, e.g. `[2,6]` = 2d6)
- Carry capacity: `30 + STR×5`; `encumbered` (>50%) halves movement; `overburdened` (>100%) blocks movement

---

## v0.214 — 2026-03-09
### High-resolution greyscale sprites

- All sprites drawn at 3× internal resolution (288 px), `smoothscale`'d to 96 px
- Pure greyscale palette — faithful to the 1985 Mac aesthetic with shading depth
- Floors: gradient + grout border; walls: staggered brick rows with mortar
- Stairs: bold dark chevrons; player: dark plate armour with highlight rim
- Monsters: tier-based darkness (55–95 v); items: iconic silhouettes with glint highlights

---

## v0.301 — 2026-03-10
### Knight sprite revert + spear throw fix

- Player knight sprite reverted to dark plate armour (Crusader redesign reverted per feedback)
  - Draw order: sword → shield → gorget → pauldrons → cuirass → arms → faulds → greaves → helmet
- Sword item sprite: single line from tip (76,12) to base (28,68)
- Spear/dart throw: individual projectiles always removed from inventory immediately on throw

---

## v0.302 — 2026-03-10
### Turn-based time system

- **5-second real-time turns** (`TURN_MS=5000`): auto-Pass fires if player is idle
- **Action costs**: move/attack/throw/wand/drink/equip/rest = 1 turn; scroll = 2; wish = 3; eat = 4
- **Multi-turn actions**: monsters act once per consumed turn
- **Pause**: Space or Control > Pause; PAUSED overlay; resumes with fresh 5 seconds
- **HP regen**: 50% chance of +1 HP every 5 turns
- **Stuffed penalty**: eating past `FOOD_STUFFED=950` halves movement speed

---

## v0.303 — 2026-03-10
### Dungeon generator rewrite — faithful corridor-grid maze

- Completely replaced room+corridor generator with a corridor-grid maze matching the 1985 original
- **Structure**: grid of equal-width corridors separated by single-tile walls,
  connected as a perfect spanning tree (iterative recursive backtracker) — no rooms, no open spaces
- **Corridor width (W) by floor**: 2→9, 5→8, 10→7, 15→6, 20→5, 25→4, 30→3, 35→2, 40→1
  — Formula: `W = max(1, round(9 - floor/5))`
- Corner "pillar" tiles at wall-grid intersections stay solid
- Grid centred in the 58×58 usable interior (1-tile hard border)
- Stairs at two most-distant cell centres; removed `Rect` class and `_fix_wall_islands()`

---

## v0.304 — 2026-03-10
### Boulder tile + wand of Digging rework

**New tile: `T_BOULDER = 4`**
- Wand of Digging now converts walls to boulders on first hit:
  *"The beam crumbles the wall into a boulder!"*
- A second hit destroys the boulder completely: *"The boulder disintegrates!"*
- Wand of Digging bypasses the WIS accuracy check (targets walls, never creatures — always 100% accurate)

**Boulder mechanics**
- Boulders are **not passable** and **not inventory items** — cannot be walked through or picked up
- **Push** (STR ≥ 20): player moves boulder one tile in the facing direction, steps into its old spot;
  costs 4 turns (`AP_PUSH_BOULDER = 4`); message: *"The boulder moves!"*
  - Cannot push if the tile beyond the boulder is occupied (wall, monster, another boulder)
- **Blocked** (STR < 20): *"The boulder is too heavy!"* (turn consumed, player doesn't move)
- Boulders block line of sight (FOV) exactly like walls

**Boulder sprite** (`tile_boulder()` in ui/sprites.py)
- Drawn at 3× (288 px), smoothscaled to 96 px — consistent with all other tiles
- Lit floor background; rounded stone with horizontal band shading (bright top-left → dark lower-right)
- Four fissure/crack lines in dark grey communicate partial destruction
- Cast shadow beneath the boulder; greyscale palette consistent with wall/floor aesthetic

**Save/load persistence** (`DungeonLevel.tile_mods`)
- `tile_mods: dict` records every post-generation tile change as `{(x, y): tile_type}`
- Serialised as `[[x, y, tile_type], ...]` in the floor JSON entry
- On load, tile_mods are replayed onto the freshly generated level
- Both dug-open walls and pushed boulder positions survive save/load cycles

**Constants added**: `T_BOULDER = 4`, `BOULDER_MIN_STR = 20`, `AP_PUSH_BOULDER = 4`

---

## v0.305 — 2026-03-10
### Hall of Fame

**New module: `engine/hof.py`**
- `hof.json` lives next to `main.py` and is **never packaged in release zips** — created
  at runtime on first score submission and survives every version update automatically
- `load_hof()` — returns up to 10 entries sorted by glory; gracefully handles missing/corrupt file
- `submit_entry(game)` — computes glory, deduplicates by `game_id` (same run occupies one slot,
  replaced only if score improves), trims to top 10, writes to disk
- `compute_glory(game)` — returns `(total, breakdown_dict)` with six categories:

| Category | Formula |
|---|---|
| Floor reached | `floor × 100` |
| Character level | `char_level × 150` |
| XP earned | `stat_xp_earned × 2` (cumulative, never resets) |
| Items identified | `len(identified) × 25` |
| Floors explored | `floors_with_≥100_tiles_walked × 50` |
| Victory bonus | `+5 000` flat (only on win) |

**Typical score ranges**: floor-10 death ≈ 1,600 · floor-30 death ≈ 4,950 · victory > 9,000

**New `GameState` fields** (all pre-zeroed in `__init__` and reset in `start_new_game`):
- `game_id` — set to `cache.base_seed`; unique per run; used as deduplication key
- `stat_xp_earned` — cumulative XP counter; incremented in `_kill_monster`; never resets on level-up
- `death_cause` — set just before `PHASE_DEAD`/`PHASE_WIN` in all three death paths and on victory
- `hof_result` — `(entry_dict, rank_or_None)` stored after submission; read by overlay screens
- `_hof_submitted` — guard flag so submission fires exactly once per run

**`main.py` integration**: HoF submitted automatically in the main loop the first frame
`game.phase` enters `PHASE_DEAD` or `PHASE_WIN`.

**Title screen** (`ui/screens.py` — `TitleScreen.draw`):
- Hall of Fame panel now loads and displays real entries from `hof.json`
- Columns: `#` · Name · Cls · Lv · Fl · Cause · Glory (right-aligned)
- Victory entries rendered in gold; death entries in standard dark text
- Empty slots show `—` as before

**Death / Win overlays** (`OverlayScreen`):
- `draw_death` and `draw_win` both call `_draw_glory_panel` which shows:
  - Large **GLORY: N,NNN** total
  - Six-row breakdown (victory row hidden on death)
  - Hall of Fame rank line: *"Hall of Fame — Rank #N"* or *"Score not high enough…"*
- Helper functions: `short_outcome()` (≤12-char abbreviation), `class_abbrev()` (3-char class code)

---

## v0.306 — 2026-03-10
### Difficulty levels + Glory class modifiers

**Four difficulty levels** (selected at character creation; cannot be changed mid-game):

| Key | Label | Effect | Glory |
|---|---|---|---|
| `explorer` | Explorer | HP regen guaranteed every 5 turns (no RNG). Hunger drains at ½ rate. | ×50% |
| `adventurer` | Adventurer | Normal rules — no changes. | ×100% |
| `hero` | Hero | File > Save / Save As disabled. Game auto-saves to `resume.dod` on quit. | ×200% |
| `architect` | Architect *(hidden)* | Enter "Architect" as character name to unlock. All stats 25, all items granted, all items auto-identified. No glory, excluded from Hall of Fame. | ×0% |

**Hero mode details**
- Manual save and Save As are both disabled (log message shown if attempted via menu)
- On quit (window close or File > Quit) the game is silently saved to `resume.dod` next to `main.py`
- `resume.dod` is **never packaged in release zips** — created at runtime
- **Resume button** on the title screen is now enabled whenever `resume.dod` exists (cross-session persistence)
- When a Hero run ends (death or victory), `resume.dod` is automatically deleted

**Architect mode details**
- Triggered by entering the name "Architect" exactly (case-sensitive) at character creation
- All six stats set to 25, HP set to 99
- All items added to inventory (one of each, orb excluded — still lives in the dungeon)
- All items auto-identified at game start
- Glory is always 0; run is always excluded from Hall of Fame

**Glory class modifiers** (additive, applied after difficulty multiplier):
- Knight, Fighter: no bonus
- **Sage, Alchemist, Wizard, Jeweler: +20%**
- **Jones: +30%**

**New constants** (`constants.py`): `DIFF_EXPLORER`, `DIFF_ADVENTURER`, `DIFF_HERO`, `DIFF_ARCHITECT`,
`DIFF_ORDER`, `DIFF_LABEL`, `DIFF_DESC`, `DIFF_GLORY_MULT`, `CLASS_GLORY_BONUS`

**New `GameState` fields**: `difficulty` (str), `_food_acc` (float, fractional food accumulator for Explorer)

**New `save.py` export**: `RESUME_PATH` — path to `dod/resume.dod`

**`engine/hof.py`**: `compute_glory` applies `DIFF_GLORY_MULT` then `CLASS_GLORY_BONUS`; `submit_entry` returns `(entry, None)` for Architect without writing to disk

## v0.308 — Monster Hostility System

### Overview
Every monster now has a hostility disposition that governs its behaviour before, during, and after encounters with the player.

### Hostility States
| State    | Colour dot | Behaviour |
|----------|-----------|-----------|
| HOSTILE  | red (none shown — default) | Chases and attacks on sight (up to 8 tiles) |
| CAUTIOUS | orange | Only engages if player comes within 3 tiles or attacks first |
| NEUTRAL  | green | Ignores the player entirely unless provoked |
| AFRAID   | yellow | Actively flees away from the player |

### Monster Dispositions
- **HOSTILE by default:** Kobold, Orc, Skeleton, Ettin, Zombie, Schwein Hund, Ice Whirlwind, Drackone, Vampire, Dragon, Dark Wizard
- **CAUTIOUS by default:** Giant Bat, Giant Rat, Giant Scorpion, Fire Lizard, Pirboleg, Alligog, Electric Penguin
- **NEUTRAL by default:** Centaur, Sethron, Shambling Mound, The Floor

### Effective Hostility Formula
Computed every turn for each monster:
1. Ring of Monster Attraction → forces HOSTILE (overrides all)
2. fear_turns > 0 → forces AFRAID
3. Charmed → forces NEUTRAL
4. Provoked (player attacked them) → forces HOSTILE
5. Undead / Boss special tags → always HOSTILE (immune to CHA / level adjustments)
6. Base hostility ± CHA modifier ± level-gap modifier (clamped to AFRAID..HOSTILE)

### Charisma Effect
- CHA ≥ 22 → −1 hostility step (monsters are one tier friendlier)
- CHA 9–21 → no modifier
- CHA ≤ 8  → +1 hostility step (monsters are one tier more hostile)

### Level Gap Effect
- Player level 4+ above monster equivalent → −1 hostility step
- Player level 8+ above monster equivalent → −2 hostility steps (many will flee)

### Provocation
Attacking a neutral or cautious monster sets `provoked = True`, permanently flipping it to HOSTILE. A "turns hostile!" message is shown in the log.

### New Items
- **Scroll of Scare Monster** — all visible non-undead/boss monsters gain 20 turns of AFRAID state
- **Scroll of Charm Monster** — all visible non-undead/boss monsters become NEUTRAL for 30 turns; charm breaks on damage

### Updated Items / Wands
- **Wand of Fear** — now grants 20 fear_turns instead of the old `fleeing` flag; immune to undead/bosses
- **Ring of Monster Attraction** — always overrides hostility to HOSTILE for all floor monsters
- **Potion of Charisma** — permanently raises CHA, reducing hostility by one step at CHA ≥ 22

### Visual Indicators
- Non-hostile monsters show a small coloured dot in the bottom-right corner of their tile
- The Stats Panel lists all visible monsters with their hostility state

## v0.309 — Per-Item Unique Sprites

### Overview
Every item in the game now has a unique hand-drawn sprite at 3× internal resolution
(288px) smoothscaled to 96px, matching the Mac greyscale aesthetic of the 1985 original.

### Architecture Change
- `ui/sprites.py` — new `sprite_item_by_id(item_id, glyph, color)` function replaces
  the old glyph-only `sprite_item()`. Falls back to glyph dispatch for any unknown IDs.
- `ui/renderer.py` — item sprite cache key is now `itm_{item.id}` (was `itm_{glyph}_{color}`),
  so each unique item gets its own sprite slot.

### New Sprites (34 unique item drawings + 5 helper bases)

**Weapons** — each has a distinct silhouette:
- Long Sword: long diagonal blade with visible crossguard and round pommel
- Two-Handed Sword: fills most of the tile; wider elongated crossguard, heavier blade
- Dagger: short stubby blade, minimal guard, no pommel
- Leather Whip: thick handle with tapering S-curve lash
- Mace: heavy flanged ball-head with 6 radial spikes, thick handle
- Death Blade: dark serrated sword with skull-style guard
- Sling: Y-shaped thong with central leather cup
- Small Rock / Large Rock: rough stone with surface chips and cracks
- Dart: thin needle with triangular flight fins
- Spear: long shaft, triangular spearhead at tip
- Macintosh Plus: faithful Mac silhouette with screen, drive slot, and face

**Armor** — each reads distinctly at 96px:
- Leather Armor: soft body with plain outlines and skirt
- Chain Armor: diamond chainmail grid pattern
- Banded Armor: horizontal plate bands with strong pauldrons
- Plate Armor: full-plate with central ridge catch-light
- Elven Cloak: flowing cape with clasp gem
- Shield: kite shield with central boss and cross
- Helmet: dome with visor slit and nose guard
- Gloves: two gauntlets side-by-side with finger and knuckle detail

**Potions** — three distinct flask shapes:
- Healing/Life variants: bright wide-body round flask
- Poison/Blindness: dark narrow round flask
- Speed/Levitation/Invisibility: tall thin bottle
- Strength/Muscle: oversized wide flask
- All others: standard round flask

**Scrolls**: rolled parchment cylinder with elliptical end-caps and text lines

**Wands**: thin diagonal rod with sparkle burst at the tip

**Rings**: thick band with gem setting at top; gem brightness varies by type
(dull for cursed rings like Ring of Slowness/Hunger)

**Food**:
- Food Ration (good/bland): bone drumstick with knuckle end
- Food Ration (rotten): same with cracks and dark patches
- Fruit: round apple with stem and leaf
- Spider: 8-legged silhouette with body segments
- Lizard: side-view with head, body, legs, and tail

**Jewels**:
- Diamond: 4-point ◇ with internal facet cross-lines
- Ruby: 8-sided brilliant cut with shaded facets
- Emerald: square emerald-cut with step facets

**Misc**:
- Orb of Carnos: dark mystic orb with inner swirling glow and orbiting sparks
- Plastic Orb: plain bright sphere with simple specular highlight

## v0.401.20260311
- **data/monsters.py** — complete rewrite with all 42 original TDR monsters
  (replaces invented D&D creatures: kobolds, orcs, zombies, etc.)
- Monster stats (XP, HP, AC, Atk, Dmg) extracted from TDR v1.2.3 binary
- Level ranges cross-validated against DoD V4.0 binary, which revealed a
  systematic +1 data-table shift in TDR for monsters #13–28 (Electric Penguin
  through Dark Wizard); corrected ranges applied for those 16 monsters
- Further level ranges confirmed by playtesting to floor 15
- Added `MONSTER_POWER: float = 1.0` — single dial scaling HP, damage, and XP
  simultaneously (0.5 = very easy, 1.0 = authentic, 1.5 = very hard)
- Added `_scale_hp()`, `_scale_dmg()`, `_scale_xp()`, `_hp_dice()`, `_dmg_dice()`
  helper functions; dice values recomputed on import when MONSTER_POWER changes
- Added `icon_id` field (ICON resource IDs 400–443) for future sprite lookup
- Added `weighted_monsters_for_floor()` helper (pool weighted by spawn_freq)
- Dark Wizard confirmed as sole floor 40 boss (Banshee moved to floors 18–23)

## v0.402.20260311
- **engine/game.py** — wandering monster mechanic (original DoD behaviour)
  - Every 10 turns, rolls `10% + floor//2 %` chance to spawn one monster
  - Spawn pool weighted by `spawn_freq` via `weighted_monsters_for_floor()`
  - Monsters placed on open T_FLOOR tiles outside the player's current FOV
  - Hard cap of 5 wandering spawns per floor visit (`WANDER_CAP = 5`)
  - Player hears "You hear something moving in the dark…" on each spawn
  - `turns_on_floor` and `wander_count` reset to 0 on every floor entry
- **assets/sprites/300.png** — new Knight sprite (96×96, black background keyed
  to transparency; cropped from 101×96 source)

## v0.403.20260312
- **assets/sprites/** — player sprites added for all remaining classes;
  procedural fallbacks (sprites 301–306) now replaced with 96×96 RGBA PNGs
  - `300.png` — Knight (re-exported from GIMP XCF source; clean alpha channel
    via ImageMagick XCF decode; proportional crop from 665×630 canvas)
  - `301.png` — Fighter (flood-fill bg removal from preview PNG; UI bar stripped;
    tight crop 542×629 → scaled 82×96, centred on transparent canvas)
  - `302.png` — Sage (495×628 → 75×96)
  - `303.png` — Wizard (571×629 → 87×96; magic orb glow preserved)
  - `304.png` — Alchemist (493×645 → 73×96)
  - `305.png` — Jeweler (484×622 → 74×96; diamond highlight preserved)
  - `306.png` — Jones (489×622 → 75×96)
  - All sprites: grey background (~126,126,126) flood-filled from edges with
    tolerance 22; UI overlay bar detected and stripped before crop; proportional
    resize to fit 96×96 with centred placement on transparent canvas
- **ui/sprites.py** — `_load_player_sprite()` rewritten as per-class loader;
  `CLASS_SPRITE_ID` dict maps each class key to its PNG icon ID (300–306);
  `build_cache()` now populates `player_knight` … `player_jones` cache entries
  instead of a single `"player"` key
- **ui/renderer.py** — both player blit sites updated from
  `sprites.get("player")` to `sprites.get(f"player_{p.class_key}")`
  so every class renders its own sprite in-game

## v0.404.20260314
### Dark Wizard boss — binary-accurate stats, scripted spawn, teleport-escape mechanic

All changes in this version are derived from direct analysis of the TDR v1.2.3
binary (DATA_0.bin), specifically the 22-byte monster record at offset 0xc2a6 and
the CODE_2 boss-handler routine at 0x091b–0x0e00.  The Dark Wizard was the most
inaccurate monster in the previous roster; this version makes him correct.

#### `data/monsters.py`

**Dark Wizard — corrected stats (all from TDR v1.2.3 binary offset 0xc2a6):**

| Field | v0.403 | v0.404 | Source |
|---|---|---|---|
| AC | −2 | **−5** | binary byte `fb` (signed) |
| Attack | 20 | **15** | binary byte `0f` |
| Damage dice | 8d6 | **10d6** | binary byte `24` = 36 flat → 10d6 |
| XP reward | 12,000 | **32,000** | binary word `7d00` |
| HP | rolled 22d8 | **fixed 800** | binary word `0320`; only boss in game with fixed HP |
| `spawn_freq` | 2 | **0** | binary byte `00`; scripted-only, never random |

- Added `"boss_escape"` to Dark Wizard `special` list — drives teleport mechanic
- Added `hp_fixed=800` kwarg — Dark Wizard always spawns at exactly 800 HP
  (scaled by `MONSTER_POWER`); `hp_dice` retained for display/scaling reference

**Banshee — corrected stats (binary offset 0xc29e, cross-validated against DoD V4.0):**

The Banshee and Dark Wizard had their high-value stats effectively swapped in
the previous implementation.  The TDR binary is unambiguous:

| Field | v0.403 | v0.404 | Source |
|---|---|---|---|
| AC | −5 | **+2** | binary byte `02` |
| Attack | 15 | **9** | binary byte `09` |
| Damage dice | 10d6 | **4d6** | binary byte `0e` = 14 flat → 4d6 |
| XP reward | 32,000 | **2,000** | binary word `07d0` |
| base_hp | 32 | **57** | binary word `0039` |

The Banshee is now correctly a dangerous mid-range threat (floors 18–23) rather
than the single most powerful monster in the game.  Its level-drain and scream
abilities remain unchanged.

**`_m()` helper — new `hp_fixed` parameter:**
- Optional kwarg `hp_fixed=None`; when set, stored as
  `round(hp_fixed * MONSTER_POWER)` in the monster dict
- `hp_fixed` takes precedence over `hp_dice` during both initial dungeon
  population and any subsequent `MONSTER_POWER`-driven rescaling

#### `engine/dungeon.py` — scripted floor 40 boss placement

- Dark Wizard is now placed by a dedicated scripted block in `_populate()`,
  executed *before* the normal `monsters_for_floor()` eligibility check
  (which correctly returns empty for floor 40, since `spawn_freq = 0`)
- Boss tile chosen as the floor tile with the greatest Manhattan distance from
  `lv.stair_up` (player entry point), matching the original game's layout
- HP set from `hp_fixed` (800) rather than rolled dice
- `boss_escapes: 0` initialised in the spawn dict for save-file persistence
- Normal random monster pool still runs after boss placement on any floor
  where `monsters_for_floor()` returns results; floor 40 gets only the Wizard
- `tile_cur` (item-spawn offset) now derived from `len(lv.monster_spawns)`
  rather than a local `n_mon` variable — fixes `UnboundLocalError` on
  floors where the random pool is empty

#### `engine/game.py` — boss teleport-escape mechanic

The original TDR CODE_2 routine (0x0d70–0x0dba) implements a non-death escape
path for the Wizard: when his HP reaches zero he teleports rather than dying,
logging "The Wizard disappeared! You hear a laugh and he is gone!" (DATA_0 offset
0x091b).  The third lethal hit is fatal and drops the Orb.

- **`_player_attacks()`** — after `monster.take_damage()` resolves to `is_dead()`,
  checks for `"boss_escape"` in `monster.special` and `monster.boss_escapes < 2`;
  calls `_boss_escape()` instead of `_kill_monster()` when both are true
- **`_boss_escape()`** (new method):
  - Collects open `T_FLOOR` tiles outside the player's current FOV
  - Teleports the Wizard to a randomly chosen candidate tile
  - Increments `monster.boss_escapes`
  - Restores HP to 25% of `max_hp` so the fight continues
  - Revives `monster.alive = True` (take_damage set it False)
  - Logs verbatim TDR message in purple `(180, 100, 255)`
- **`_kill_monster()`** — on kill of a `"boss"` monster:
  - Spawns `orb_of_carnos` Item directly onto the Wizard's tile
  - Logs "The Orb of Carnos falls from the Wizard's grasp!" in gold
  - Logs "Your journey back to the surface will be easy now." in gold
  - Returns early (no random loot roll on boss kills)
- **`_save_floor_state()`** — `boss_escapes` included in each monster spawn dict
- **`_spawn_entities()`** — `boss_escapes` restored from spawn dict on floor load
  (defaults to 0 for saves predating v0.404)

#### `entities/monster.py`
- Added `self.boss_escapes: int = 0` instance field

#### `constants.py`
- Version bumped to `0.404.20260314`

## v0.405.20260314
### Monster special abilities — full implementation

All 13 special tags defined in `data/monsters.py` are now implemented.
Previously only `boss`, `boss_escape`, and the item-side `confuse` effect
(Potion of Confusion) were wired up.  This version connects every tag to
live game logic.

#### `entities/player.py`

- **`drain_level()`** (new method) — Banshee level drain: decrements `level`,
  recalculates `xp_next` backwards one geometric step, clamps `xp`, removes
  the HP that level granted (`max(1, 4 + CON mod)`). Returns `False` at
  level 1 (cannot drain below 1). Death can result if HP falls to 0.

- **`stunned: bool`** (new field) — set by `head_smash` (Reaper) and `scream`
  (Banshee). Consuming a turn in `try_move()` while stunned skips the action.
  Tracked via `status_turns["stunned"]` and decremented by `tick_statuses()`
  like all other timed effects.

- **`slowed: bool`** (new field) — set by `cold_aura` contact (Ice Whirlwind,
  Drackone). Causes every other movement step to be skipped, identical to
  encumbrance penalty. Cleared automatically when `status_turns["slowed"]`
  expires.

- **`status_summary()`** — added `STUNNED` and `SLOWED` entries.

#### `engine/save.py`

- `stunned` and `slowed` added to `_player_to_dict()` and `_player_from_dict()`.
  Both default to `False` on load from saves predating v0.405.

#### `engine/effects.py` — `fire_wand_at_direction()`

- **`immune_fire`** check: `wand_fire` deals 0 damage to Caveman, Black Unicorn,
  and Dark Wizard. Log message: *"[name] absorbs the blast!"*
- **`immune_cold`** check: `wand_ice` deals 0 damage to Ice Whirlwind and Drackone.
- Both are handled per-target inside the hit loop so multi-target piercing
  shots can hit a mix of immune and non-immune monsters in one beam.

#### `engine/game.py`

**`try_move()` additions:**

- **Stunned check** — if `p.stunned`, consume the turn silently (monsters still
  act), decrement `status_turns["stunned"]`, log *"You are stunned and cannot
  act!"* Stun clears on expiry with *"You shake off the stun."*
- **Confused movement** — if `p.confused`, 50% chance each move to replace
  `(dx, dy)` with a random 8-directional vector before computing `(nx, ny)`.
  Logs *"You stumble in confusion!"* when triggered.
- **Cold-slow movement** — if `p.slowed` (from cold aura), every other movement
  attempt is skipped, same mechanic as encumbrance. Logs *"You move sluggishly
  in the cold."*

**`_monster_attacks()` and `_apply_monster_on_hit()` (new method):**

Called after every successful melee hit. Iterates `monster.special` and
applies each relevant tag:

| Tag | Effect |
|---|---|
| `confuse` | Sets `p.confused = True`, 20 turns. Wandering Eye, Witch. |
| `stat_drain` | Randomly selects one of 6 stats and decrements it by 1 (minimum 1). CON drain also reduces `max_hp`. Amadon. |
| `level_drain` | Calls `p.drain_level()`. Logs level reduction. Can kill. Banshee. |
| `head_smash` | 40% chance to set `p.stunned` for 2 turns. If helmet equipped, logs save message instead of stun message. Reaper. |
| `acid_splash` | Deals 1d4 extra acid damage to player. Also damages all monsters adjacent to the Black Pudding. Black Pudding. |

**`_run_monster_turns()` additions:**

- **`cold_aura`** — checked before the monster's action. If player is adjacent
  (Manhattan dist ≤ 1) and not `resist_cold`: deals 1d4 cold damage, applies
  `slowed` for 2–4 turns. Resist Cold absorbs entirely. Ice Whirlwind, Drackone.

- **`fire_breath`** — checked before `think()` when player is 2–6 tiles away
  and in unobstructed LOS (DDA ray check). Takes the monster's full action;
  `continue` skips the normal melee `think()` for that turn. Calls
  `_monster_fire_breath()`. Fire Lizard, Evil Cleric, Dark Wizard.

- **`necromancy`** — increments a per-monster `_necro_timer`; every 15 turns
  calls `_necromancer_raise()`. Evil Necromancer.

- **`scream`** — checked after a successful melee hit. 30% chance to call
  `_banshee_scream()`. Banshee.

**New helper methods:**

- **`_monster_fire_breath(monster)`** — rolls 2d8 fire damage. If `p.resist_fire`:
  logs absorption, no damage. Otherwise applies damage directly (bypasses AC).
  Death cause set to *"Incinerated by [name]"*.

- **`_banshee_scream(banshee)`** — stuns player for 2 turns if within 3 tiles.
  Also forces `sleeping = 2` on any other monsters within 3 tiles (they're
  deafened too). Logs *"The Banshee screams! The sound stuns you!"*

- **`_necromancer_raise(necromancer)`** — scans 5×5 area around the necromancer
  for open, unoccupied floor tiles. Spawns a Sethron or Alligog (random) with
  full rolled HP, `provoked = True`. Logs *"The [name] raises the dead!"*

## v0.406.20260318
### Gate Keeper barrier system + "The Floor" monster corrections + monster sprite engine

#### Binary research basis
All Gate Keeper mechanics derived from TDR v1.2.3 binary analysis:
- DATA_0 monster record at offset 0xc33a: XP=15000, HP=1 (placeholder),
  spawn_freq=0, boss flag (b12=5)
- CODE_5 @ 0x3050: jump table with 11 cases assigning HP min/max ranges
  per dungeon section (confirmed via BSR args #50/#57 seen at CODE_4 @ 0x06e0)
- CODE_5 @ 0x3024: CLR.B clears gate_keeper_defeated flag per section
- DATA_0 strings 0x11a2 / 0x11da / 0x0abe / 0x0ad3: verbatim messages used

#### `constants.py`
- `VERSION` bumped to `0.406.20260318`
- `GK_BARRIER_FLOORS = [5, 10, 15, 20, 25, 30, 35]`
- `GK_HP_TABLE`: per-barrier HP ranges from CODE_5 jump table
- `GK_AC_TABLE`: AC scaling per barrier (4 down to −3)
- `GK_ATK_TABLE`: (atk, dmg_min, dmg_max) scaling per barrier

#### `data/monsters.py`
- **Gate Keeper** corrected: `spawn_freq=0` (never random), `xp=15000`
  (confirmed from binary), `special=["gate_keeper"]` (new tag), placeholder
  stats (hp=1, ac=1, atk=1, dmg=1) — all overridden at spawn time.
  `min_floor=5, max_floor=35` (present on all barrier floors).
- **`floor_a`** added (TDR monster index 41, icon 441): "The Floor",
  floors 18–20, HP 70, AC 1, XP 3000, `spawn_freq=5`,
  `base_hostility=HOSTILITY_NEUTRAL` — camouflaged until provoked.
- **`floor_b`** added (TDR monster index 42, icon 442): "The Floor",
  floors 26–28, HP 85, AC 0, XP 4000, `spawn_freq=5`,
  `base_hostility=HOSTILITY_NEUTRAL`.
- `LEGACY_ID_MAP`: `the_floor → floor_a` (was `wandering_eye`).

#### `engine/game.py`
- `GameState.gk_sections_cleared: set` — tracks which barrier floors have
  been cleared this run. Initialised empty on `start_new_game()`.
- `_maybe_spawn_gate_keeper()` — called from `_enter_floor()`. Places one
  Gate Keeper adjacent to `stair_down` with section-appropriate HP/AC/dmg.
  No-ops if section cleared, GK already present, or no stair_down.
- `_gk_blocks_descent(next_floor)` — returns True when next_floor is a
  barrier and a live Gate Keeper exists on the current floor.
- `_nearest_barrier_below()` — finds the relevant barrier for the current floor.
- `try_move()` T_STAIR_DOWN: checks `_gk_blocks_descent()`; if blocked,
  logs verbatim TDR strings and consumes a turn without descending.
- `_kill_monster()`: `"gate_keeper"` tag adds barrier to
  `gk_sections_cleared`, logs verbatim TDR congratulations strings, returns
  early (no loot).
- `_save_floor_state()` / `_spawn_entities()`: GK's runtime AC and dmg stats
  persisted in spawn dict under `gk_ac`, `gk_dmg_min`, `gk_dmg_max`.

#### `engine/save.py`
- `gk_sections_cleared` saved as a JSON list; loaded back as a set.
  Defaults to empty set for saves predating v0.406.

#### `ui/sprites.py` (from v0.405 manual changes)
- New `get_monster_sprite(monster_id)` loader: checks `assets/sprites/` for
  a PNG named after the monster's `icon_id` (e.g. `401.png`); scales
  proportionally and centres on transparent 96×96 canvas if not square;
  falls back to procedural Mac-style silhouette if file absent.
- `build_cache()` pre-loads all 42 monsters from the MONSTERS roster at
  startup using `monster_{id}` cache keys (e.g. `monster_ice_whirlwind`).
- `sys.path` injection at top of file resolves `ModuleNotFoundError` for
  cross-directory imports of `data/` from the `ui/` subfolder.

#### `ui/renderer.py` (from v0.405 manual changes)
- `_draw_dungeon()` now blits `sprites.get(f"monster_{mon.id}")` for each
  visible monster instead of dynamic shape drawing; HP bar and hostility dot
  overlays preserved.

#### `assets/sprites/` — monster sprites 401–417
- 17 monster PNG sprites added (96×96 RGBA), covering icon IDs 401–417:
  Sethron (401) through Witch (417).

## v0.407.20260319
### Item sprite framework — PNG asset pipeline for all 82 items

#### Design
Mirrors the player-class (v0.403) and monster (v0.405/406) sprite systems.
Each item resolves to a PNG icon ID at cache-build time; categories that
share art (potions, scrolls, rings, wands, gems, food) all map to the same
icon file so a single PNG drives all variants. Items with unique visuals
(weapons, armor, throwables, orbs) each get their own icon ID.

#### Icon ID allocation (500-series, `assets/sprites/`)
| ID range | Contents |
|----------|----------|
| 500–511  | Weapons & throwables — one unique ID per item |
| 512–519  | Armor pieces — one unique ID per item |
| 520      | All potions (17 items share one PNG) |
| 521      | All scrolls (16 items share one PNG) |
| 522      | All rings (7 items share one PNG) |
| 523      | All wands (11 items share one PNG) |
| 524      | All gems / jewels (3 items share one PNG) |
| 525      | All food (6 items share one PNG) |
| 526      | Orb of Carnos (unique) |
| 527      | Plastic Orb (unique) |

To add art: drop a `{icon_id}.png` file into `assets/sprites/`. Non-96×96
images are proportionally scaled and centred on a transparent canvas
automatically. Missing files fall back to the existing procedural drawings.

#### `ui/sprites.py`
- `ITEM_SPRITE_ID: dict` — maps all 82 item IDs to their icon numbers.
  Shared-category items (e.g. every `potion_*`) point to the same icon ID.
- `_load_item_sprite(item_id)` — load chain identical to `get_monster_sprite()`:
  resolve `ITEM_SPRITE_ID[item_id]` → try `assets/sprites/{icon_id}.png` →
  proportional scale + centre on transparent 96×96 canvas → fall back to
  `sprite_item_by_id()` procedural if PNG absent or corrupt.
- `build_cache()` — now pre-loads all 82 items at startup as `itm_{item_id}`
  cache entries. Shared-category items each get their own key but resolve to
  the same Surface object (loaded once, reused). Cache startup log updated to
  report item count alongside monsters and classes.

#### `ui/renderer.py`
- Item blit path updated: lazy `sprite_item_by_id()` call replaced by
  `sprites._load_item_sprite()` fallback for any item not found in the
  pre-built cache (handles modded saves / future items added at runtime).

#### `constants.py`
- `VERSION` bumped to `0.407.20260319`.

## v0.408.20260324
### Combat rebalance — monster threat, XP pacing, and difficulty tuning

#### Design rationale
Playtesting showed three compounding imbalances: starvation killed runs before
combat became relevant; monsters posed no threat due to a missing hit-roll
system; XP gain was so fast that players out-levelled floors trivially. This
version addresses the combat and XP sides. Food spawn is addressed separately.

#### `data/monsters.py` — three-dial power system
- `MONSTER_POWER` (single legacy dial) replaced by three independent constants:
  - `MONSTER_HP_POWER  = 2.5` — monsters have 2.5× TDR base HP; much harder to
    kill, requiring resource management and tactical retreats.
  - `MONSTER_DMG_POWER = 1.3` — 30% more damage per hit than authentic TDR,
    making each successful hit meaningfully dangerous.
  - `MONSTER_XP_POWER  = 0.4` — monsters yield 40% of TDR authentic XP,
    targeting ~1 XP level gained per dungeon level for a focused run.
- `MONSTER_POWER = 1.0` retained as legacy alias so any external reference
  compiles without error.
- `_scale_hp()`, `_scale_dmg()`, `_scale_xp()` updated to use their respective
  dedicated multiplier.
- `hp_fixed` scaling in `_m()` updated to use `MONSTER_HP_POWER` (affects
  Dark Wizard fixed HP).

#### `entities/monster.py`
- `self.atk` now stored on Monster instance from `data["atk"]`. Previously the
  `atk` field existed in the data dict but was never applied anywhere in combat
  — meaning monsters had no hit-chance system at all.

#### `engine/game.py` — `_monster_attacks()` rewritten
**Bug fixed:** the original implementation rolled damage and subtracted player
AC directly (`max(0, dmg - max(0, 10 - AC))`). With good armor, mitigation
exceeded damage roll → 0 damage every hit → effective immunity. This was not
a miss system; it was silent damage cancellation with no feedback.

New hit-roll system:
- Roll `1d20`; monster hits if `roll ≤ clamp(atk + player.AC - 10, 1, 20)`.
- AC still matters (better armor raises the hit threshold), but can never reduce
  hit chance below 5% (threshold min = 1) — armor is now evasion, not immunity.
- On a successful hit: `max(1, randint(dmg_min, dmg_max))` — guaranteed 1 HP
  minimum damage. No monster that lands a blow can deal 0 damage.
- On a miss: log "The X misses you." and return immediately (no specials fire).
- Special on-hit abilities now trigger unconditionally on any hit (previously
  gated on `actual > 0`, which was always False for armored players).

Example hit thresholds with `atk=9` (typical floor 5–10 monster):
| Player AC | Threshold | Hit chance |
|-----------|-----------|------------|
| 10 (bare) | 9         | 45%        |
| 8 (leather)| 7        | 35%        |
| 6 (chain) | 5         | 25%        |
| 4 (banded)| 3         | 15%        |
| 2 (plate) | 1         | 5% (min)   |

- Gate Keeper: `gk_atk` now persisted in `_save_floor_state()` and restored in
  `_spawn_entities()`. `_maybe_spawn_gate_keeper()` sets `gk.atk` from
  `GK_ATK_TABLE`.

#### `constants.py`
- `XP_BASE` raised from `10` to `200`. At the old value a single floor-1
  monster kill (20 XP) blew through levels 1→2→3 simultaneously. At 200,
  reaching level 2 requires clearing ~20 floor-1 monsters; level 3 requires
  a full floor 2 grind. Combined with `MONSTER_XP_POWER=0.4` this targets
  ~1 XP level per dungeon level for a moderate-grind run.
- `XP_GROWTH` raised from `1.7` to `2.0`. At ×2.0 each level requires exactly
  double the XP of the previous. This naturally slows progression to 1 level
  per 2 floors in mid-game, encouraging exploration over speedrunning.
- `VERSION` bumped to `0.408.20260324`.

## v0.409.20260324
### Bug fixes, UI polish, identification overhaul, hostility rebalance

#### Bug fixes
- **Pause bug** (`main.py`): movement and all action keys were processed even
  when the timer was paused. `_handle_playing()` now returns immediately when
  `game.paused` is True; only Space (toggle pause) is allowed through. Mouse-
  held auto-movement also blocked while paused.

#### Character creation
- **Auto-focus name field** (`main.py`, `ui/screens.py`): clicking a class row
  or pressing Up/Down to change class now immediately moves cursor focus to the
  name input field, so the player can type their name without an extra click.

#### Title screen
- **Illustration added** (`ui/screens.py`): the "[ Game Illustration ]"
  placeholder is replaced by `assets/sprites/title_bg.png`. Image is scaled
  to cover-fill the 680×440 art box with centre-crop. Falls back to the
  placeholder box gracefully if the file is missing.
- Asset file: `assets/sprites/title_bg.png` (1376×768 RGBA, scaled at runtime).

#### Identification system overhaul (`engine/game.py`)
- **Starting kit fully identified**: carry items that match the class expert
  category (Sage's scrolls, Wizard's wands, Alchemist's potions, Jeweler's
  ring) are added to `game.identified` at game start and flagged
  `identified=True` / `enchant_known=True`.
- **`_apply_expert_identify()`** replaces `_apply_fuzzy_enchant()`:
  - Covers all expert categories (not just wearables).
  - Accuracy = `clamp(50 + (stat − 10) × 3, 65, 95)%` where stat is DEX
    (Knight/Fighter), WIS (Jeweler), or INT (Sage/Wizard/Alchemist).
  - **Correct ID**: item added to `game.identified` immediately; name shown
    without `?`.
  - **Wrong ID**: a random valid item name from the same category stored as
    `fuzzy_name`; `pending_confirm=True` appended to name as `"Name?"`.
  - **Confirmation on use**: when a `pending_confirm` consumable is used,
    `pending_confirm` is cleared, true `item_id` added to `identified`, and
    a "You now know this was a X!" message is logged.
- `item_display_name()` updated to render `"Name?"` for pending-confirm items.

#### Monster hostility & AI (`data/monsters.py`, `entities/monster.py`)
- All `base_hostility=HOSTILITY_CAUTIOUS` entries promoted to
  `HOSTILITY_HOSTILE`. Only The Floor (NEUTRAL ambush monster) and Gate Keeper
  retain their original hostility — all other monsters are now aggressive on
  sight.
- Hostile chase range extended from **8** to **15** tiles.
- Cautious attack range extended from **3** to **5** tiles.
- **Hostility indicator dot removed** (`ui/renderer.py`): the coloured dot
  overlay on monster tiles has been removed. All monsters behave uniformly
  hostile; the visual indicator is no longer meaningful.

#### Stair sprites (`ui/sprites.py`)
- `STAIR_UP_SPRITE_ID   = 550`
- `STAIR_DOWN_SPRITE_ID = 551`
- `_load_stair_sprite(icon_id, fallback_fn)`: same PNG pipeline as monsters
  and items — proportional scale + centre-crop to 96×96; falls back to
  procedural tile if file absent.
- `build_cache()` now calls `_load_stair_sprite()` for both stair cache
  entries. To add custom art: drop `550.png` (stair up) or `551.png`
  (stair down) into `assets/sprites/`.

#### `constants.py`
- `VERSION` bumped to `0.409.20260324`.

## v0.410.20260325
### Mouse-pause bug fix + full tile sprite pipeline

#### Bug fix
- **Mouse click movement during pause** (`main.py`): viewport click-to-move
  was not blocked by `game.paused`. The `MOUSEBUTTONDOWN` handler now checks
  `not game.paused` before allowing any viewport movement click, matching the
  existing keyboard and mouse-hold guards.

#### Tile sprite pipeline (`ui/sprites.py`)
All dungeon tile types now support custom PNG art via the same drop-in
mechanism as monsters, items, players, and stairs. Place a **96×96 px PNG**
in `assets/sprites/` named by icon ID to override the procedural tile.

| ID  | File        | Tile                              | Px size  |
|-----|-------------|-----------------------------------|----------|
| 550 | `550.png`   | Staircase up   (T_STAIR_UP)       | 96×96    |
| 551 | `551.png`   | Staircase down (T_STAIR_DOWN)     | 96×96    |
| 560 | `560.png`   | Stone wall     (T_WALL)           | 96×96    |
| 561 | `561.png`   | Floor — light square (checkerboard even) | 96×96 |
| 562 | `562.png`   | Floor — grey square  (checkerboard odd)  | 96×96 |
| 563 | `563.png`   | Boulder        (T_BOULDER)        | 96×96    |

**Notes on floor tiles:** The game renders floors as a checkerboard of two
alternating tile types for visual texture. `561.png` covers the lighter
squares; `562.png` covers the darker squares. If you want a uniform floor,
supply identical images for both IDs.

**Dim variants** (tiles in explored-but-not-currently-visible areas) are
derived automatically: the lit PNG is darkened to 55% brightness at runtime.
No separate dim PNG is required.

**Size:** All tiles must be 96×96 px. If a different-size image is supplied
it will be scaled to 96×96; for best quality, author at exactly 96×96 px.

**Fallback:** If a PNG is absent or unreadable, the procedural tile is used
transparently with no error.

`_load_tile_sprite(icon_id, fallback_fn, dim, dim_factor)` replaces the
previous `_load_stair_sprite()` helper. The old stair loader is subsumed —
all tile types now use the unified function.

#### `constants.py`
- `VERSION` bumped to `0.410.20260325`.
