# entities/player.py
# The player character — full D&D attribute system ready for all 10 steps.

import random
from typing import Optional, List, Dict
from constants import (
    S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA,
    STAT_NAMES, STAT_MAX,
    FOOD_MAX, FOOD_START, FOOD_PER_MOVE, FOOD_STARVE, FOOD_STUFFED,
    XP_BASE, XP_GROWTH,
    HP_PER_CON_POINT,
    FOV_RADIUS_BASE,
)


class Player:
    def __init__(self, name: str, class_key: str, stats: List[int], base_hp: int):
        # Identity
        self.name      = name
        self.class_key = class_key

        # Position (set by GameState on floor load)
        self.x: int = 0
        self.y: int = 0

        # D&D attributes [STR, INT, WIS, DEX, CON, CHA]
        self.stats: List[int] = list(stats)

        # HP — base_hp + CON modifier
        con_bonus   = max(0, self.stats[S_CON] - 10)
        self.max_hp = base_hp + con_bonus
        self.hp     = self.max_hp

        # Levels & XP
        self.level   = 1
        self.xp      = 0
        self.xp_next = XP_BASE

        # Gold
        self.gold = 0

        # Food meter
        self.food     = FOOD_START
        self.starving  = False
        self.stuffed   = False    # food >= FOOD_STUFFED → movement penalty

        # Status effects (Step 3+)
        self.poisoned    = False
        self.confused    = False    # movement directions randomised
        self.blinded     = False    # FOV radius = 1
        self.hasted      = False    # acts twice per turn
        self.invisible   = False    # monsters can't see player
        self.levitating  = False    # can't melee attack
        self.resist_fire = False
        self.resist_cold = False
        self.protected   = False    # can't be hit
        self.stunned     = False    # head_smash / scream: player loses next turn
        self.slowed      = False    # cold_aura contact: movement skips every other step
        self.status_turns: Dict[str, int] = {}   # effect → turns remaining

        # Equipment slots (Step 4)
        self.equipped: Dict[str, Optional[dict]] = {
            "weapon":    None,
            "offhand":   None,
            "armor":     None,
            "cloak":     None,
            "helmet":    None,
            "gauntlets": None,
            "ring_l":    None,
            "ring_r":    None,
            "missile":   None,   # throwing items (rocks, darts, javelins…)
        }

        # Inventory (Step 4): list of item dicts
        self.inventory: List[dict] = []

        # State flags
        self.alive = True
        self.won   = False

        self.rng = random.Random()

    # ── Stat accessors ────────────────────────────────────────────────────────

    def stat(self, idx: int) -> int:
        return self.stats[idx]

    def mod(self, idx: int) -> int:
        """D&D-style modifier: (stat - 10) // 2"""
        return (self.stats[idx] - 10) // 2

    @property
    def strength(self):     return self.stats[S_STR]
    @property
    def intelligence(self): return self.stats[S_INT]
    @property
    def wisdom(self):       return self.stats[S_WIS]
    @property
    def dexterity(self):    return self.stats[S_DEX]
    @property
    def constitution(self): return self.stats[S_CON]
    @property
    def charisma(self):     return self.stats[S_CHA]

    # ── Derived values ────────────────────────────────────────────────────────

    @property
    def fov_radius(self) -> int:
        if self.blinded:
            return 1
        bonus = 1 if any(
            s and s.get("effect") == "light" for s in self.equipped.values()
        ) else 0
        return FOV_RADIUS_BASE + bonus

    @property
    def xray_vision(self) -> bool:
        """True when Ring of X-Ray is equipped — FOV ignores walls."""
        return any(
            r and r.get("effect") == "ring_xray"
            for r in (self.equipped.get("ring_l"), self.equipped.get("ring_r"))
        )

    @property
    def ring_slowed(self) -> bool:
        """True when Ring of Slowness is equipped."""
        return any(
            r and r.get("effect") == "ring_slowness"
            for r in (self.equipped.get("ring_l"), self.equipped.get("ring_r"))
        )

    @property
    def ring_monster_attraction(self) -> bool:
        """True when Ring of Monster Attraction is equipped."""
        return any(
            r and r.get("effect") == "ring_monster"
            for r in (self.equipped.get("ring_l"), self.equipped.get("ring_r"))
        )

    @property
    def ring_hunger_drain(self) -> int:
        """Extra food consumed per move from powerful always-on rings.
        Each ring_xray or ring_regen equipped adds 1 extra hunger/move.
        Jeweler class is immune (returns 0)."""
        if self.class_key == "jeweler":
            return 0
        hungry_effects = {"ring_xray", "ring_regen"}
        return sum(
            1 for r in (self.equipped.get("ring_l"), self.equipped.get("ring_r"))
            if r and r.get("effect") in hungry_effects
        )

    @property
    def armor_class(self) -> int:
        """AC = 10 - sum(base_ac+enchant for all armor slots) - DEX_mod."""
        base = 10
        for slot in ("armor", "cloak", "offhand", "helmet", "gauntlets"):
            item = self.equipped.get(slot)
            if item and item.get("cat") == "armor":
                base -= item.get("base_ac", 0) + item.get("enchant", 0)
        for rs in ("ring_l", "ring_r"):
            r = self.equipped.get(rs)
            if r and r.get("effect") == "ring_protect":
                base -= 1
        base -= self.mod(S_DEX)
        return base

    @property
    def attack_bonus(self) -> int:
        """To-hit bonus: level + STR mod + equipped weapon enchant."""
        base = self.level + self.mod(S_STR)
        wpn  = self.equipped.get("weapon")
        if wpn:
            base += wpn.get("enchant", 0)
        return base

    @property
    def damage_bonus(self) -> int:
        """Flat damage added to every weapon roll.
        Requires STR ≥ 13 to contribute — STR 12 and below gives +0.
        This prevents starting martial classes from trivialising early combat
        via their stat bonus alone; players must invest in STR gear to push dmg.
        Negative STR still penalises damage (min bonus = STR modifier clamped ≥ -3).
        """
        raw = self.mod(S_STR)
        if raw > 0:
            # Positive: only kicks in from STR 13 (mod=1 at old formula, now +0)
            # New: treat STR modifier as (STR - 12) // 2  for positive range only
            return max(0, (self.stats[S_STR] - 12) // 2)
        return max(-3, raw)   # negative: cap penalty at -3

    @property
    def weapon_damage_range(self) -> tuple:
        """Return (n_dice, faces, enchant) for the equipped weapon, or unarmed.
        Enchant adds to each die face: a +1 Dagger rolls 1d5 instead of 1d4."""
        wpn = self.equipped.get("weapon")
        if wpn:
            n, d = wpn.get("dmg_dice", (1, wpn.get("base_dmg", 4)))
            enc  = wpn.get("enchant", 0) if wpn.get("enchant_known", True) else wpn.get("enchant", 0)
            return (n, max(1, d + enc))
        return (1, 4)   # unarmed: 1d4

    @property
    def hp_pct(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0

    @property
    def food_pct(self) -> float:
        return self.food / FOOD_MAX

    @property
    def xp_pct(self) -> float:
        return self.xp / self.xp_next if self.xp_next > 0 else 1.0

    @property
    def can_dual_wield(self) -> bool:
        return self.strength >= 16 and self.dexterity >= 18

    # ── HP management ─────────────────────────────────────────────────────────

    def heal(self, amount: int) -> int:
        healed = min(amount, self.max_hp - self.hp)
        self.hp = min(self.max_hp, self.hp + healed)
        return healed

    def take_damage(self, amount: int) -> int:
        amount = max(0, amount)
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return amount

    def drain_max_hp(self, amount: int):
        """Vampire drain — reduces max HP permanently."""
        self.max_hp = max(1, self.max_hp - amount)
        self.hp     = min(self.hp, self.max_hp)
        if self.hp <= 0:
            self.alive = False

    # ── Food ──────────────────────────────────────────────────────────────────

    def consume_food(self, amount: int = FOOD_PER_MOVE):
        self.food = max(0, self.food - amount)
        self.starving = self.food <= FOOD_STARVE
        self.stuffed  = self.food >= FOOD_STUFFED

    def eat(self, food_amount: int) -> str:
        if self.food >= FOOD_MAX:
            return "You can't eat another bite!"
        was_stuffed = self.food >= FOOD_STUFFED
        added  = min(food_amount, FOOD_MAX - self.food)
        self.food += added
        self.starving = False
        self.stuffed  = self.food >= FOOD_STUFFED
        if not was_stuffed and self.stuffed:
            return "You're stuffed!"
        return ""

    # ── XP & Level ───────────────────────────────────────────────────────────

    def gain_xp(self, amount: int) -> bool:
        """Returns True if the player levelled up."""
        self.xp += amount
        if self.xp >= self.xp_next:
            self._level_up()
            return True
        return False

    def _level_up(self):
        self.level   += 1
        self.xp      -= self.xp_next
        self.xp_next  = int(self.xp_next * XP_GROWTH)
        # CON-based HP gain
        hp_gain     = max(1, 4 + self.mod(S_CON))
        self.max_hp += hp_gain
        self.hp      = min(self.hp + hp_gain, self.max_hp)

    def drain_level(self) -> bool:
        """Banshee level_drain: reduce player level by 1 (minimum 1).

        Reverses one level-up: decrements level, recalculates xp_next back one
        step, clamps current xp, and removes the HP that level granted.
        Returns True if the drain took effect, False if already level 1.
        """
        if self.level <= 1:
            return False
        hp_loss      = max(1, 4 + self.mod(S_CON))
        self.level  -= 1
        self.xp_next = max(XP_BASE, int(self.xp_next / XP_GROWTH))
        self.xp      = min(self.xp, self.xp_next - 1)
        self.max_hp  = max(1, self.max_hp - hp_loss)
        self.hp      = min(self.hp, self.max_hp)
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return True

    # ── Status effects ────────────────────────────────────────────────────────

    def apply_status(self, effect: str, turns: int):
        setattr(self, effect, True)
        self.status_turns[effect] = turns

    def tick_statuses(self) -> List[str]:
        """Decrement timers; return list of effects that expired this turn."""
        expired = []
        for effect in list(self.status_turns):
            self.status_turns[effect] -= 1
            if self.status_turns[effect] <= 0:
                del self.status_turns[effect]
                setattr(self, effect, False)
                expired.append(effect)
        return expired

    def poison_tick(self) -> int:
        if self.poisoned:
            return self.take_damage(1)
        return 0

    def starvation_tick(self) -> int:
        if self.starving:
            return self.take_damage(1)
        return 0

    # ── Stat modification (potions, scrolls, etc.) ───────────────────────────

    def modify_stat(self, idx: int, delta: int) -> int:
        old = self.stats[idx]
        self.stats[idx] = max(1, min(STAT_MAX, self.stats[idx] + delta))
        # CON change affects max HP
        if idx == S_CON and delta > 0:
            gain = delta * HP_PER_CON_POINT
            self.max_hp += gain
            self.hp = min(self.hp + gain, self.max_hp)
        return self.stats[idx] - old  # actual change

    # ── Inventory / weight helpers ────────────────────────────────────────────

    @property
    def carry_capacity(self) -> int:
        """Max carry weight before penalty. Scales with STR: 30 + STR*5."""
        return 30 + self.stats[S_STR] * 5

    @property
    def carried_weight(self) -> int:
        """Total weight of everything in inventory."""
        return sum(it.get("weight", 0) for it in self.inventory)

    @property
    def encumbrance_ratio(self) -> float:
        """carried_weight / carry_capacity (1.0 = at limit)."""
        cap = self.carry_capacity
        return self.carried_weight / cap if cap else 0.0

    @property
    def encumbered(self) -> bool:
        """True when >110% of carry capacity — movement slowed (every other step)."""
        return self.encumbrance_ratio > 1.10

    @property
    def overburdened(self) -> bool:
        """True when >130% of carry capacity — movement blocked entirely."""
        return self.encumbrance_ratio > 1.30

    def can_carry(self, item_weight: int = 0) -> bool:
        """True if player can pick up an item of the given weight.
        Allows pickup up to 130% cap (overburdened threshold)."""
        return (self.carried_weight + item_weight) <= self.carry_capacity * 1.30

    def add_to_inventory(self, item: dict) -> bool:
        w = item.get("weight", 0)
        if not self.can_carry(w):
            return False
        self.inventory.append(item)
        return True

    def remove_from_inventory(self, item: dict):
        if item in self.inventory:
            self.inventory.remove(item)

    # ── String representations ────────────────────────────────────────────────

    def stat_line(self) -> str:
        parts = [f"{STAT_NAMES[i]}:{self.stats[i]:2d}" for i in range(6)]
        return "  ".join(parts)

    def status_summary(self) -> List[str]:
        flags = []
        if self.overburdened: flags.append("OVERBURDENED")
        elif self.encumbered: flags.append("ENCUMBERED")
        if self.stuffed:     flags.append("STUFFED")
        if self.starving:    flags.append("STARVING")
        if self.poisoned:    flags.append("POISONED")
        if self.confused:    flags.append("CONFUSED")
        if self.blinded:     flags.append("BLIND")
        if self.hasted:      flags.append("HASTED")
        if self.invisible:   flags.append("INVISIBLE")
        if self.levitating:  flags.append("LEVITATING")
        if self.protected:   flags.append("PROTECTED")
        if self.resist_fire: flags.append("RESIST FIRE")
        if self.resist_cold: flags.append("RESIST COLD")
        if self.stunned:     flags.append("STUNNED")
        if self.slowed:      flags.append("SLOWED")
        return flags
