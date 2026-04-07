# entities/monster.py
# Monster entity with full hostility system.

import random
from typing import Optional, Tuple
from data.monsters import get_monster
from constants import (
    HOSTILITY_AFRAID, HOSTILITY_NEUTRAL, HOSTILITY_CAUTIOUS, HOSTILITY_HOSTILE,
    cha_hostility_mod, MAP_COLS, MAP_ROWS,
)

# Tags that always force HOSTILE regardless of CHA / level adjustments
_FORCED_HOSTILE_TAGS = {"undead", "boss"}


class Monster:
    def __init__(self, monster_id: str, x: int, y: int, hp: int, max_hp: int):
        self.id      = monster_id
        data         = get_monster(monster_id)
        self.name    = data["name"]
        self.glyph   = data["glyph"]
        self.ac          = data["ac"]
        self.atk         = data["atk"]    # used for hit-chance roll in _monster_attacks()
        self.num_attacks = data.get("num_attacks", 1)  # attacks per turn
        self.dmg_min, self.dmg_max = data["damage"]
        self.xp      = data["xp"]
        self.speed   = data["speed"]
        self.special = list(data["special"])
        self.loot_chance = data["loot_chance"]
        self.color   = data["color_hint"]
        self.min_floor = data["min_floor"]

        # Hostility
        self.base_hostility: int = data.get("base_hostility", HOSTILITY_HOSTILE)
        # Undead and bosses are always hostile regardless of player stats
        if any(tag in self.special for tag in _FORCED_HOSTILE_TAGS):
            self.base_hostility = HOSTILITY_HOSTILE
        self.provoked: bool  = False   # set True when player hits the monster
        self.fear_turns: int = 0       # remaining turns of forced AFRAID state
        self.charmed: bool   = False   # pacified by scroll of charm

        # Current effective hostility (updated each think() — readable by renderer)
        self.current_hostility: int = self.base_hostility

        self.x   = x
        self.y   = y
        self.hp  = hp
        self.max_hp = max_hp

        self.alive    = True
        self.asleep   = False       # legacy flag
        self.slowed   = False       # from wand of slow
        self.sleeping = 0           # turns of sleep remaining (wand_sleep)
        self.invisible = False      # hidden from view (wand_invisibility)
        self._invis_turns = 0
        self._speed_acc = 0         # accumulator for fractional speed

        # Boss-specific state
        self.boss_escapes: int = 0  # times this monster has teleported away (boss_escape tag)

        self.rng = random.Random()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def hp_pct(self): return self.hp / self.max_hp if self.max_hp > 0 else 0

    def is_dead(self): return self.hp <= 0

    # ── Hostility calculation ─────────────────────────────────────────────────

    def effective_hostility(self, player_level: int, cha_score: int,
                             attracted: bool) -> int:
        """
        Compute effective hostility this turn.

        Priority order (highest wins):
          1. Ring of Monster Attraction  → always HOSTILE
          2. fear_turns > 0             → always AFRAID
          3. Charmed                    → always NEUTRAL
          4. Provoked                   → always HOSTILE (player attacked this monster)
          5. Forced hostile tags (undead/boss) → HOSTILE floor for CHA / level
          6. Base hostility adjusted by CHA mod and player/monster level gap

        CHA modifier:
          CHA ≥ 22 → -1 step (friendlier)
          CHA  9-21 → 0
          CHA ≤  8 → +1 step (more hostile)

        Level gap (player_level − monster_equiv_level):
          gap ≥ 4 → -1 step (monsters respect power)
          gap ≥ 8 → -2 steps (monsters flee from much stronger foe)
        """
        if attracted:
            return HOSTILITY_HOSTILE
        if self.fear_turns > 0:
            return HOSTILITY_AFRAID
        if self.charmed:
            return HOSTILITY_NEUTRAL
        if self.provoked:
            return HOSTILITY_HOSTILE

        # Undead / boss: ignore CHA and level; always HOSTILE
        if any(tag in self.special for tag in _FORCED_HOSTILE_TAGS):
            return HOSTILITY_HOSTILE

        # Monster equivalent level based on min_floor
        mon_equiv_level = max(1, self.min_floor // 3 + 1)
        level_gap = player_level - mon_equiv_level

        h = self.base_hostility

        # CHA adjustment
        h += cha_hostility_mod(cha_score)

        # Level gap — powerful player intimidates monsters
        if level_gap >= 8:
            h -= 2
        elif level_gap >= 4:
            h -= 1

        # Clamp to valid range
        return max(HOSTILITY_AFRAID, min(HOSTILITY_HOSTILE, h))

    # ── Action / speed ────────────────────────────────────────────────────────

    def act_this_turn(self) -> bool:
        """Fast monsters act every turn; slow ones every other turn."""
        if "slow" in self.special and not self.slowed:
            self._speed_acc += 1
            if self._speed_acc < 2:
                return False
            self._speed_acc = 0
        return True

    # ── AI ────────────────────────────────────────────────────────────────────

    def think(self, player, level, attracted: bool = False,
              player_level: int = 1, cha_score: int = 13,
              other_positions: set = None) -> "Optional[Tuple]":
        """
        Decide action based on effective hostility.

        Returns:
          ("melee",)          — attack adjacent player
          ("move", nx, ny)    — step toward or away from player
          None                — no action (sleeping, out of range, neutral)
        """
        if not self.act_this_turn():
            return None

        # Sleep check: skip turn, decrement counter
        if self.sleeping > 0:
            self.sleeping -= 1
            return None

        # Fear countdown
        if self.fear_turns > 0:
            self.fear_turns -= 1

        eff = self.effective_hostility(player_level, cha_score, attracted)
        self.current_hostility = eff   # cache for renderer

        dx = player.x - self.x
        dy = player.y - self.y
        dist = abs(dx) + abs(dy)

        occupied = other_positions or set()

        # ── AFRAID — run away ────────────────────────────────────────────────
        if eff == HOSTILITY_AFRAID:
            return self._flee(player, level, occupied)

        # ── NEUTRAL — ignore player ───────────────────────────────────────────
        if eff == HOSTILITY_NEUTRAL:
            return None

        # ── CAUTIOUS — attack if within 5 tiles ──────────────────────────────
        if eff == HOSTILITY_CAUTIOUS:
            if dist == 1:
                return ("melee",)
            if dist <= 5:
                return self._step_toward(player, level, occupied)
            return None

        # ── HOSTILE — chase from up to 15 tiles ──────────────────────────────
        if dist == 1:
            return ("melee",)
        chase_range = 999 if attracted else 15
        if dist <= chase_range:
            return self._step_toward(player, level, occupied)

        return None

    def _step_toward(self, player, level, occupied: set = None) -> "Optional[Tuple]":
        occupied = occupied or set()
        dx = player.x - self.x
        dy = player.y - self.y
        sx = (1 if dx > 0 else -1) if dx != 0 else 0
        sy = (1 if dy > 0 else -1) if dy != 0 else 0
        for (ox, oy) in ((sx, sy), (sx, 0), (0, sy)):
            nx, ny = self.x + ox, self.y + oy
            if (level.is_passable(nx, ny)
                    and (nx, ny) != (player.x, player.y)
                    and (nx, ny) not in occupied):
                self.x, self.y = nx, ny
                return ("move", nx, ny)
        return None

    def _flee(self, player, level, occupied: set = None) -> "Optional[Tuple]":
        """Move away from the player, preferring tiles further away."""
        occupied = occupied or set()
        dx = player.x - self.x
        dy = player.y - self.y
        sx = (-1 if dx > 0 else 1) if dx != 0 else 0
        sy = (-1 if dy > 0 else 1) if dy != 0 else 0
        candidates = [(sx, sy), (sx, 0), (0, sy), (-sx, 0), (0, -sy)]
        for (ox, oy) in candidates:
            nx, ny = self.x + ox, self.y + oy
            if (0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS
                    and level.is_passable(nx, ny)
                    and (nx, ny) != (player.x, player.y)
                    and (nx, ny) not in occupied):
                self.x, self.y = nx, ny
                return ("move", nx, ny)
        return None

    # ── Combat ────────────────────────────────────────────────────────────────

    def take_damage(self, amount: int) -> int:
        amount = max(0, amount)
        self.hp -= amount
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        # Getting hit instantly provokes and wakes
        if amount > 0:
            self.provoked = True
            if self.sleeping > 0:
                self.sleeping = 0
            if self.charmed:
                self.charmed = False
        return amount
