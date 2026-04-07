# engine/game.py
# Central game state. Orchestrates turn logic, combat, floor transitions,
# message log, and all entity interactions.
# Designed as the stable backbone for all 10 build steps.

import random
from typing import List, Optional, Tuple

from constants import (
    MAP_COLS, MAP_ROWS, TOTAL_FLOORS,
    S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA,
    FOOD_PER_MOVE, T_STAIR_UP, T_STAIR_DOWN, T_WALL, T_BOULDER, T_FLOOR,
    C_WHITE, C_TEXT_DIM, C_HP_LOW, C_GOLD, C_XP,
    FOV_RADIUS_BASE, MSG_MAX_STORED,
    AP_MOVE, AP_SCROLL, AP_EAT, AP_WISH, AP_PUSH_BOULDER,
    PASSABLE, BOULDER_MIN_STR,
    DIFF_EXPLORER, DIFF_ADVENTURER, DIFF_HERO, DIFF_ARCHITECT,
    GK_BARRIER_FLOORS, GK_HP_TABLE, GK_AC_TABLE, GK_ATK_TABLE,
    FOOD_OVERSTAY_WARN, FOOD_OVERSTAY_HEAVY,
    FOOD_OVERSTAY_MULT_WARN, FOOD_OVERSTAY_MULT_HEAVY,
)
from engine.dungeon import FloorCache, DungeonLevel
from engine.fov import FovMap
from engine.audio import get_audio
from entities.player import Player
from entities.monster import Monster
from entities.item import Item
from data.classes import get_class


# ── Message Log ──────────────────────────────────────────────────────────────

class MessageLog:
    def __init__(self):
        self._lines: List[Tuple[str, tuple]] = []

    def add(self, text: str, color: tuple = C_WHITE):
        self._lines.insert(0, (text, color))
        if len(self._lines) > MSG_MAX_STORED:
            self._lines.pop()

    def recent(self, n: int = 6) -> List[Tuple[str, tuple]]:
        return self._lines[:n]

    def clear(self):
        self._lines.clear()


# ── Game phases ───────────────────────────────────────────────────────────────

PHASE_TITLE      = "title"
PHASE_CHAR_CREATE= "char_create"
PHASE_PLAYING    = "playing"
PHASE_DEAD       = "dead"
PHASE_WIN        = "win"
PHASE_INVENTORY  = "inventory"
PHASE_WISH       = "wish"        # wish-entry popup
PHASE_QUICK_USE  = "quick_use"
PHASE_WAND_AIM   = "wand_aim"    # directional wand firing
PHASE_THROW_AIM  = "throw_aim"   # directional item throwing


# ── GameState ────────────────────────────────────────────────────────────────

class GameState:

    def __init__(self):
        self.phase:   str          = PHASE_TITLE
        self.id_map:  dict         = {}   # item_id → unidentified display name
        self.identified: set       = set()  # item IDs the player knows
        self.pending_identify: int = 0    # uses remaining from identify scroll
        self.fov_dirty: bool        = False
        self.pickup_mode: bool      = True   # auto-pick up items on move
        self._last_pickup: list     = []     # item dicts picked up this floor visit
        self.wish_uses:   int       = 0      # how many wishes have been used (max 3)
        self.wish_input:  str       = ""     # text being typed in wish popup
        self.quick_use_cat: str     = ""     # category for quick-use submenu
        self._encumber_skip: bool   = False  # alternating skip when encumbered
        self._stuffed_skip:  int    = 0   # step counter for stuffed penalty (fires every 4th)
        self._ring_slow_skip: bool  = False  # alternating skip from ring of slowness
        self.pending_wand:  dict    = None   # wand item awaiting direction in PHASE_WAND_AIM
        self.pending_throw: dict    = None   # throw item awaiting direction in PHASE_THROW_AIM
        self.ray_anim:      dict    = None   # active ray animation for renderer
        self.paused:        bool    = False  # real-time turn timer frozen
        self.turn_reset_pending: bool = False  # signals main loop to restart turn timer
        self.player:  Optional[Player] = None
        self.log:     MessageLog   = MessageLog()
        self.rng:     random.Random = random.Random()

        # Current floor
        self.floor:   int          = 1
        self.level:   Optional[DungeonLevel] = None
        self.cache:   Optional[FloorCache]   = None

        # Entities on current floor
        self.monsters: List[Monster] = []
        self.items:    List[Item]    = []

        # FOV maps keyed by floor number
        self._fov_maps: dict = {}

        # Turn counter
        self.turn: int = 0

        # Wandering monster tracking
        self.turns_on_floor: int  = 0   # resets each time the player enters a floor
        self.wander_count:   int  = 0   # wandering monsters spawned this floor visit

        # Save state
        self.save_path: str = ""    # path of last save/load, or "" if never saved
        self.dirty:    bool = False  # True when unsaved changes exist

        # ── Hall of Fame tracking ──────────────────────────────────────────────
        self.game_id:        int  = 0    # = dungeon base_seed, unique per run
        self.death_cause:    str  = ""   # set just before PHASE_DEAD / PHASE_WIN
        self.stat_xp_earned: int  = 0    # cumulative XP ever awarded (never resets)
        self.hof_result            = None  # (entry_dict, rank|None) after submit
        self._hof_submitted: bool  = False

        # ── Difficulty ────────────────────────────────────────────────────────
        self.difficulty:     str   = DIFF_ADVENTURER
        self._food_acc:      float = 0.0   # fractional food accumulator (Explorer ½ rate)

        # ── Gate Keeper section tracking ─────────────────────────────────────
        # Set of barrier floor numbers whose Gate Keeper has been defeated.
        self.gk_sections_cleared: set = set()

    # ── Floor FOV ─────────────────────────────────────────────────────────────

    @property
    def fov(self) -> FovMap:
        if self.floor not in self._fov_maps:
            self._fov_maps[self.floor] = FovMap(MAP_COLS, MAP_ROWS)
        return self._fov_maps[self.floor]

    @property
    def player_on_stairs(self) -> bool:
        """True when player is standing on any stair tile — renderer uses this for blackout."""
        if not self.player or not self.level:
            return False
        t = self.level.get(self.player.x, self.player.y)
        return t in (T_STAIR_UP, T_STAIR_DOWN)

    # ── New game ──────────────────────────────────────────────────────────────

    def start_new_game(self, name: str, class_key: str, difficulty: str = DIFF_ADVENTURER):
        cls          = get_class(class_key)
        self.player  = Player(name, class_key, cls["stats"], cls["base_hp"])
        self.log     = MessageLog()
        self.rng     = random.Random()
        seed         = self.rng.randint(0, 0xFFFFFF)
        self.cache   = FloorCache(seed)
        self.floor   = 1
        self._fov_maps.clear()
        self.turn    = 0
        self.phase   = PHASE_PLAYING
        self.paused  = False
        self.turn_reset_pending = False
        self._stuffed_skip = 0
        self.identified      = set()
        self.pending_identify = 0
        self.pending_wand     = None
        self.pending_throw    = None
        self.ray_anim         = None
        self._build_id_map()
        self.gk_sections_cleared = set()
        # HoF — new run
        self.game_id        = self.cache.base_seed
        self.death_cause    = ""
        self.stat_xp_earned = 0
        self.hof_result     = None
        self._hof_submitted = False

        # Difficulty
        # Architect is unlocked by entering exactly "Architect" as character name
        if name.strip() == "Architect":
            self.difficulty = DIFF_ARCHITECT
        else:
            self.difficulty = difficulty
        self._food_acc = 0.0

        self._enter_floor(1, from_above=True)
        self._grant_starting_kit()

        # ── Architect mode post-init ──────────────────────────────────────────
        if self.difficulty == DIFF_ARCHITECT:
            self._init_architect()

        self.log.add("Maybe the Orb will set you free...", C_TEXT_DIM)
        self.log.add(f"You are a level 1 {cls['name']}. Descend to find the Orb.")

    # ── Floor loading ─────────────────────────────────────────────────────────

    def _grant_starting_kit(self):
        """Grant each character class their starting equipment and consumables.
        Weapons and armour are auto-equipped; expert classes know their own gear
        (enchant_known=True, no fuzzy guess for starting items)."""
        from data.classes import CLASSES
        from data.items   import get_item
        from constants    import IC_WEAPON, IC_ARMOR, IC_RING

        p   = self.player
        cls = CLASSES[p.class_key]
        kit = cls.get("starting_kit", {})

        def _make_item(item_id: str, enchant: int = 0) -> dict:
            data = dict(get_item(item_id))
            data["item_id"]      = item_id
            data["enchant"]      = enchant
            data["enchant_known"] = False
            data["identified"]   = False
            data["cursed"]       = False
            data["charges"]      = data.get("charges", 0)
            data["throws"]       = data.get("max_throws", 0)
            return data

        def _slot_for(item_dict: dict) -> str:
            """Return the equipped-slot key for a wearable item."""
            s = item_dict.get("slot", "")
            if s == "weapon":    return "weapon"
            if s == "offhand":   return "offhand"
            if s in ("armor",):  return "armor"
            if s == "helmet":    return "helmet"
            if s == "gauntlets": return "gauntlets"
            if s == "cloak":     return "cloak"
            if s == "ring":      return "ring_r"
            return ""

        cls_id_cat = cls.get("identify")

        # ── Equip items ────────────────────────────────────────────────────────
        for entry in kit.get("equip", []):
            choices = entry["choices"]
            item_id = self.rng.choice(choices)
            item_d  = _make_item(item_id)
            # Expert classes already know their own starting gear
            if cls_id_cat and item_d.get("cat") == cls_id_cat:
                item_d["enchant_known"] = True
            p.inventory.append(item_d)
            slot = _slot_for(item_d)
            if slot:
                p.equipped[slot] = item_d

        # ── Carry items (consumables, rings) ──────────────────────────────────
        for entry in kit.get("carry", []):
            choices = list(entry["choices"])
            count   = entry.get("count", 1)
            self.rng.shuffle(choices)
            for item_id in choices[:count]:
                item_d = _make_item(item_id)
                # Expert classes start with their consumable category identified
                if cls_id_cat and item_d.get("cat") == cls_id_cat:
                    item_d["identified"]    = True
                    item_d["enchant_known"] = True
                    self.identified.add(item_id)
                p.inventory.append(item_d)

    def _init_architect(self):
        """Architect hidden mode: max stats, all items, all identified."""
        from constants import STAT_MAX
        from data.items import ITEMS

        p = self.player
        # Max out all stats
        p.stats = [STAT_MAX] * 6
        p.max_hp = 99
        p.hp     = 99

        # Identify everything
        self.identified = {item["id"] for item in ITEMS}

        # Add one of each item to inventory (skip orb — it lives in the dungeon)
        for item_data in ITEMS:
            if item_data["id"] == "orb_of_carnos":
                continue
            inv_item = dict(item_data)
            inv_item["item_id"]       = item_data["id"]
            inv_item["enchant"]       = 0
            inv_item["enchant_known"] = True
            inv_item["identified"]    = True
            inv_item["cursed"]        = False
            inv_item["charges"]       = item_data.get("charges", 0)
            inv_item["throws"]        = item_data.get("max_throws", 0)
            p.inventory.append(inv_item)

        self.log.add("ARCHITECT MODE: All items granted. All stats maxed.", (100, 200, 255))

    def _consume_food(self, base_amount: float = FOOD_PER_MOVE):
        """Apply food cost with difficulty scaling, ring hunger drain,
        and overstay multiplier.

        Overstay multiplier (applied when turns_on_floor exceeds thresholds):
          0–299 turns  : ×1.0  (normal — full floor exploration is comfortable)
          300–499 turns: ×1.5  (warning — player is lingering too long)
          500+ turns   : ×2.5  (heavy — clear punishment for camping/grinding)
        Explorer difficulty: base rate halved via float accumulator before
        the multiplier is applied, so overstay still escalates on Explorer.
        """
        p = self.player

        # ── Overstay multiplier ───────────────────────────────────────────────
        tof = self.turns_on_floor
        if tof >= FOOD_OVERSTAY_HEAVY:
            mult = FOOD_OVERSTAY_MULT_HEAVY
        elif tof >= FOOD_OVERSTAY_WARN:
            mult = FOOD_OVERSTAY_MULT_WARN
        else:
            mult = 1.0

        effective = base_amount * mult

        # ── Difficulty scaling (Explorer: half rate) ──────────────────────────
        if self.difficulty == DIFF_EXPLORER:
            self._food_acc += effective * 0.5
            amount = int(self._food_acc)
            self._food_acc -= amount
        else:
            # Use accumulator for all non-integer drain values
            self._food_acc += effective
            amount = int(self._food_acc)
            self._food_acc -= amount

        # ── Ring hunger drain (per base move call only) ───────────────────────
        if base_amount == FOOD_PER_MOVE:
            amount += p.ring_hunger_drain

        # ── Warn once when overstay threshold is first crossed ────────────────
        if (tof == FOOD_OVERSTAY_WARN and
                base_amount == FOOD_PER_MOVE and
                self.difficulty != DIFF_ARCHITECT):
            self.log.add(
                "You've been on this floor a long time. Your hunger grows.",
                (200, 160, 60)
            )
        elif (tof == FOOD_OVERSTAY_HEAVY and
                base_amount == FOOD_PER_MOVE and
                self.difficulty != DIFF_ARCHITECT):
            self.log.add(
                "You are lingering far too long. Hunger gnaws at you fiercely!",
                C_HP_LOW
            )

        p.consume_food(amount)

    def _enter_floor(self, floor: int, from_above: bool = True):
        self.floor = floor
        self.level = self.cache.get(floor)
        lv         = self.level
        p          = self.player

        # Place player
        if from_above:
            # Entering from above: land on stair_up (entrance from surface / upper floor)
            p.x, p.y = lv.stair_up if lv.stair_up else lv.spawn_player
        else:
            # Ascending from below: land on stair_DOWN — the stairs you just came through.
            # Landing on stair_up would mean the next step takes you up again (wrong).
            p.x, p.y = lv.stair_down if lv.stair_down else lv.spawn_player

        # Always reload entities from the level's saved spawn tables.
        # On first visit: tables were set by _populate() — all valid floor tiles.
        # On return:      _save_floor_state() updated the tables before we left,
        #                 so reloading correctly restores the saved state.
        # Bug fixed: the old guard (if floor not in self._fov_maps) skipped this
        # on revisits, leaving self.monsters/self.items from the previous floor —
        # those entities had coordinates valid on the other map, appearing in walls here.
        self._spawn_entities(lv)

        # Reset wandering monster counters for this visit
        self.turns_on_floor = 0
        self.wander_count   = 0

        # Gate Keeper: spawn on floors that guard a barrier below
        self._maybe_spawn_gate_keeper()

        # Recompute FOV
        self._update_fov()

    def _spawn_entities(self, lv: DungeonLevel):
        self.monsters.clear()
        self.items.clear()
        occupied_positions: set = set()   # guard against duplicate spawn coords

        for spawn in lv.monster_spawns:
            pos = (spawn["x"], spawn["y"])
            if pos in occupied_positions:
                # Find nearest free passable tile
                pos = self._nearest_free_tile(lv, pos, occupied_positions)
                if pos is None:
                    continue   # no room — skip this spawn
            occupied_positions.add(pos)
            m = Monster(spawn["monster_id"], pos[0], pos[1],
                        spawn["hp"], spawn["max_hp"])
            m.boss_escapes = spawn.get("boss_escapes", 0)
            if spawn["monster_id"] == "gate_keeper":
                if spawn.get("gk_ac") is not None:
                    m.ac          = spawn["gk_ac"]
                if spawn.get("gk_atk") is not None:
                    m.atk         = spawn["gk_atk"]
                if spawn.get("gk_num_attacks") is not None:
                    m.num_attacks = spawn["gk_num_attacks"]
                if spawn.get("gk_dmg_min") is not None:
                    m.dmg_min     = spawn["gk_dmg_min"]
                if spawn.get("gk_dmg_max") is not None:
                    m.dmg_max     = spawn["gk_dmg_max"]
            self.monsters.append(m)

        for spawn in lv.item_spawns:
            it = Item(spawn["item_id"], spawn["x"], spawn["y"],
                      enchant=spawn.get("enchant", 0))
            # Restore identification state from when this item was dropped
            it.id_state_identified     = spawn.get("identified",     False)
            it.id_state_enchant_known  = spawn.get("enchant_known",  False)
            it.id_state_fuzzy_enchant  = spawn.get("fuzzy_enchant",  None)
            it.id_state_fuzzy_id       = spawn.get("fuzzy_id",       None)
            it.id_state_fuzzy_name     = spawn.get("fuzzy_name",     None)
            it.id_state_pending_confirm = spawn.get("pending_confirm", False)
            self.items.append(it)

    def _floor_monsters(self) -> List[Monster]:
        return [m for m in self.monsters if m.alive]

    def _floor_items(self) -> List[Item]:
        return list(self.items)

    # ── FOV update ────────────────────────────────────────────────────────────

    def _update_fov(self):
        p   = self.player
        fov = self.fov
        fov.update(self.level, p.x, p.y, p.fov_radius, p.intelligence,
                   xray=p.xray_vision)
        fov.mark_walked(p.x, p.y)   # record footstep for mini-map

    # ── Player turn ───────────────────────────────────────────────────────────

    def try_move(self, dx: int, dy: int) -> bool:
        """
        Attempt to move the player by (dx, dy).
        Returns True if a turn was consumed.
        Handles: walls, doors, monster bumps, tile events, floor transitions.
        """
        if self.phase != PHASE_PLAYING:
            return False

        p  = self.player
        lv = self.level

        # ── Stunned: player loses their action entirely ───────────────────────
        if getattr(p, "stunned", False):
            p.apply_status("stunned", max(0, p.status_turns.get("stunned", 1) - 1))
            if p.status_turns.get("stunned", 0) <= 0:
                p.stunned = False
                p.status_turns.pop("stunned", None)
                self.log.add("You shake off the stun.", (200, 200, 200))
            else:
                self.log.add("You are stunned and cannot act!", C_HP_LOW)
            self._end_player_turn()
            return True

        # ── Confused: 50% chance to randomise movement direction ─────────────
        if getattr(p, "confused", False) and self.rng.random() < 0.5:
            dirs = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
            dx, dy = self.rng.choice(dirs)
            self.log.add("You stumble in confusion!", (180, 100, 180))

        nx = p.x + dx
        ny = p.y + dy

        # ── Encumbrance movement checks ───────────────────────────────────────
        if p.overburdened:
            self.log.add("You are too encumbered to move!", C_HP_LOW)
            self._end_player_turn()
            return True   # turn consumed

        if p.encumbered:
            # Every other movement attempt is skipped (slowed)
            if self._encumber_skip:
                self._encumber_skip = False
                self.log.add("You struggle under the weight.", (180, 140, 60))
                self._end_player_turn()
                return True
            self._encumber_skip = True
        else:
            self._encumber_skip = False

        # ── Stuffed movement penalty ───────────────────────────────────────────
        # Penalty fires every 4th step (much milder than encumbrance).
        # Eating is still discouraged but not severely punished.
        if p.stuffed:
            self._stuffed_skip = (self._stuffed_skip + 1) % 4
            if self._stuffed_skip == 0:
                self.log.add("You waddle, weighed down by your full belly.", (180, 140, 80))
                self._end_player_turn()
                return True
        else:
            self._stuffed_skip = 0

        # ── Ring of Slowness ────────────────────────────────────────────────────
        # Skip every other player action; monsters still act (effectively double turns for them)
        if p.ring_slowed:
            if self._ring_slow_skip:
                self._ring_slow_skip = False
                self.log.add("You move sluggishly.", (120, 120, 180))
                self._end_player_turn()   # monsters act, player is stuck this turn
                return True
            self._ring_slow_skip = True
        else:
            self._ring_slow_skip = False

        # ── Cold-aura slow (from Drackone / Ice Whirlwind proximity) ─────────
        if getattr(p, "slowed", False):
            if self._encumber_skip:   # reuse alternating-skip bool for cold slow
                self._encumber_skip = False
                self.log.add("You move sluggishly in the cold.", (140, 180, 220))
                self._end_player_turn()
                return True
            self._encumber_skip = True

        if not lv.is_in_bounds(nx, ny):
            return False

        tile = lv.get(nx, ny)

        # ── Wall / void ───────────────────────────────────────────────────────
        if tile == T_WALL:
            return False

        # ── Boulder: push or block ─────────────────────────────────────────────
        if tile == T_BOULDER:
            if p.strength < BOULDER_MIN_STR:
                self.log.add("The boulder is too heavy!", C_HP_LOW)
                self._end_player_turn()
                return True
            bx, by = nx + dx, ny + dy
            beyond = lv.get(bx, by)
            if beyond not in PASSABLE:
                self.log.add("There's no room to push the boulder.", C_TEXT_DIM)
                self._end_player_turn()
                return True
            if self._monster_at(bx, by):
                self.log.add("Something blocks the boulder!", C_TEXT_DIM)
                self._end_player_turn()
                return True
            # Slide the boulder into the next tile; player steps into its old spot
            lv.set(nx, ny, T_FLOOR)
            lv.set(bx, by, T_BOULDER)
            lv.tile_mods[(nx, ny)] = T_FLOOR
            lv.tile_mods[(bx, by)] = T_BOULDER
            self.log.add("The boulder moves!", (200, 200, 200))
            get_audio().play("boulder_push")
            p.x, p.y = nx, ny
            self._consume_food()
            self._pick_up_items_v2(nx, ny)
            self._update_fov()
            self._end_player_turn(AP_PUSH_BOULDER)
            return True

        # ── Monster: attack ───────────────────────────────────────────────────
        target = self._monster_at(nx, ny)
        if target:
            self._player_attacks(target)
            self._end_player_turn()
            return True

        # ── Blocked stair exit (floor 1, no Orb) ─────────────────────────────
        # Must check before moving so the player never lands on the tile.
        if tile == T_STAIR_UP and self.floor <= 1:
            has_orb = any(
                getattr(it, 'id', None) == 'orb_of_carnos'
                for it in p.inventory
            )
            if not has_orb:
                self.log.add("A force prevents you from leaving without the Orb!", C_HP_LOW)
                self._end_player_turn()
                return True   # turn consumed — bumped the invisible barrier

        # ── Move ──────────────────────────────────────────────────────────────
        p.x, p.y = nx, ny
        self._consume_food()
        self._pick_up_items_v2(nx, ny)

        # Auto-transition: stepping onto a stair immediately changes floor.
        # The renderer will draw the player blind (FOV=0) on the stair for
        # exactly one frame before the new floor is loaded.
        if tile == T_STAIR_DOWN:
            if getattr(p, "levitating", False):
                self.log.add("You float above the stairs — you cannot descend!", C_HP_LOW)
                self._end_player_turn()
                return True
            if self.floor >= TOTAL_FLOORS:
                self.log.add("There is nowhere deeper to go.")
            else:
                # Gate Keeper stair block
                next_floor = self.floor + 1
                if self._gk_blocks_descent(next_floor):
                    self.log.add(
                        "A force prevents you from descending to the next level.",
                        C_HP_LOW
                    )
                    self.log.add("The Gate Keeper holds the key!!!", (220, 180, 60))
                    self._end_player_turn()
                    return True
                self.log.add(f"You descend to level {self.floor + 1}.")
                get_audio().play("stairs_down")
                self._save_floor_state()
                self._enter_floor(self.floor + 1, from_above=True)
            self._end_player_turn()
            return True

        if tile == T_STAIR_UP:
            if self.floor <= 1:
                self.log.add("You escaped the dungeon with the Orb of Carnos!", C_GOLD)
                get_audio().play("victory")
                self.death_cause = "Escaped with the Orb"
                self.phase = PHASE_WIN
                self._end_player_turn()
                return True
            else:
                self.log.add(f"You ascend to level {self.floor - 1}.")
                get_audio().play("stairs_up")
                self._save_floor_state()
                self._enter_floor(self.floor - 1, from_above=False)
            self._end_player_turn()
            return True

        self._update_fov()
        self._end_player_turn()
        return True

    def rest(self) -> bool:
        """Skip a turn; recover 1 HP if no adjacent enemies."""
        if self.phase != PHASE_PLAYING:
            return False
        p = self.player
        adjacent = any(
            abs(m.x - p.x) <= 1 and abs(m.y - p.y) <= 1
            for m in self._floor_monsters()
        )
        if not adjacent and p.hp < p.max_hp:
            p.heal(1)
        self._consume_food()
        self._end_player_turn()
        return True

    def _handle_tile_at(self, x: int, y: int):
        pass  # Stair transitions now handled directly in try_move

    def descend(self) -> bool:
        """Go down the stairs."""
        if self.phase != PHASE_PLAYING:
            return False
        p  = self.player
        lv = self.level
        if lv.get(p.x, p.y) != T_STAIR_DOWN:
            self.log.add("You are not standing on a staircase.")
            return False
        if self.floor >= TOTAL_FLOORS:
            self.log.add("There is nowhere deeper to go.")
            return False
        self.log.add(f"You descend to level {self.floor + 1}.")
        # Save current floor monster/item state
        self._save_floor_state()
        self._enter_floor(self.floor + 1, from_above=True)
        return True

    def ascend(self) -> bool:
        """Go up the stairs."""
        if self.phase != PHASE_PLAYING:
            return False
        p  = self.player
        lv = self.level
        if lv.get(p.x, p.y) != T_STAIR_UP:
            self.log.add("You are not standing on an upward staircase.")
            return False
        if self.floor <= 1:
            self.log.add("A force prevents you from escaping to the surface.")
            return False
        self.log.add(f"You ascend to level {self.floor - 1}.")
        self._save_floor_state()
        self._enter_floor(self.floor - 1, from_above=False)
        return True

    def _save_floor_state(self):
        """
        Persist live monster/item state back to the floor's spawn tables
        so they're restored when the player returns.
        """
        lv = self.level
        lv.monster_spawns = [
            {
                "monster_id": m.id, "x": m.x, "y": m.y,
                "hp": m.hp, "max_hp": m.max_hp,
                "boss_escapes": getattr(m, "boss_escapes", 0),
                "gk_ac":         getattr(m, "ac",          None) if m.id == "gate_keeper" else None,
                "gk_atk":        getattr(m, "atk",         None) if m.id == "gate_keeper" else None,
                "gk_num_attacks":getattr(m, "num_attacks",  None) if m.id == "gate_keeper" else None,
                "gk_dmg_min":    getattr(m, "dmg_min",     None) if m.id == "gate_keeper" else None,
                "gk_dmg_max":    getattr(m, "dmg_max",     None) if m.id == "gate_keeper" else None,
            }
            for m in self.monsters if m.alive
        ]
        lv.item_spawns = [
            {
                "item_id":       it.id,
                "x":             it.x,
                "y":             it.y,
                "enchant":       it.enchant,
                # Persist identification state so dropped+re-picked items retain
                # what the player already knew about them.
                "identified":    getattr(it, "id_state_identified",   False),
                "enchant_known": getattr(it, "id_state_enchant_known", False),
                "fuzzy_enchant": getattr(it, "id_state_fuzzy_enchant", None),
                "fuzzy_id":      getattr(it, "id_state_fuzzy_id",     None),
                "fuzzy_name":    getattr(it, "id_state_fuzzy_name",   None),
                "pending_confirm":getattr(it, "id_state_pending_confirm", False),
            }
            for it in self.items
        ]

    # ── Item pickup ───────────────────────────────────────────────────────────

    # ── Combat ────────────────────────────────────────────────────────────────

    def _player_attacks(self, monster: Monster):
        p        = self.player
        # Wake sleeping monsters when hit
        if getattr(monster, "sleeping", 0) > 0:
            monster.sleeping = 0
            self.log.add(f"The {monster.name} wakes up!", (220, 200, 120))
        # Track pre-attack hostility to announce provocation
        was_non_hostile = getattr(monster, "current_hostility", 2) < 2 and not monster.provoked
        n, faces = p.weapon_damage_range          # n dice, each 1..faces
        roll     = sum(self.rng.randint(1, faces) for _ in range(n)) + p.damage_bonus
        dmg      = max(0, roll)
        monster.take_damage(dmg)

        if dmg == 0:
            self.log.add(f"You miss the {monster.name}.")
        else:
            self.log.add(f"You hit the {monster.name} for {dmg} damage.")
            get_audio().play("hit_monster")
            if was_non_hostile and monster.provoked:
                self.log.add(f"The {monster.name} turns hostile!", (220, 120, 40))

        if monster.is_dead():
            if "boss_escape" in monster.special and monster.boss_escapes < 2:
                self._boss_escape(monster)
            else:
                self._kill_monster(monster)

    def _monster_attacks(self, monster: Monster):
        """Execute one monster's attack sequence for this turn.

        Hit system (hybrid — AC affects both avoidance and mitigation):
          Hit roll:    1d20 ≤ clamp(atk - (10 - player.AC) // 2, 1, 20)
                       AC contributes half as much to avoidance as in pure systems.
                       Examples with atk=9:
                         Unarmored (AC=10): threshold=9  → 45% hit
                         Chain     (AC= 8): threshold=8  → 40% hit
                         Banded    (AC= 6): threshold=7  → 35% hit
                         Plate     (AC= 4): threshold=6  → 30% hit
          AC effect:   damage reduced by max(0, (10 - player.AC) × 0.4)
                       Leather absorbs 0.4/hit, Chain 0.8, Banded 1.6, Plate 2.4.
                       Each upgrade tier is meaningfully felt.
          Min damage:  1 HP on every successful hit (armour never negates a blow).

        Multi-attack: num_attacks fires per turn (1 for most, 2 for elite atk>=20,
        3 for apex atk>=25). Each attack rolls independently.
        """
        p       = self.player
        name    = monster.name
        num_atk = getattr(monster, "num_attacks", 1)

        # AC-based flat damage reduction (independent of hit chance)
        ac_reduction = max(0.0, (10 - p.armor_class) * 0.4)

        for attack_n in range(num_atk):
            if not p.alive:
                break

            # ── Hit roll ──────────────────────────────────────────────────────
            threshold = max(1, min(20, monster.atk - (10 - p.armor_class) // 2))
            hit_roll  = self.rng.randint(1, 20)

            if hit_roll > threshold:
                if num_atk == 1:
                    self.log.add(f"The {name} misses you.")
                else:
                    self.log.add(f"The {name} misses (attack {attack_n + 1}).")
                continue

            # ── Damage roll — minimum 1 on a successful hit ───────────────────
            raw_dmg = self.rng.randint(monster.dmg_min, monster.dmg_max)
            dmg     = max(1, int(raw_dmg - ac_reduction))
            actual  = p.take_damage(dmg)

            if name == "The Floor":
                self.log.add(f"The Floor hits! ({actual} damage)", C_HP_LOW)
            elif num_atk > 1:
                self.log.add(
                    f"The {name} hits you ({attack_n + 1}/{num_atk})"
                    f" for {actual} damage.", C_HP_LOW)
            else:
                self.log.add(f"The {name} hits you for {actual} damage.", C_HP_LOW)
            get_audio().play("hit_player")

            # ── On-hit special abilities ──────────────────────────────────────
            self._apply_monster_on_hit(monster)

            if not p.alive:
                get_audio().play("player_death")
                self.death_cause = f"Slain by {name}"
                self.phase = PHASE_DEAD
                self.log.add("You have died.", C_HP_LOW)
                return

    def _apply_monster_on_hit(self, monster: Monster):
        """Apply the monster's on-hit special tag effects to the player."""
        p = self.player
        for tag in monster.special:

            # ── confuse: Wandering Eye, Witch ─────────────────────────────────
            if tag == "confuse":
                if not getattr(p, "confused", False):
                    p.confused = True
                    p.status_turns["confused"] = 20
                    self.log.add(f"The {monster.name} confuses you!", (180, 100, 220))

            # ── stat_drain: Amadon ────────────────────────────────────────────
            elif tag == "stat_drain":
                from constants import S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA, STAT_NAMES
                idx = self.rng.randint(0, 5)
                if p.stats[idx] > 1:
                    p.stats[idx] -= 1
                    # CON drain permanently reduces max HP
                    if idx == S_CON:
                        loss = max(0, p.max_hp - max(1, p.max_hp - 1))
                        p.max_hp = max(1, p.max_hp - 1)
                        p.hp     = min(p.hp, p.max_hp)
                    sname = STAT_NAMES[idx]
                    self.log.add(
                        f"The {monster.name} drains your {sname}! ({sname} now {p.stats[idx]})",
                        (220, 60, 60)
                    )

            # ── level_drain: Banshee ──────────────────────────────────────────
            elif tag == "level_drain":
                drained = p.drain_level()
                if drained:
                    self.log.add(
                        f"The {monster.name} drains your life force!  Level → {p.level}",
                        (160, 60, 220)
                    )
                else:
                    self.log.add(f"The {monster.name} reaches for your soul!", (160, 60, 220))
                if not p.alive:
                    self.death_cause = f"Level drained to death by {monster.name}"

            # ── head_smash: Reaper (40% stun chance) ─────────────────────────
            elif tag == "head_smash":
                if self.rng.random() < 0.40:
                    stun_turns = 2
                    p.stunned  = True
                    p.status_turns["stunned"] = stun_turns
                    if p.equipped.get("helmet"):
                        self.log.add(
                            f"The {monster.name} smashes your head!  Your helmet saves you!",
                            (200, 180, 60)
                        )
                    else:
                        self.log.add(
                            f"The {monster.name} smashes your head!  You are stunned!",
                            C_HP_LOW
                        )

            # ── acid_splash: Black Pudding ────────────────────────────────────
            elif tag == "acid_splash":
                acid_dmg = self.rng.randint(1, 4)
                p.take_damage(acid_dmg)
                self.log.add(
                    f"Acid splashes! ({acid_dmg} extra damage)",
                    (100, 200, 60)
                )
                # Also damages adjacent monsters (no friendly fire in original)
                for m in self._floor_monsters():
                    if m is monster:
                        continue
                    if abs(m.x - monster.x) <= 1 and abs(m.y - monster.y) <= 1:
                        m.take_damage(acid_dmg)
                        if m.is_dead():
                            self._kill_monster(m)
                if not p.alive:
                    self.death_cause = f"Dissolved by {monster.name}"

    def _boss_escape(self, monster: Monster):
        """Dark Wizard teleport-escape mechanic (original TDR behaviour).

        When the Wizard is reduced to 0 HP for the first or second time he
        teleports to a random floor tile rather than dying, restoring to 25%
        of max HP.  The third lethal hit triggers _kill_monster() normally.
        The log message is taken verbatim from the TDR v1.2.3 DATA_0 resource
        at offset 0x091b: "The Wizard disappeared! You hear a laugh and he
        is gone!"
        """
        lv  = self.level
        fov = self.fov
        p   = self.player

        # Collect open floor tiles outside the player's FOV and not occupied
        occupied = {(m.x, m.y) for m in self._floor_monsters() if m is not monster}
        occupied.add((p.x, p.y))
        candidates = [
            (x, y)
            for y in range(MAP_ROWS)
            for x in range(MAP_COLS)
            if lv.get(x, y) == T_FLOOR
            and not fov.is_visible(x, y)
            and (x, y) not in occupied
        ]

        if candidates:
            monster.x, monster.y = self.rng.choice(candidates)
        # else: nowhere to flee — stays in place (still doesn't die)

        monster.boss_escapes += 1
        # Restore to 25% max HP so the fight continues
        monster.hp    = max(1, monster.max_hp // 4)
        monster.alive = True   # take_damage() set this False — revive

        self.log.add(
            "The Wizard disappeared! You hear a laugh and he is gone!",
            (180, 100, 255)
        )

    def _kill_monster(self, monster: Monster):
        levelled = self.player.gain_xp(monster.xp)
        self.stat_xp_earned += monster.xp          # cumulative — feeds HoF glory
        self.monsters = [m for m in self.monsters if m is not monster]
        self.log.add(f"The {monster.name} is slain!  +{monster.xp} XP", C_XP)
        get_audio().play("kill_monster")
        if levelled:
            self.log.add(
                f"You reach level {self.player.level}! "
                f"HP +{max(1,4+self.player.mod(S_CON))}.",
                (180, 255, 180)
            )
            get_audio().play("level_up")
        # Gate Keeper kill: mark section cleared, unlock descent
        if "gate_keeper" in monster.special:
            barrier_floor = self._nearest_barrier_below()
            if barrier_floor:
                self.gk_sections_cleared.add(barrier_floor)
            self.log.add("Congratulations!!!", C_GOLD)
            self.log.add(
                "With the Gate Keeper dead you can continue your journey down.",
                C_GOLD
            )
            return
        # Boss kill: drop Orb of Carnos directly onto the corpse tile
        if "boss" in monster.special:
            orb = Item("orb_of_carnos", monster.x, monster.y)
            self.items.append(orb)
            self.log.add(
                "The Orb of Carnos falls from the Wizard's grasp!",
                C_GOLD
            )
            self.log.add(
                "Your journey back to the surface will be easy now.",
                C_GOLD
            )
            return   # no random loot on boss kill
        # Normal loot drop (CHA affects probability)
        cha_bonus = (self.player.charisma - 10) * 0.02
        if self.rng.random() < monster.loot_chance + cha_bonus:
            self._drop_loot(monster.x, monster.y)

    def _drop_loot(self, x: int, y: int):
        from data.items import items_by_category
        from constants import IC_POTION, IC_WEAPON, IC_SCROLL
        pool = (items_by_category(IC_POTION) +
                items_by_category(IC_SCROLL) +
                items_by_category(IC_WEAPON)[:4])
        if pool:
            chosen = self.rng.choice(pool)
            it = Item(chosen["id"], x, y)
            self.items.append(it)

    # ── Monster turns ─────────────────────────────────────────────────────────

    def _run_monster_turns(self):
        p        = self.player
        attracted = p.ring_monster_attraction
        plv      = p.level
        cha      = p.charisma
        fov      = self.fov

        for m in list(self._floor_monsters()):
            if not p.alive: break

            # Tick invisibility
            if getattr(m, "invisible", False):
                m._invis_turns = getattr(m, "_invis_turns", 0) - 1
                if m._invis_turns <= 0:
                    m.invisible = False
                    m._invis_turns = 0
                    self.log.add(f"The {m.name} reappears!", (200, 200, 200))
            # Tick charm
            if getattr(m, "charmed", False):
                m._charm_turns = getattr(m, "_charm_turns", 0) - 1
                if m._charm_turns <= 0:
                    m.charmed = False
                    self.log.add(f"The {m.name} looks angry again!", (200, 120, 80))

            dx   = p.x - m.x
            dy   = p.y - m.y
            dist = abs(dx) + abs(dy)

            # ── cold_aura: deals cold damage + applies slow when adjacent ─────
            # Fires regardless of the monster's action that turn.
            if "cold_aura" in m.special and dist <= 1:
                if not getattr(p, "resist_cold", False):
                    cold_dmg = self.rng.randint(1, 4)
                    p.take_damage(cold_dmg)
                    self.log.add(
                        f"The {m.name}'s icy aura chills you! ({cold_dmg} damage)",
                        (140, 200, 255)
                    )
                    # Apply slow status (2-4 turns)
                    if not getattr(p, "slowed", False):
                        p.slowed = True
                        p.status_turns["slowed"] = self.rng.randint(2, 4)
                        self.log.add("You are slowed by the cold!", (140, 180, 220))
                else:
                    self.log.add(f"The {m.name}'s aura washes over you harmlessly.", (140, 200, 255))
                if not p.alive:
                    self.death_cause = f"Frozen by {m.name}"
                    self.phase = PHASE_DEAD
                    self.log.add("You have died.", C_HP_LOW)
                    return

            # ── fire_breath: ranged fire cone when player in LOS ≤ 6 tiles ───
            # Takes the monster's action instead of a melee move/attack.
            if "fire_breath" in m.special and dist <= 6 and dist > 1:
                # Only fire if the player is visible from the monster's position
                from engine.fov import _ray_blocked
                if not _ray_blocked(self.level, m.x, m.y, p.x, p.y):
                    self._monster_fire_breath(m)
                    if not p.alive: return
                    continue   # action consumed — skip normal think()

            # ── necromancy: Evil Necromancer raises a nearby undead every 15 turns ──
            if "necromancy" in m.special:
                m._necro_timer = getattr(m, "_necro_timer", 0) + 1
                if m._necro_timer >= 15:
                    m._necro_timer = 0
                    self._necromancer_raise(m)

            result = m.think(p, self.level, attracted=attracted,
                              player_level=plv, cha_score=cha,
                              other_positions={
                                  (o.x, o.y) for o in self._floor_monsters()
                                  if o is not m
                              })
            if result and result[0] == "melee":
                self._monster_attacks(m)

            # ── scream: Banshee AoE stun on melee attack ─────────────────────
            if "scream" in m.special and result and result[0] == "melee":
                if self.rng.random() < 0.30 and p.alive:
                    self._banshee_scream(m)

    def _monster_fire_breath(self, monster: Monster):
        """Fire Lizard / Evil Cleric / Dark Wizard fire breath attack.

        Ranged fire cone.  Damage = 2d8 (≈9 avg); resisted by resist_fire.
        Player must be in LOS ≤ 6 tiles.  Cannot be blocked by AC.
        """
        p        = self.player
        base_dmg = sum(self.rng.randint(1, 8) for _ in range(2))
        if getattr(p, "resist_fire", False):
            self.log.add(
                f"The {monster.name} breathes fire!  Your resistance absorbs the blast.",
                (255, 180, 60)
            )
        else:
            p.take_damage(base_dmg)
            self.log.add(
                f"A burst of flame is released by the {monster.name}! ({base_dmg} damage)",
                (255, 120, 30)
            )
            if not p.alive:
                self.death_cause = f"Incinerated by {monster.name}"
                self.phase = PHASE_DEAD
                self.log.add("You have died.", C_HP_LOW)

    def _banshee_scream(self, banshee: Monster):
        """Banshee scream: AoE stun centred on the Banshee.

        All living entities within 3 tiles (player and other monsters) are
        stunned.  The Banshee itself is immune.
        """
        p     = self.player
        stun  = 2   # turns stunned

        # Stun the player
        if abs(p.x - banshee.x) + abs(p.y - banshee.y) <= 3:
            p.stunned = True
            p.status_turns["stunned"] = stun
            self.log.add(
                f"The {banshee.name} screams!  The sound stuns you!",
                (220, 220, 255)
            )

        # Also stun nearby monsters (they hear it too)
        for m in self._floor_monsters():
            if m is banshee:
                continue
            if abs(m.x - banshee.x) + abs(m.y - banshee.y) <= 3:
                m.sleeping = max(m.sleeping, stun)

    def _necromancer_raise(self, necromancer: Monster):
        """Evil Necromancer raises a low-level undead from nearby corpse tiles.

        Spawns a Sethron or Alligog (the two weakest monsters, used as
        'shambling corpses') adjacent to the necromancer on an open tile
        not occupied by the player or another monster.
        """
        from data.monsters import get_monster
        lv   = self.level
        p    = self.player

        # Find an open adjacent tile
        candidates = []
        for ddx in range(-2, 3):
            for ddy in range(-2, 3):
                tx, ty = necromancer.x + ddx, necromancer.y + ddy
                if not lv.is_in_bounds(tx, ty): continue
                if not lv.is_passable(tx, ty):  continue
                if (tx, ty) == (p.x, p.y):       continue
                if self._monster_at(tx, ty):      continue
                candidates.append((tx, ty))

        if not candidates:
            return

        tx, ty   = self.rng.choice(candidates)
        risen_id = self.rng.choice(["sethron", "alligog"])
        mdata    = get_monster(risen_id)
        n, s     = mdata["hp_dice"]
        hp       = max(1, sum(self.rng.randint(1, s) for _ in range(n)))
        risen    = Monster(risen_id, tx, ty, hp, hp)
        risen.provoked = True   # immediately hostile
        self.monsters.append(risen)
        self.log.add(
            f"The {necromancer.name} raises the dead!",
            (140, 60, 200)
        )

    # ── Pause / auto-pass ─────────────────────────────────────────────────────

    def toggle_pause(self):
        """Freeze or unfreeze the 5-second turn timer. No log message — silent."""
        active = (PHASE_PLAYING, PHASE_INVENTORY, PHASE_QUICK_USE,
                  PHASE_WAND_AIM, PHASE_THROW_AIM, PHASE_WISH)
        if self.phase not in active:
            return
        self.paused = not self.paused
        if self.paused:
            get_audio().pause_music()
        else:
            get_audio().resume_music()
            self.turn_reset_pending = True   # give player a fresh 5 seconds

    def auto_pass(self):
        """Timer expired with no player action — pass the turn (monsters act)."""
        if self.phase != PHASE_PLAYING or self.paused:
            return
        self.log.add("Pass.", C_TEXT_DIM)
        self._end_player_turn(AP_MOVE)

    # ── End of player turn ────────────────────────────────────────────────────

    def _end_player_turn(self, turns: int = AP_MOVE):
        """Advance the game by `turns` turns.
        Each consumed turn: status ticks once, monsters act once.
        HP regen fires every 5th turn (50 % chance of +1 HP).
        """
        p = self.player
        for _ in range(max(1, turns)):
            self.turn += 1
            self.turns_on_floor += 1
            self.dirty = True
            self.turn_reset_pending = True   # tell main loop to restart timer

            # ── Wandering monster check (every 10 turns) ──────────────────────
            if self.turns_on_floor % 10 == 0:
                self._try_wander_spawn()

            # ── Status ticks ──────────────────────────────────────────────────
            expired = p.tick_statuses()
            for e in expired:
                self.log.add(f"You are no longer {e}.")

            # ── Poison ────────────────────────────────────────────────────────
            if p.poisoned:
                dmg = p.poison_tick()
                if dmg:
                    self.log.add(f"Poison deals {dmg} damage.", C_HP_LOW)
                if not p.alive:
                    self.death_cause = "Succumbed to poison"

            # ── Starvation ────────────────────────────────────────────────────
            if p.starving:
                dmg = p.starvation_tick()
                if dmg:
                    self.log.add("You are starving!", C_HP_LOW)
                if not p.alive and not self.death_cause:
                    self.death_cause = "Starved to death"

            # ── HP regeneration ───────────────────────────────────────────────
            # Explorer: guaranteed regen every 5 turns (×2 normal rate)
            # Normal/Hero: 50% chance every 5 turns
            if self.turn % 5 == 0:
                if p.hp < p.max_hp:
                    if self.difficulty == DIFF_EXPLORER or self.rng.random() < 0.50:
                        p.heal(1)

            if not p.alive:
                self.phase = PHASE_DEAD
                self.log.add("You have died.", C_HP_LOW)
                return

            # ── Monsters act ──────────────────────────────────────────────────
            self._run_monster_turns()
            if not p.alive:
                # death_cause set by _monster_attacks inside _run_monster_turns
                self.phase = PHASE_DEAD
                self.log.add("You have died.", C_HP_LOW)
                return

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _monster_at(self, x: int, y: int) -> Optional[Monster]:
        for m in self._floor_monsters():
            if m.x == x and m.y == y:
                return m
        return None

    def _nearest_free_tile(self, lv, origin: tuple,
                            occupied: set) -> Optional[tuple]:
        """BFS outward from origin to find the nearest passable tile not in
        occupied. Returns None if the entire floor is full."""
        from collections import deque
        ox, oy = origin
        visited = {origin}
        queue   = deque([(ox, oy)])
        while queue:
            x, y = queue.popleft()
            if (x, y) not in occupied and lv.is_passable(x, y):
                return (x, y)
            for dx, dy in ((0,1),(0,-1),(1,0),(-1,0)):
                nx, ny = x+dx, y+dy
                if lv.is_in_bounds(nx, ny) and (nx,ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return None

    # ── Wandering monster spawner ─────────────────────────────────────────────

    #: Maximum extra monsters that can wander in during a single floor visit.
    WANDER_CAP = 5

    def _try_wander_spawn(self):
        """
        Called every 10 turns.  Rolls a chance to spawn one wandering monster
        from the eligible pool for the current floor, placed on an open tile
        outside the player's current FOV.

        Chance = 10% + floor//2 %  (e.g. floor 1 → 10%, floor 10 → 15%,
                                         floor 20 → 20%, floor 40 → 30%)
        Hard cap: WANDER_CAP wanderers per floor visit, regardless of time spent.
        """
        if self.wander_count >= self.WANDER_CAP:
            return

        chance = 0.10 + (self.floor // 2) / 100.0
        if self.rng.random() >= chance:
            return

        # Build weighted pool for this floor
        from data.monsters import weighted_monsters_for_floor
        pool = weighted_monsters_for_floor(self.floor)
        if not pool:
            return

        # Collect open floor tiles outside the player's FOV
        lv  = self.level
        fov = self.fov
        p   = self.player

        occupied = {(m.x, m.y) for m in self._floor_monsters()}
        occupied.add((p.x, p.y))

        candidates = []
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                if (lv.get(x, y) == T_FLOOR
                        and not fov.is_visible(x, y)
                        and (x, y) not in occupied):
                    candidates.append((x, y))

        if not candidates:
            return   # nowhere safe to place it

        mx, my = self.rng.choice(candidates)
        mdata  = self.rng.choice(pool)

        # Roll HP for the new monster
        count, sides = mdata["hp_dice"]
        hp = sum(self.rng.randint(1, sides) for _ in range(count))
        hp = max(1, hp)

        new_m = Monster(mdata["id"], mx, my, hp, hp)
        self.monsters.append(new_m)
        self.wander_count += 1

        # Subtle log — player hears it, doesn't see it
        self.log.add(f"You hear something moving in the dark…", C_TEXT_DIM)

    def _nearest_barrier_below(self) -> int:
        """Return the nearest GK barrier floor at or below current floor, or 0."""
        for bf in sorted(GK_BARRIER_FLOORS):
            if bf >= self.floor:
                return bf
        return 0

    def _gk_blocks_descent(self, next_floor: int) -> bool:
        """True when next_floor is a barrier and a Gate Keeper is alive here."""
        if next_floor not in GK_BARRIER_FLOORS:
            return False
        if next_floor in self.gk_sections_cleared:
            return False
        return any(
            m.id == "gate_keeper" and m.alive
            for m in self.monsters
        )

    def _maybe_spawn_gate_keeper(self):
        """Spawn a Gate Keeper near stair_down if this floor guards a barrier."""
        lv         = self.level
        next_floor = self.floor + 1
        if next_floor not in GK_BARRIER_FLOORS:
            return
        if next_floor in self.gk_sections_cleared:
            return
        if any(m.id == "gate_keeper" for m in self.monsters):
            return
        if lv.stair_down is None:
            return

        sx, sy     = lv.stair_down
        occupied   = {(m.x, m.y) for m in self.monsters}
        occupied.add((self.player.x, self.player.y))
        candidates = []
        for ddx in range(-2, 3):
            for ddy in range(-2, 3):
                tx, ty = sx + ddx, sy + ddy
                if not lv.is_in_bounds(tx, ty): continue
                if not lv.is_passable(tx, ty):  continue
                if (tx, ty) in occupied:         continue
                candidates.append((tx, ty))

        if not candidates:
            candidates = [
                t for t in lv.floor_tiles()
                if t not in occupied
            ]
        if not candidates:
            return

        gx, gy = self.rng.choice(candidates)

        hp_min, hp_max = GK_HP_TABLE.get(next_floor, (20, 40))
        hp = int(hp_min + (hp_max - hp_min) * self.rng.random())
        hp = max(1, hp)

        gk         = Monster("gate_keeper", gx, gy, hp, hp)
        gk.ac      = GK_AC_TABLE.get(next_floor, 0)
        atk, dmg_min, dmg_max = GK_ATK_TABLE.get(next_floor, (12, 8, 16))
        gk.atk        = atk
        gk.num_attacks = 3 if atk >= 22 else (2 if atk >= 15 else 1)
        gk.dmg_min    = dmg_min
        gk.dmg_max    = dmg_max
        self.monsters.append(gk)
        get_audio().play("gate_keeper")

    def _item_at(self, x: int, y: int) -> Optional[Item]:
        for it in self.items:
            if it.x == x and it.y == y:
                return it
        return None

    # ── Identification map (per run) ──────────────────────────────────────────

    def _build_id_map(self):
        """Assign randomised unidentified names to potions/scrolls/wands/rings."""
        from data.items import (POTION_COLORS, POTION_IDS,
                                SCROLL_NAMES,  SCROLL_IDS,
                                WAND_MATERIALS,WAND_IDS,
                                RING_GEMS,     RING_IDS)
        rng = random.Random(id(self) ^ self.rng.randint(0, 0xFFFFFF))
        self.id_map = {}

        colors = list(POTION_COLORS); rng.shuffle(colors)
        for i, pid in enumerate(POTION_IDS):
            self.id_map[pid] = f"{colors[i]} Potion"

        names = list(SCROLL_NAMES); rng.shuffle(names)
        for i, sid in enumerate(SCROLL_IDS):
            self.id_map[sid] = f"Scroll: {names[i]}"

        mats = list(WAND_MATERIALS); rng.shuffle(mats)
        for i, wid in enumerate(WAND_IDS):
            self.id_map[wid] = f"{mats[i]} Wand"

        gems = list(RING_GEMS); rng.shuffle(gems)
        for i, rid in enumerate(RING_IDS):
            self.id_map[rid] = f"{gems[i]} Ring"

    def _reshuffle_id_map(self):
        """Amnesia scroll — re-randomise all unidentified names."""
        self.identified.clear()
        self._build_id_map()

    def _apply_expert_identify(self, item_dict: dict):
        """
        Expert class identification on pickup — covers all expert categories.

        Wearables (Knight/Fighter/Jeweler — armor/weapon/ring):
          Assign a fuzzy enchant guess proportional to the expert stat.
          Accuracy = clamp(50 + (stat - 10) * 3, 65, 95) %

        Consumables (Sage/scrolls, Wizard/wands, Alchemist/potions):
          Roll identification proportional to INT (Sage), INT (Wizard), or
          INT (Alchemist).  Accuracy = clamp(50 + (INT - 10) * 3, 65, 95) %
          • SUCCESS  → add to self.identified, flag item["identified"]=True,
                       item["pending_confirm"]=False  (name shows cleanly).
          • FAILURE  → pick a random WRONG item_id from the same category,
                       store in item["fuzzy_id"], set item["pending_confirm"]=True
                       (display name will be "Wrong Name?").
        """
        from data.classes import CLASSES
        from data.items   import ITEMS
        from constants import (IC_WEAPON, IC_ARMOR, IC_RING,
                               IC_SCROLL, IC_WAND, IC_POTION,
                               S_INT, S_DEX, S_WIS)
        p          = self.player
        cls_entry  = CLASSES.get(p.class_key, {})
        cls_id_cat = cls_entry.get("identify", None)
        item_cat   = item_dict.get("cat", "")

        if cls_id_cat is None or item_cat != cls_id_cat:
            return

        # ── Determine governing stat and accuracy ────────────────────────────
        STAT_MAP = {
            IC_ARMOR:  S_DEX,   # Knight — DEX (armour feel)
            IC_WEAPON: S_DEX,   # Fighter — DEX
            IC_RING:   S_WIS,   # Jeweler — WIS (gem lore)
            IC_SCROLL: S_INT,   # Sage — INT
            IC_WAND:   S_INT,   # Wizard — INT
            IC_POTION: S_INT,   # Alchemist — INT
        }
        stat_idx  = STAT_MAP.get(cls_id_cat, S_INT)
        stat_val  = p.stats[stat_idx]
        accuracy  = min(0.95, max(0.65, 0.50 + (stat_val - 10) * 0.03))

        # ── Wearables: fuzzy enchant guess ───────────────────────────────────
        if cls_id_cat in (IC_WEAPON, IC_ARMOR, IC_RING):
            if item_dict.get("enchant_known", False):
                return
            real  = item_dict.get("enchant", 0)
            roll  = self.rng.random()
            if roll < accuracy:
                guess = real
            elif roll < accuracy + (1 - accuracy) / 2:
                guess = real - 1
            else:
                guess = real + 1
            item_dict["fuzzy_enchant"] = guess
            return

        # ── Consumables: identify with possible wrong name ───────────────────
        iid = item_dict.get("item_id", item_dict.get("id", ""))
        if iid in self.identified:
            return   # already known

        roll = self.rng.random()
        if roll < accuracy:
            # Correct identification
            item_dict["identified"]      = True
            item_dict["pending_confirm"] = False
            self.identified.add(iid)
        else:
            # Wrong identification: pick a random different item in same category
            same_cat = [i["id"] for i in ITEMS
                        if i.get("cat") == cls_id_cat and i["id"] != iid]
            if same_cat:
                wrong_id = self.rng.choice(same_cat)
                # Store fake display name from id_map or item name
                fake_name = self.id_map.get(wrong_id,
                            next((i["name"] for i in ITEMS if i["id"] == wrong_id),
                                 "Unknown"))
                item_dict["fuzzy_id"]        = wrong_id
                item_dict["fuzzy_name"]      = fake_name
                item_dict["pending_confirm"] = True

    def item_display_name(self, item: dict) -> str:
        """Return display name for an inventory dict item.
        - Unidentified consumables: show id_map alias (e.g. 'Blue Potion')
        - pending_confirm (wrong expert guess): show fuzzy_name + '?'
        - Correctly expert-identified (pending_confirm=False, identified=True):
          show true name cleanly
        - Enchant: '+N?' for fuzzy guess, '+N' when known exactly
        - Cursed tag: only after full identification
        """
        iid = item.get("item_id", item.get("id", ""))
        from constants import IC_POTION, IC_SCROLL, IC_WAND, IC_RING, IC_WEAPON, IC_ARMOR
        needs_id = {IC_POTION, IC_SCROLL, IC_WAND, IC_RING}

        # ── Base name ─────────────────────────────────────────────────────────
        if item.get("cat") in needs_id and iid not in self.identified:
            if item.get("pending_confirm"):
                # Expert gave a wrong name — show it with ?
                base = item.get("fuzzy_name", self.id_map.get(iid, item.get("name", "???"))) + "?"
            else:
                # Still fully unidentified — show shuffled alias
                base = self.id_map.get(iid, item.get("name", "???"))
        else:
            base = item.get("name", "???")

        # ── Enchant suffix ────────────────────────────────────────────────────
        enc = item.get("enchant", 0)
        if item.get("enchant_known", False):
            if enc > 0:  base += f" +{enc}"
            elif enc < 0: base += f" {enc}"
        elif "fuzzy_enchant" in item:
            fe = item["fuzzy_enchant"]
            if fe > 0:   base += f" +{fe}?"
            elif fe < 0: base += f" {fe}?"
            else:        base += " +0?"

        # ── Cursed tag ────────────────────────────────────────────────────────
        if item.get("cursed") and iid in self.identified and item.get("enchant_known", False):
            base += " {cursed}"
        return base

    # ── Item actions (called from inventory screen / game loop) ───────────────

    def use_item(self, item: dict) -> tuple:
        """Use/consume a potion, scroll, food, or wand.
        Logs a "You X the Y." prefix then returns (effect_msg, col)."""
        from engine.effects import apply_effect
        from constants import IC_FOOD, IC_POTION, IC_SCROLL, IC_WAND
        p        = self.player
        cat      = item.get("cat", "")
        original = item   # keep ref to inventory object before any copying

        # "You drink/read/eat/zap the <name>."
        _verbs = {IC_POTION: "drink", IC_SCROLL: "read",
                  IC_FOOD: "eat", IC_WAND: "zap"}
        verb = _verbs.get(cat, "use")
        nm   = self.item_display_name(original)
        self.log.add(f"You {verb} the {nm}.", (200, 200, 180))

        if cat == IC_FOOD:
            get_audio().play("eat_food")
            item = dict(item); item["effect"] = "eat"
        elif cat == IC_WAND:
            if item.get("charges", 0) <= 0:
                get_audio().play("wand_empty")
                return "The wand is empty.", (180, 60, 60)
            get_audio().play("zap_wand")
            self.begin_wand_aim(item)
            return "Choose a direction to fire the wand.", (220, 200, 100)
        elif cat == IC_POTION:
            effect = item.get("effect", "")
            if effect in ("confuse", "blind", "poison_drink"):
                get_audio().play("potion_bad")
            else:
                get_audio().play("drink_potion")
        elif cat == IC_SCROLL:
            get_audio().play("read_scroll")

        msg, col = apply_effect(self, item)

        # ── Confirm pending expert identification on use ───────────────────────
        # If the player used an item that had a fuzzy/wrong expert guess,
        # the actual effect reveals the true identity.
        iid = original.get("item_id", original.get("id", ""))
        if original.get("pending_confirm") and iid:
            original.pop("pending_confirm", None)
            original.pop("fuzzy_id",        None)
            original.pop("fuzzy_name",      None)
            original["identified"] = True
            self.identified.add(iid)
            self.log.add(f"You now know this was a {original.get('name','item')}!",
                         (210, 200, 120))

        # Remove consumables from inventory using the ORIGINAL reference
        if cat in (IC_FOOD, IC_POTION, IC_SCROLL):
            p.remove_from_inventory(original)

        # Wands stay in inventory until out of charges
        if cat == IC_WAND and item.get("charges", 0) <= 0:
            p.remove_from_inventory(original)

        # Action costs: scroll=2 turns, food=4 turns, everything else=1
        if cat == IC_SCROLL:
            self._end_player_turn(AP_SCROLL)
        elif cat == IC_FOOD:
            self._end_player_turn(AP_EAT)
        else:
            self._end_player_turn(AP_MOVE)   # potion, wand = 1 turn
        return msg, col

    def equip_item(self, item: dict) -> tuple:
        """Equip or unequip an item. Item stays in inventory. Returns (msg, col)."""
        p   = self.player
        cat = item.get("cat", "")
        from constants import IC_WEAPON, IC_ARMOR, IC_RING

        if cat not in (IC_WEAPON, IC_ARMOR, IC_RING):
            return "You can't equip that.", (180, 60, 60)

        slot = item.get("slot", "")

        # Throwing weapons → missile slot
        if slot == "throw":
            if p.equipped.get("missile") is item:
                p.equipped["missile"] = None
                return f"You unready the {item.get('name','missile')}.", (200,200,200)
            prev = p.equipped.get("missile")
            if prev and prev.get("cursed"):
                return "Your readied missile is cursed!", (200,40,40)
            p.equipped["missile"] = item
            self._end_player_turn()
            return f"You ready the {item.get('name','missile')}.", (220,200,120)

        # Ring: auto-assign to first empty ring finger
        if cat == IC_RING:
            if p.equipped.get("ring_l") is item or p.equipped.get("ring_r") is item:
                for rs in ("ring_l", "ring_r"):
                    if p.equipped[rs] is item:
                        p.equipped[rs] = None
                return f"You remove the {item.get('name','ring')}.", (200,200,200)
            for rs in ("ring_l", "ring_r"):
                if p.equipped[rs] is None:
                    p.equipped[rs] = item
                    self._end_player_turn()
                    return f"You put on the {item.get('name','ring')}.", (220,180,40)
            return "You have no free ring fingers.", (180,60,60)

        # Already equipped in this slot → unequip
        if p.equipped.get(slot) is item:
            if item.get("cursed"):
                get_audio().play("curse_blocked")
                return "It's cursed — you can't remove it!", (200,40,40)
            p.equipped[slot] = None
            get_audio().play("equip")
            return f"You remove the {item.get('name','item')}.", (200,200,200)

        # Unequip anything currently in that slot
        prev = p.equipped.get(slot)
        if prev and prev.get("cursed"):
            get_audio().play("curse_blocked")
            return "Your current item is cursed — you can't remove it!", (200,40,40)

        # ── Two-handed weapon rules ───────────────────────────────────────────
        # Equipping a two-handed weapon: force-unequip any offhand item first
        # (unless that offhand item is cursed — then block the equip entirely).
        if slot == "weapon" and item.get("hands", 1) == 2:
            offhand = p.equipped.get("offhand")
            if offhand is not None:
                if offhand.get("cursed"):
                    get_audio().play("curse_blocked")
                    return (
                        "You can't wield a two-handed weapon — "
                        "your offhand item is cursed!", (200, 40, 40)
                    )
                p.equipped["offhand"] = None
                self.log.add(
                    f"You stow the {offhand.get('name','offhand item')} "
                    f"to wield the {item.get('name','weapon')} with both hands.",
                    (200, 200, 180)
                )

        # Equipping an offhand item: blocked if a two-handed weapon is wielded
        if slot == "offhand":
            wpn = p.equipped.get("weapon")
            if wpn is not None and wpn.get("hands", 1) == 2:
                return (
                    f"You need both hands for the {wpn.get('name','weapon')} "
                    f"— you cannot use an offhand item.", (200, 140, 60)
                )

        p.equipped[slot] = item

        # Class expertise: reveal exact enchant immediately on equip
        from data.classes import CLASSES
        cls_identify = CLASSES.get(p.class_key, {}).get("identify", None)
        if cls_identify and item.get("cat") == cls_identify:
            item["enchant_known"] = True
            item.pop("fuzzy_enchant", None)   # exact known — discard guess
            # Expert classes also fully identify the item type
            iid2 = item.get("item_id", item.get("id", ""))
            self.identified.add(iid2)

        self._end_player_turn()
        nm = self.item_display_name(item)
        get_audio().play("equip")
        return f"You equip the {nm}.", (220,200,120)

    def drop_item(self, item: dict) -> tuple:
        """Remove item from inventory, place on floor. Returns (msg, col)."""
        p = self.player
        if item.get("cursed") and any(p.equipped.get(s) is item
                                       for s in p.equipped):
            return "It's cursed — you can't drop it!", (200,40,40)
        # Unequip if equipped
        for slot in list(p.equipped):
            if p.equipped[slot] is item:
                p.equipped[slot] = None
        p.remove_from_inventory(item)
        floor_item = Item(item["item_id"], p.x, p.y,
                          enchant=item.get("enchant", 0))
        # Copy identification state so it survives the drop→pickup cycle
        iid = item.get("item_id", item.get("id", ""))
        floor_item.id_state_identified      = iid in self.identified or item.get("identified", False)
        floor_item.id_state_enchant_known   = item.get("enchant_known", False)
        floor_item.id_state_fuzzy_enchant   = item.get("fuzzy_enchant", None)
        floor_item.id_state_fuzzy_id        = item.get("fuzzy_id", None)
        floor_item.id_state_fuzzy_name      = item.get("fuzzy_name", None)
        floor_item.id_state_pending_confirm = item.get("pending_confirm", False)
        self.items.append(floor_item)
        self._end_player_turn()
        nm = self.item_display_name(item)
        return f"You drop the {nm}.", (200,200,200)

    # ── Wand aiming ───────────────────────────────────────────────────────────────

    def begin_wand_aim(self, item: dict):
        """Enter PHASE_WAND_AIM with the given wand item pending direction."""
        from constants import IC_WAND
        if item.get("cat") != IC_WAND:
            return
        if item.get("charges", 0) <= 0:
            self.log.add("The wand is empty.", C_HP_LOW)
            return
        self.pending_wand = item
        self.phase = PHASE_WAND_AIM

    def aim_wand(self, dx: int, dy: int) -> tuple:
        """Fire pending_wand in direction (dx,dy). Returns (msg, col)."""
        from engine.effects import fire_wand_at_direction
        item = self.pending_wand
        if not item:
            return "No wand selected.", C_HP_LOW
        msg, col = fire_wand_at_direction(self, item, dx, dy)
        if item.get("charges", 0) <= 0:
            self.player.remove_from_inventory(item)
        self.pending_wand = None
        self.phase = PHASE_PLAYING
        self.log.add(msg, col)
        self._end_player_turn()
        return msg, col

    def begin_throw_aim(self, item: dict):
        """Enter PHASE_THROW_AIM with the given throw item pending direction."""
        from constants import IC_WEAPON
        if item.get("slot") != "throw":
            self.log.add("You can't throw that.", (180, 180, 180))
            return
        self.pending_throw = item
        self.phase = PHASE_THROW_AIM

    def aim_throw(self, dx: int, dy: int):
        """Fire pending_throw in direction (dx,dy)."""
        from engine.effects import throw_item_at_direction
        item = self.pending_throw
        if not item:
            return
        msg, col = throw_item_at_direction(self, item, dx, dy)
        self.pending_throw = None
        self.phase = PHASE_PLAYING
        self.log.add(msg, col)
        self._end_player_turn()

    # ── Pick-up (update to store full item dict) ──────────────────────────────

    def _restore_id_state(self, item_dict: dict, floor_item) -> bool:
        """If floor_item carries saved identification state (from a previous
        drop), copy it back into item_dict and skip re-identification.
        Returns True if state was restored, False if fresh identification needed.
        """
        has_identified     = getattr(floor_item, "id_state_identified",     False)
        has_enchant_known  = getattr(floor_item, "id_state_enchant_known",  False)
        has_fuzzy_enchant  = getattr(floor_item, "id_state_fuzzy_enchant",  None) is not None
        has_fuzzy_id       = getattr(floor_item, "id_state_fuzzy_id",       None) is not None

        # If none of the four id-state markers are set, this item has never been
        # touched by identification — let _apply_expert_identify() run fresh.
        if not has_identified and not has_enchant_known \
                and not has_fuzzy_enchant and not has_fuzzy_id:
            return False

        iid = item_dict.get("item_id", item_dict.get("id", ""))

        if has_identified:
            item_dict["identified"]    = True
            item_dict["enchant_known"] = has_enchant_known
            self.identified.add(iid)
        if has_enchant_known:
            item_dict["enchant_known"] = True
        if has_fuzzy_enchant:
            item_dict["fuzzy_enchant"] = getattr(floor_item, "id_state_fuzzy_enchant")
        if has_fuzzy_id:
            item_dict["fuzzy_id"]        = getattr(floor_item, "id_state_fuzzy_id")
            item_dict["fuzzy_name"]      = getattr(floor_item, "id_state_fuzzy_name", "???")
            item_dict["pending_confirm"] = getattr(floor_item, "id_state_pending_confirm", True)
        return True

    def pick_up_forced(self) -> int:
        """Pick up all items at the player's tile, ignoring pickup_mode.
        Returns the number of items picked up. Used by Inventory > Get an Item."""
        p    = self.player
        here = [it for it in self.items if it.x == p.x and it.y == p.y]
        count = 0
        for item in here:
            item_dict = item.to_dict()
            if p.add_to_inventory(item_dict):
                if not self._restore_id_state(item_dict, item):
                    self._apply_expert_identify(item_dict)
                self.items.remove(item)
                self._last_pickup.append(item_dict)
                nm = self.item_display_name(item_dict)
                self.log.add(f"You pick up: {nm}.", (210,175,45))
                get_audio().play("pickup")
                if p.overburdened:
                    self.log.add("You are overburdened! You cannot move.", C_HP_LOW)
                elif p.encumbered:
                    self.log.add("You are encumbered. Movement is slowed.", (200,160,60))
                count += 1
            else:
                wt = f"{p.carried_weight}/{p.carry_capacity}"
                self.log.add(f"Too heavy to carry! ({wt} wt)", (200,40,40))
                break
        if not here:
            self.log.add("There is nothing here to pick up.", (150,150,150))
        return count

    def _pick_up_items_v2(self, x: int, y: int):
        """Enhanced pickup — stores full item data dict in inventory."""
        if not self.pickup_mode:
            return
        p    = self.player
        here = [it for it in self.items if it.x == x and it.y == y]
        for item in here:
            item_dict = item.to_dict()
            if p.add_to_inventory(item_dict):
                if not self._restore_id_state(item_dict, item):
                    self._apply_expert_identify(item_dict)
                self.items.remove(item)
                self._last_pickup.append(item_dict)
                nm = self.item_display_name(item_dict)
                self.log.add(f"You pick up: {nm}.", (210,175,45))
                get_audio().play("pickup")
                if p.overburdened:
                    self.log.add("You are overburdened! You cannot move.", C_HP_LOW)
                elif p.encumbered:
                    self.log.add("You are encumbered. Movement is slowed.", (200,160,60))
            else:
                wt = f"{p.carried_weight}/{p.carry_capacity}"
                self.log.add(f"Too heavy to carry! ({wt} wt)", (200,40,40))
                break

    # ── Bulk drop helpers (Inventory menu) ────────────────────────────────────

    def drop_by_categories(self, cats: set) -> int:
        """Drop all inventory items whose category is in `cats`. Returns count."""
        p     = self.player
        count = 0
        for item in list(p.inventory):
            if item.get("cat","") in cats:
                # Unequip if needed
                for slot in list(p.equipped):
                    if p.equipped[slot] is item:
                        if item.get("cursed"):
                            continue   # can't drop cursed equipped items
                        p.equipped[slot] = None
                from entities.item import Item
                floor_item = Item(item["item_id"], p.x, p.y,
                                  enchant=item.get("enchant", 0))
                iid = item.get("item_id", item.get("id", ""))
                floor_item.id_state_identified      = iid in self.identified or item.get("identified", False)
                floor_item.id_state_enchant_known   = item.get("enchant_known", False)
                floor_item.id_state_fuzzy_enchant   = item.get("fuzzy_enchant", None)
                floor_item.id_state_fuzzy_id        = item.get("fuzzy_id", None)
                floor_item.id_state_fuzzy_name      = item.get("fuzzy_name", None)
                floor_item.id_state_pending_confirm = item.get("pending_confirm", False)
                self.items.append(floor_item)
                p.remove_from_inventory(item)
                count += 1
        if count:
            self.log.add(f"You drop {count} item(s).", (200,200,200))
            self._end_player_turn()
        return count

    def drop_all_items(self) -> int:
        """Drop everything in inventory (except cursed-equipped). Returns count."""
        from constants import (IC_WEAPON, IC_ARMOR, IC_POTION, IC_SCROLL,
                                IC_WAND, IC_RING, IC_FOOD, IC_JEWEL, IC_MISC)
        all_cats = {IC_WEAPON, IC_ARMOR, IC_POTION, IC_SCROLL,
                    IC_WAND, IC_RING, IC_FOOD, IC_JEWEL, IC_MISC}
        return self.drop_by_categories(all_cats)

    def drop_last_pickup(self) -> int:
        """Drop the most recently auto-picked-up item. Returns count."""
        p = self.player
        if not self._last_pickup:
            self.log.add("Nothing to put back.", (150,150,150))
            return 0
        item = self._last_pickup.pop()
        if item not in p.inventory:
            self.log.add("Item no longer in inventory.", (150,150,150))
            return 0
        msg, col = self.drop_item(item)
        self.log.add(msg, col)
        return 1
