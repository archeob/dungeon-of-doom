# engine/effects.py — Item effect resolver v0.109
#
# apply_effect(game, item_dict) → (message, color)
# apply_wand(game, item_dict)   → (message, color)   targets nearest visible monster
#
# Effects are resolved from item_dict["effect"] tags defined in data/items.py.

from constants import (C_HP_FULL, C_HP_LOW, C_GOLD, C_XP, C_WHITE,
                       C_LTEXT, C_LTEXT_DIM, C_LTEXT_ACCENT,
                       S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA,
                       T_FLOOR, T_WALL, T_BOULDER, PASSABLE,
                       MAP_COLS, MAP_ROWS, STAT_MAX)


def apply_effect(game, item: dict) -> tuple:
    """Apply a consumable item's effect. Returns (message_str, color_tuple)."""
    p   = game.player
    eff = item.get("effect", "nothing")
    msg = item.get("message", "Nothing happens.")
    col = C_LTEXT

    # ── Food ─────────────────────────────────────────────────────────────────
    if eff == "eat":
        fv = item.get("food_val", 0)
        if item.get("poisonous") and fv == 0:
            p.poisoned = True
            p.status_turns["poisoned"] = 15
            col = C_HP_LOW
        else:
            warning = p.eat(fv)
            if warning:
                msg = warning; col = C_HP_LOW

    # ── Healing potions ───────────────────────────────────────────────────────
    elif eff == "heal":
        healed = p.heal(item.get("power", 8))
        if healed == 0: msg = "You are already at full health."
    elif eff == "heal_major":
        healed = p.heal(item.get("power", 30))
        if healed == 0: msg = "You are already at full health."
    elif eff == "life_restore":
        p.hp = p.max_hp   # restore to current max (drained HP)

    # ── Stat boosts (permanent) ───────────────────────────────────────────────
    elif eff == "str_up":
        p.modify_stat(S_STR, item.get("power", 1)); col = C_HP_FULL
    elif eff == "dex_up":
        p.modify_stat(S_DEX, item.get("power", 1)); col = C_HP_FULL
    elif eff == "con_up":
        p.modify_stat(S_CON, item.get("power", 1)); col = C_HP_FULL
    elif eff == "cha_up":
        p.modify_stat(S_CHA, item.get("power", 1)); col = C_HP_FULL
    elif eff == "int_up":
        p.modify_stat(S_INT, item.get("power", 1)); col = C_HP_FULL
    elif eff == "wis_up":
        p.modify_stat(S_WIS, item.get("power", 1)); col = C_HP_FULL
    elif eff == "str_restore":
        # Restore STR to its class base (not tracked yet; just boost to 10 min)
        if p.stats[S_STR] < 10:
            p.stats[S_STR] = 10
        col = C_HP_FULL

    # ── Status effects (temporary) ────────────────────────────────────────────
    elif eff == "confuse":
        p.confused = True
        p.status_turns["confused"] = item.get("power", 20); col = C_HP_LOW
    elif eff == "blind":
        p.blinded  = True
        p.status_turns["blinded"]  = item.get("power", 20); col = C_HP_LOW
    elif eff == "haste":
        p.hasted   = True
        p.status_turns["hasted"]   = item.get("power", 30); col = C_HP_FULL
    elif eff == "invisible":
        p.invisible = True
        p.status_turns["invisible"] = item.get("power", 30)
    elif eff == "levitate":
        p.levitating = True
        p.status_turns["levitating"] = item.get("power", 25); col = C_LTEXT_DIM
    elif eff == "resist_fire":
        p.resist_fire = True
        p.status_turns["resist_fire"] = item.get("power", 40)
    elif eff == "resist_cold":
        p.resist_cold = True
        p.status_turns["resist_cold"] = item.get("power", 40)
    elif eff == "protect":
        p.protected = True
        p.status_turns["protected"] = item.get("power", 20); col = C_HP_FULL
    elif eff == "poison_drink":
        p.poisoned = True
        p.status_turns["poisoned"] = item.get("power", 20)
        p.modify_stat(S_STR, -2); col = C_HP_LOW

    # ── Scroll effects ────────────────────────────────────────────────────────
    elif eff == "gain_level":
        p._level_up(); col = C_XP
    elif eff == "identify":
        # Flag for 4 identify uses; open inventory immediately for selection
        game.pending_identify = 4
        from engine.game import PHASE_INVENTORY
        game.phase = PHASE_INVENTORY
        col = C_LTEXT_ACCENT
    elif eff == "enchant_weapon":
        wpn = p.equipped.get("weapon")
        if wpn:
            me = wpn.get("max_enchant", 4)
            if wpn.get("enchant", 0) < me:
                wpn["enchant"] = wpn.get("enchant", 0) + 1
                msg = f"Your {wpn['name']} glows!"; col = C_HP_FULL
            else:
                msg = "Your weapon is already at maximum enchantment."
        else:
            msg = "You have no weapon equipped."
    elif eff == "enchant_armor":
        # Cycle through slots in priority order; enchant the first upgradeable piece
        _ENCHANT_ARMOR_ORDER = ["armor", "helmet", "gauntlets", "offhand", "cloak"]
        arm = None
        for _slot in _ENCHANT_ARMOR_ORDER:
            _candidate = p.equipped.get(_slot)
            if _candidate and _candidate.get("cat") == "armor":
                if _candidate.get("enchant", 0) < _candidate.get("max_enchant", 4):
                    arm = _candidate
                    break
        if arm:
            arm["enchant"] = arm.get("enchant", 0) + 1
            msg = f"Your {arm['name']} glows!"; col = C_HP_FULL
        else:
            msg = "All your armor is already fully enchanted."
    elif eff == "map_floor":
        _reveal_floor(game); col = C_LTEXT_ACCENT
    elif eff == "teleport":
        _teleport_player(game); col = C_LTEXT_ACCENT
    elif eff == "remove_curse":
        from engine.audio import get_audio
        get_audio().play("remove_curse")
        _remove_curse(p); col = C_HP_FULL
    elif eff == "amnesia":
        game._reshuffle_id_map(); col = C_HP_LOW
    elif eff == "wish":
        # Open the wish-entry popup; actual grant happens via resolve_wish()
        if getattr(game, "wish_uses", 0) >= 3:
            msg = "The scroll crumbles — you have used all three wishes."; col = C_HP_LOW
        else:
            game.wish_input = ""
            from engine.game import PHASE_WISH
            game.phase = PHASE_WISH
            msg = "Wish for an object!"; col = C_XP
    elif eff == "scare_monsters":
        # Frighten every monster currently in the player's FOV
        count = 0
        fear_turns = item.get("power", 20)
        for m in game._floor_monsters():
            if (m.x, m.y) in game.fov.visible:
                # Undead and bosses are immune to fear
                if not any(t in m.special for t in ("undead", "boss")):
                    m.fear_turns = fear_turns
                    m.charmed    = False
                    count += 1
        if count:
            msg = f"{count} monster{'s' if count > 1 else ''} cower in terror!"; col = C_LTEXT_ACCENT
        else:
            msg = "No nearby monsters are affected."; col = C_LTEXT_DIM

    elif eff == "charm_monsters":
        # Pacify every monster in the player's FOV (not undead/boss)
        count = 0
        charm_turns = item.get("power", 30)
        for m in game._floor_monsters():
            if (m.x, m.y) in game.fov.visible:
                if not any(t in m.special for t in ("undead", "boss")):
                    m.charmed      = True
                    m.provoked     = False
                    m.fear_turns   = 0
                    m._charm_turns = charm_turns
                    count += 1
        if count:
            msg = f"{count} monster{'s' if count > 1 else ''} become{'s' if count==1 else ''} friendly."; col = C_LTEXT_ACCENT
        else:
            msg = "No nearby monsters are affected."; col = C_LTEXT_DIM
        col = C_LTEXT_DIM

    # ── Wand effects (self-targeted or nearest monster) ───────────────────────
    elif eff.startswith("wand_"):
        return apply_wand(game, item)

    # Identify the item after use (for potions/scrolls)
    _auto_identify(game, item)

    return msg, col


# ── Wand ray colours (used by renderer for animation) ─────────────────────────
WAND_RAY_COLORS = {
    "wand_lightning":   (255, 255, 120),
    "wand_fire":        (255, 140,  30),
    "wand_ice":         (100, 200, 255),
    "wand_death":       (180,  60, 220),
    "wand_striking":    (255, 255, 255),
    "wand_fear":        (200, 200,  60),
    "wand_sleep":       (160, 160, 255),
    "wand_teleport":    ( 60, 220, 120),
    "wand_polymorph":   (220,  60, 200),
    "wand_invisibility":(180, 180, 180),
    "wand_digging":     (180, 130,  70),
}
WAND_RAY_TICKS = 28    # animation length in frames (~0.47s at 60fps)


# Wand effects whose rays pierce through monsters (hit all in path)
_PIERCING_WANDS = {"wand_lightning", "wand_fire", "wand_ice"}


def _wand_ray_tiles(game, px, py, dx, dy, max_range=14, piercing=False):
    """Step from (px,py) in (dx,dy) until wall/edge. Returns list of (wx,wy).
    If piercing=True the ray passes through monsters and hits all in path."""
    tiles = []
    cx, cy = px + dx, py + dy
    for _ in range(max_range):
        if not (0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS):
            break
        if not game.level.is_passable(cx, cy):
            break          # ray always stops at walls
        tiles.append((cx, cy))
        if not piercing and game._monster_at(cx, cy):
            break          # non-piercing ray stops at first monster
        cx += dx; cy += dy
    return tiles


def fire_wand_at_direction(game, item: dict, dx: int, dy: int) -> tuple:
    """Fire a wand in direction (dx, dy) with WIS-based accuracy.
    Sets game.ray_anim for the renderer.  Returns (message, color)."""
    from constants import S_WIS
    p   = game.player
    eff = item.get("effect", "")
    col = C_LTEXT

    if item.get("charges", 0) <= 0:
        return "The wand is empty.", C_HP_LOW

    item["charges"] -= 1

    # ── Accuracy check (WIS-based, stat range 1–25) ───────────────────────
    # Wand of Digging is always accurate — it targets walls, never creatures.
    # All other wands use WIS-based accuracy: WIS 1→30%, WIS 25→98%.
    if eff == "wand_digging":
        accurate    = True
        fire_dx, fire_dy = dx, dy
    else:
        wis      = p.stats[S_WIS]
        hit_pct  = max(30, min(98, round(30 + (wis - 1) * 68 / (STAT_MAX - 1))))
        accurate = (game.rng.randint(1, 100) <= hit_pct)
        fire_dx, fire_dy = dx, dy
        if not accurate:
            # Deflect 45° left or right
            dirs = [(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
            i = dirs.index((dx, dy)) if (dx, dy) in dirs else 0
            fire_dx, fire_dy = dirs[(i + game.rng.choice([-1, 1])) % 8]

    # ── Compute ray ────────────────────────────────────────────────────────
    piercing  = eff in _PIERCING_WANDS
    ray_tiles = _wand_ray_tiles(game, p.x, p.y, fire_dx, fire_dy, piercing=piercing)

    # Collect all monsters along the ray (piercing: all; non-piercing: last only)
    targets = [game._monster_at(wx, wy) for wx, wy in ray_tiles
               if game._monster_at(wx, wy)]
    target  = targets[-1] if targets else None   # kept for single-target branches

    # ── Set animation state ────────────────────────────────────────────────
    ray_col = WAND_RAY_COLORS.get(eff, (255, 255, 255))
    game.ray_anim = {
        "tiles":       ray_tiles,
        "color":       ray_col,
        "start_tick":  None,      # set by renderer on first draw
        "total_ticks": WAND_RAY_TICKS,
        "hit":         target is not None,
    }

    msg = item.get("message", "The wand fires!")

    # ── Apply effect ───────────────────────────────────────────────────────
    if not accurate and not target:
        msg = "The beam goes wide!"
        col = C_LTEXT_DIM

    elif eff in ("wand_lightning","wand_fire","wand_ice","wand_striking","wand_death"):
        if not targets:
            msg = "The beam hits nothing." if accurate else "The beam goes wide!"
            col = C_LTEXT_DIM
        else:
            dmg      = item.get("dmg", 4)
            slain    = []
            hit_names = []
            immune_names = []
            for t in targets:
                # Elemental immunity checks
                absorbed = False
                if eff == "wand_fire"  and "immune_fire" in t.special:
                    absorbed = True
                    immune_names.append(t.name)
                elif eff == "wand_ice" and "immune_cold" in t.special:
                    absorbed = True
                    immune_names.append(t.name)
                if not absorbed:
                    t.take_damage(dmg)
                    hit_names.append(t.name)
                    if t.is_dead():
                        game._kill_monster(t)
                        slain.append(t.name)
            base_msg = item.get("message", "The wand fires!")
            if len(hit_names) > 1:
                names_str = ", ".join(hit_names)
                msg = f"{base_msg}  Hits: {names_str}."
            else:
                msg = base_msg if hit_names else "The blast is absorbed."
            if immune_names:
                msg += "  " + ", ".join(immune_names) + (" absorbs" if len(immune_names)==1 else " absorb") + " the blast!"
            if slain:
                msg += "  Slain: " + ", ".join(slain) + "!"
            col = C_HP_LOW if hit_names else C_LTEXT_DIM

    elif eff == "wand_fear":
        if target:
            # Undead and bosses are immune to fear
            if any(t in target.special for t in ("undead", "boss")):
                msg = f"The {target.name} is unaffected!"; col = C_LTEXT_DIM
            else:
                target.fear_turns = 20
                target.charmed    = False
                msg = f"The {target.name} is terrified!"; col = C_LTEXT_ACCENT
        else:
            msg = "The beam dissipates."; col = C_LTEXT_DIM

    elif eff == "wand_sleep":
        if target:
            target.sleeping = 15
            msg = f"The {target.name} falls asleep!"; col = C_LTEXT_ACCENT
        else:
            msg = "The beam dissipates."; col = C_LTEXT_DIM

    elif eff == "wand_teleport":
        if target:
            tiles = [t for t in game.level.floor_tiles()
                     if abs(t[0]-target.x)+abs(t[1]-target.y) > 5]
            if not tiles:
                tiles = list(game.level.floor_tiles())
            if tiles:
                nx, ny = game.rng.choice(tiles)
                target.x, target.y = nx, ny
            msg = f"The {target.name} vanishes!"; col = C_LTEXT_ACCENT
        else:
            msg = "The beam dissipates."; col = C_LTEXT_DIM

    elif eff == "wand_invisibility":
        if target:
            target.invisible = True
            target._invis_turns = 10
            msg = f"The {target.name} fades from view!"; col = C_LTEXT_ACCENT
        else:
            msg = "The beam dissipates."; col = C_LTEXT_DIM

    elif eff == "wand_digging":
        # Find the first non-passable tile (wall or boulder) along the beam.
        # Check the immediate next tile first; if passable, scan along the ray.
        lv = game.level
        tx, ty = p.x + fire_dx, p.y + fire_dy
        if lv.is_passable(tx, ty):
            # Beam travels through open floor — find first wall/boulder beyond
            if ray_tiles:
                lx, ly = ray_tiles[-1]
                tx, ty = lx + fire_dx, ly + fire_dy
            else:
                tx, ty = None, None

        if tx is not None and lv.is_in_bounds(tx, ty):
            target_tile = lv.get(tx, ty)
            if target_tile == T_WALL:
                # First hit: wall → boulder (partially destroyed)
                lv.set(tx, ty, T_BOULDER)
                lv.tile_mods[(tx, ty)] = T_BOULDER
                game.ray_anim["tiles"] = (ray_tiles or []) + [(tx, ty)]
                msg = "The beam crumbles the wall into a boulder!"; col = C_LTEXT
            elif target_tile == T_BOULDER:
                # Second hit: boulder → open floor (destroyed)
                lv.set(tx, ty, T_FLOOR)
                lv.tile_mods[(tx, ty)] = T_FLOOR
                game.ray_anim["tiles"] = (ray_tiles or []) + [(tx, ty)]
                msg = "The boulder disintegrates!"; col = C_LTEXT
            else:
                msg = "The beam finds no wall to dig."; col = C_LTEXT_DIM
        else:
            msg = "The beam finds no wall to dig."; col = C_LTEXT_DIM

    elif eff == "wand_polymorph":
        if target:
            from data.monsters import MONSTERS
            # Find the target's approximate "level" by its min_floor
            try:
                orig_data  = next(m for m in MONSTERS if m["id"] == target.id)
                orig_level = orig_data["min_floor"]
            except StopIteration:
                orig_level = game.floor

            # Build pool: different monster type, min_floor within ±10 of original
            pool = [
                m for m in MONSTERS
                if m["id"] != target.id
                and abs(m["min_floor"] - orig_level) <= 10
            ]
            # Fallback: any monster that isn't the same type
            if not pool:
                pool = [m for m in MONSTERS if m["id"] != target.id]

            if pool:
                new_m    = game.rng.choice(pool)
                old_name = target.name
                hp_ratio = target.hp / max(1, target.max_hp)
                target.id          = new_m["id"]
                target.name        = new_m["name"]
                target.glyph       = new_m["glyph"]
                target.color       = new_m.get("color_hint", (200, 200, 200))
                target.special     = list(new_m["special"])
                target.dmg_min, target.dmg_max = new_m["damage"]
                target.ac          = new_m["ac"]
                target.atk         = new_m["atk"]
                target.num_attacks = new_m.get("num_attacks", 1)
                target.xp          = new_m["xp"]
                target.loot_chance = new_m["loot_chance"]
                if new_m.get("hp_fixed") is not None:
                    new_max_hp = new_m["hp_fixed"]
                else:
                    n, s = new_m["hp_dice"]
                    new_max_hp = max(1, sum(game.rng.randint(1, s) for _ in range(n)))
                target.max_hp = new_max_hp
                target.hp     = max(1, int(new_max_hp * hp_ratio))
                msg = f"The {old_name} transforms into a {target.name}!"
                col = C_LTEXT_ACCENT
        else:
            msg = "The beam dissipates."; col = C_LTEXT_DIM

    else:
        msg = "The wand fizzles."; col = C_LTEXT_DIM

    if not accurate:
        msg = "(Missed) " + msg

    _auto_identify(game, item)
    return msg, col


def apply_wand(game, item: dict) -> tuple:
    """Legacy stub — wands now require directional aiming via PHASE_WAND_AIM."""
    return "Choose a direction to fire.", C_LTEXT


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auto_identify(game, item: dict):
    """Mark item as identified in game.identified after use."""
    game.identified.add(item.get("item_id", item.get("id", "")))


def _reveal_floor(game):
    """Mark all tiles on the current level as explored."""
    lv = game.level
    for x in range(MAP_COLS):
        for y in range(MAP_ROWS):
            game.fov.explored.add((x, y))
            game.fov.walked.add((x, y))


def _teleport_player(game):
    p     = game.player
    tiles = [t for t in game.level.floor_tiles()
             if abs(t[0]-p.x)+abs(t[1]-p.y) > 5]
    if tiles:
        p.x, p.y = game.rng.choice(tiles)
        if hasattr(game, "_update_fov"): game._update_fov()


def _remove_curse(p):
    """Remove curses from all currently equipped items only.
    Matches TDR v1.2.3 original behaviour — inventory items are unaffected.
    The player must equip an item before the scroll can free it."""
    for slot, item in p.equipped.items():
        if item and item.get("cursed"):
            item["cursed"] = False


# ── Wish resolver ─────────────────────────────────────────────────────────────

def resolve_wish(game, wish_text: str) -> tuple:
    """
    Parse wish_text and grant the item. Returns (message, color).

    Grammar:
        [plural] <item name> [+N]
    - Item name must match an item's canonical name (case-insensitive).
    - "+N" sets enchant on weapons/armor (capped at item's max_enchant; random if omitted).
    - Plural (trailing s / es, or "Potions of X") grants 2 copies for scrolls/potions.
    - Wands are granted with full charges.
    - Enchant stated > max_enchant → set to random(1, max_enchant).
    - Unrecognised wish → nothing happens.
    """
    import re
    from data.items import ITEMS
    from constants import (IC_WEAPON, IC_ARMOR, IC_SCROLL, IC_POTION,
                           IC_WAND, IC_RING, IC_FOOD, IC_JEWEL, IC_MISC)
    C_GRANT = (210, 175, 45)

    p   = game.player
    raw = wish_text.strip()
    if not raw:
        return "Your wish fades without form.", (150, 150, 150)

    # Parse trailing +N enchant
    enchant_req = None
    m = re.search(r'\+(\d+)\s*$', raw)
    if m:
        enchant_req = int(m.group(1))
        raw = raw[:m.start()].strip()

    # Detect plural form (trailing s/es, or "Scrolls of …" / "Potions of …")
    plural = False
    test   = raw.lower()
    # "Potions of Healing" → "Potion of Healing", "Scrolls of Identify" → "Scroll of Identify"
    if re.match(r'^potions? of ', test):
        plural = test.startswith('potions ')
        raw    = re.sub(r'^potions ', 'potion ', raw, flags=re.IGNORECASE)
    elif re.match(r'^scrolls? of ', test):
        plural = test.startswith('scrolls ')
        raw    = re.sub(r'^scrolls ', 'scroll ', raw, flags=re.IGNORECASE)
    elif test.endswith('s') and not test.endswith('ss'):
        # Try stripping trailing s and see if a match exists
        plural = True   # tentative; cleared if singular not found

    # Match against item names (case-insensitive, trimmed)
    raw_lower = raw.lower().strip()
    matched   = None
    for it in ITEMS:
        if it["name"].lower() == raw_lower:
            matched = it; break

    # If plural strip didn't match, try without the s
    if matched is None and plural and raw_lower.endswith('s'):
        sing = raw_lower[:-1]
        for it in ITEMS:
            if it["name"].lower() == sing:
                matched = it; break
        if matched is None:
            plural = False  # wasn't actually plural, reset

    if matched is None:
        return f'There is no such thing as "{wish_text}".' , (180, 80, 80)

    # Build the item dict (copy from template)
    cat = matched.get("cat", "")

    def _make_dict(template, enc=None):
        d = dict(template)
        d["item_id"]  = template["id"]
        d["enchant"]  = 0
        d["charges"]  = template.get("charges", 0)
        d["throws"]   = template.get("max_throws", 0)
        d["cursed"]   = False
        if cat in (IC_WEAPON, IC_ARMOR):
            me = template.get("max_enchant", 4)
            if enc is None:
                d["enchant"] = game.rng.randint(0, me)
            elif enc > me:
                d["enchant"] = game.rng.randint(1, me)
            else:
                d["enchant"] = enc
        if cat == IC_WAND:
            d["charges"] = template.get("charges", 6)
        return d

    enc = enchant_req   # may be None → random
    items_to_grant = [_make_dict(matched, enc)]
    if plural and cat in (IC_POTION, IC_SCROLL):
        items_to_grant.append(_make_dict(matched, enc))

    # Add to inventory
    granted = 0
    for item_dict in items_to_grant:
        if p.can_carry():
            p.add_to_inventory(item_dict)
            granted += 1
            # Auto-identify by type (but not enchant, unless explicitly stated)
            iid = item_dict.get("item_id","")
            game.identified.add(iid)
        else:
            game.log.add("Your pack is full — item vanishes!", (200, 80, 80))
            break

    game.wish_uses += 1

    nm   = matched["name"]
    qty  = f"{granted}× " if granted > 1 else ""
    enc_s = (f" +{items_to_grant[0]['enchant']}"
             if items_to_grant[0].get("enchant") and cat in (IC_WEAPON, IC_ARMOR)
             else "")
    remaining = 3 - game.wish_uses
    rem_msg = f" ({remaining} wish{'es' if remaining!=1 else ''} remain)" if remaining > 0 else " (no wishes remain)"
    game.log.add(f"Your pack feels heavier.{rem_msg}", C_GRANT)
    return f"Granted: {qty}{nm}{enc_s}.", C_GRANT


# ── Thrown item colors for ray animation ──────────────────────────────────────
THROW_ITEM_COLORS = {
    "small_rock":  (180, 160, 130),
    "large_rock":  (140, 120, 100),
    "dart":        (200, 200, 120),
    "spear":       (180, 140,  60),
    "mac_plus":    (200, 200, 200),
}
THROW_RAY_TICKS = 20   # faster than wand — projectile, not beam


def throw_item_at_direction(game, item: dict, dx: int, dy: int) -> tuple:
    """Throw item in direction (dx,dy) with DEX-based accuracy.
    Sets game.ray_anim.  Returns (message, color).
    Rules:
      - Max range 4 tiles (2 for rocks without sling, doubled with sling)
      - Rocks deal half damage without sling; sling restores full damage and range
      - Darts/spears/mac_plus land on last tile and can be picked up
      - Rocks do not land (they bounce/shatter)
    """
    from constants import S_DEX, STAT_MAX, IC_WEAPON
    p      = game.player
    iid    = item.get("item_id", item.get("id", ""))
    col    = C_LTEXT

    # ── Sling check ──────────────────────────────────────────────────────────
    is_rock   = iid in ("small_rock", "large_rock")
    has_sling = (game.player.equipped.get("offhand") is not None and
                 game.player.equipped["offhand"].get("id","") == "sling" or
                 game.player.equipped.get("offhand") is not None and
                 game.player.equipped["offhand"].get("item_id","") == "sling")
    # simpler check:
    offhand = game.player.equipped.get("offhand")
    has_sling = (offhand is not None and
                 offhand.get("item_id", offhand.get("id","")) == "sling")

    base_dmg  = item.get("base_dmg", 1)
    max_range = 4

    if is_rock and not has_sling:
        base_dmg  = max(1, base_dmg // 2)
        max_range = 2

    # ── Accuracy check (DEX-based, range 1-25) ───────────────────────────────
    # DEX 1→25%, DEX 13→60%, DEX 25→95%
    dex     = p.stats[S_DEX]
    hit_pct = max(25, min(95, round(25 + (dex - 1) * 70 / (STAT_MAX - 1))))
    accurate = (game.rng.randint(1, 100) <= hit_pct)

    fire_dx, fire_dy = dx, dy
    if not accurate:
        dirs = [(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
        try:
            i = dirs.index((dx, dy))
        except ValueError:
            i = 0
        fire_dx, fire_dy = dirs[(i + game.rng.choice([-1, 1])) % 8]

    # ── Trace path (stops at wall; passes through open tiles up to max_range) ─
    path_tiles = []
    cx, cy = p.x + fire_dx, p.y + fire_dy
    for _ in range(max_range):
        if not (0 <= cx < MAP_COLS and 0 <= cy < MAP_ROWS):
            break
        if not game.level.is_passable(cx, cy):
            break
        path_tiles.append((cx, cy))
        if game._monster_at(cx, cy):
            break          # stops at first monster hit
        cx += fire_dx; cy += fire_dy

    # ── Target: monster at end of path ───────────────────────────────────────
    target = None
    if path_tiles:
        lx, ly = path_tiles[-1]
        target = game._monster_at(lx, ly)

    # ── Ray animation ─────────────────────────────────────────────────────────
    ray_col = THROW_ITEM_COLORS.get(iid, (200, 200, 160))
    game.ray_anim = {
        "tiles":       path_tiles,
        "color":       ray_col,
        "start_tick":  None,
        "total_ticks": THROW_RAY_TICKS,
        "hit":         target is not None,
    }

    item_name = item.get("name", "projectile")

    # ── Consume from inventory ────────────────────────────────────────────────
    # Rocks are bundle ammo — decrement count, remove when exhausted.
    # All other throwables (dart, spear, mac_plus) are individual objects:
    # the physical item has flown away, always remove from inventory now.
    # The item may re-appear on the floor as a separate entity to pick up.
    if is_rock:
        throws_left = item.get("throws", 1) - 1
        item["throws"] = throws_left
        if throws_left <= 0:
            game.player.remove_from_inventory(item)
            if game.player.equipped.get("missile") is item:
                game.player.equipped["missile"] = None
    else:
        game.player.remove_from_inventory(item)
        if game.player.equipped.get("missile") is item:
            game.player.equipped["missile"] = None

    # ── Apply hit ────────────────────────────────────────────────────────────
    if not path_tiles:
        return f"The {item_name} hits the wall!", C_LTEXT_DIM

    if not accurate and not target:
        msg = f"The {item_name} goes wide!"
        col = C_LTEXT_DIM
    elif target:
        target.take_damage(base_dmg)
        if target.is_dead():
            game._kill_monster(target)
            msg = f"The {item_name} hits the {target.name}!  Slain!"
        else:
            msg = f"The {item_name} hits the {target.name} for {base_dmg} damage."
        col = C_HP_LOW
    else:
        msg = f"The {item_name} flies through the air."
        col = C_LTEXT_DIM

    # ── Leave landed item on floor (non-rock items only) ─────────────────────
    can_land = not is_rock
    if can_land and path_tiles:
        lx, ly = path_tiles[-1]
        from entities.item import Item as ItemEntity
        landed = ItemEntity(iid, lx, ly)
        game.items.append(landed)
        if target is None:  # only mention it if we're not talking about a kill
            msg += f"  The {item_name} lands on the floor."

    return msg, col
