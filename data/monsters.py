# data/monsters.py
# ─────────────────────────────────────────────────────────────────────────────
# Full monster roster — all 42 original creatures from The Dungeon Revealed
# (John Raymonds / Woodrose Editions, 1985–1988).
#
# DATA SOURCES (in priority order):
#   1. Observed gameplay  — player-confirmed floor ranges (highest confidence)
#   2. DoD V4.0 binary    — earlier version, correctly ordered monster table
#   3. TDR v1.2.3 binary  — primary game; stats confirmed accurate, but level
#                           fields for monsters #13–28 are shifted +1 in the
#                           data block (a corruption absent in V4.0).
#
# KNOWN UNCERTAINTIES:
#   Monsters marked † have level ranges from TDR binary only (floors 16+ not
#   yet reached in playtesting). These may need adjustment after further play.
#
# ─────────────────────────────────────────────────────────────────────────────
# MONSTER POWER SCALING
# ─────────────────────────────────────────────────────────────────────────────
#
#   MONSTER_POWER  — single global dial, default 1.0 (authentic TDR balance).
#
#   Values below 1.0 make the game easier; above 1.0 harder.
#   Examples:
#       0.5  — half HP, half damage, half XP    (very easy)
#       0.75 — gentle nerf                      (easy)
#       1.0  — authentic TDR balance            (default)
#       1.25 — slightly beefier monsters        (hard)
#       1.5  — significantly tougher            (very hard)
#
#   Only HP, damage, and XP are scaled — AC, floor ranges, special attacks,
#   and spawn frequencies are left untouched so the game feel stays authentic.
#
# ─────────────────────────────────────────────────────────────────────────────
# MONSTER POWER SCALING — three independent dials
# ─────────────────────────────────────────────────────────────────────────────
#
#   MONSTER_HP_POWER   — how many hits monsters can absorb before dying.
#                        Raise this to make monsters harder to kill.
#                        Default 2.5 = monsters have 2.5× their TDR base HP.
#
#   MONSTER_DMG_POWER  — damage output and hit-chance multiplier.
#                        Raise this to make each hit hurt more.
#                        Default 1.3 = 30% more damage than authentic TDR.
#
#   MONSTER_XP_POWER   — XP reward per kill.
#                        Reduce this to slow player level progression.
#                        Default 0.4 = monsters give 40% of TDR authentic XP.
#
#   Only HP, damage, and XP are scaled — AC, floor ranges, atk hit chance,
#   special attacks, and spawn frequencies are left untouched.
#
#   Legacy alias MONSTER_POWER kept at 1.0 so any external reference compiles.
#
MONSTER_POWER:     float = 1.0   # legacy alias — do not use for new code
MONSTER_HP_POWER:  float = 2.0   # tanky but less grindy than 2.5
MONSTER_DMG_POWER: float = 1.5   # calibrated for hybrid AC system
MONSTER_XP_POWER:  float = 0.3   # harder kills = slower levelling

from constants import HOSTILITY_HOSTILE, HOSTILITY_CAUTIOUS, HOSTILITY_NEUTRAL


# ── Scaling helpers ───────────────────────────────────────────────────────────

def _scale_hp(base: int) -> int:
    """Scale base HP by MONSTER_HP_POWER, minimum 1."""
    return max(1, round(base * MONSTER_HP_POWER))


def _scale_dmg(base: int) -> int:
    """Scale flat damage value by MONSTER_DMG_POWER, minimum 1."""
    return max(1, round(base * MONSTER_DMG_POWER))


def _scale_xp(base: int) -> int:
    """Scale XP reward by MONSTER_XP_POWER, minimum 1."""
    return max(1, round(base * MONSTER_XP_POWER))


def _hp_dice(base_hp: int):
    """
    Convert a flat HP value into a (count, sides) dice pair, scaled by
    MONSTER_HP_POWER.  Uses d8s where possible (classic Rogue convention).
    """
    scaled = _scale_hp(base_hp)
    count = max(1, round(scaled / 4.5))
    sides = max(2, round((scaled / count) * 2 - 1))
    return (count, sides)


def _dmg_dice(base_dmg: int):
    """
    Convert a flat base damage value into a (dmg_min, dmg_max) range for
    randint(), scaled by MONSTER_DMG_POWER.

    Returns a flat [min, max] pair where:
      dmg_min = ~40% of scaled value (reasonable floor)
      dmg_max = scaled value (ceiling)

    Previously this returned (count, sides) dice notation which caused a crash
    when count > sides (e.g. Caveman with high base_dmg at 1.5× power produced
    count=11, sides=6 → randint(11, 6) → ValueError).
    """
    scaled  = _scale_dmg(base_dmg)
    dmg_min = max(1, round(scaled * 0.4))
    dmg_max = max(dmg_min + 1, scaled)
    return (dmg_min, dmg_max)


# ── Special-attack tag constants (documented here for engine reference) ──────
#
#   "cold_aura"       — aura damages and slows player on contact
#   "fire_breath"     — ranged fire cone on attack
#   "immune_fire"     — takes no fire damage
#   "immune_cold"     — takes no cold damage
#   "confuse"         — chance to confuse player on hit
#   "stat_drain"      — drains a random stat on hit (Amadon)
#   "acid_splash"     — splashes adjacent tiles with acid (Black Pudding)
#   "head_smash"      — chance to stun player (Reaper)
#   "necromancy"      — raises nearby corpses as monsters (Evil Necromancer)
#   "level_drain"     — reduces player XP level (Banshee)
#   "scream"          — AOE stun on nearby player (Banshee)
#   "boss"            — unique, drops Orb of Carnos, triggers endgame on kill


# ─────────────────────────────────────────────────────────────────────────────
# Internal builder — keeps the table below compact
# ─────────────────────────────────────────────────────────────────────────────

def _m(id, name, glyph, icon_id,
       min_floor, max_floor,
       base_hp, ac, atk, base_dmg,
       base_xp, speed,
       special, spawn_freq,
       loot_chance, color_hint,
       base_hostility,
       hp_fixed=None):
    """Build a monster data dict.

    hp_fixed: if not None, the monster always spawns with exactly
    round(hp_fixed * MONSTER_POWER) HP instead of rolling hp_dice.
    Used for scripted bosses whose HP is a fixed value in the original
    binary (Dark Wizard = 800 HP per TDR v1.2.3 data block, offset 0xc2a6).
    hp_dice is still stored for MONSTER_POWER scaling display purposes.
    """
    return {
        "id":             id,
        "name":           name,
        "glyph":          glyph,
        "icon_id":        icon_id,
        "min_floor":      min_floor,
        "max_floor":      max_floor,
        "hp_dice":        _hp_dice(base_hp),
        "hp_fixed":       round(hp_fixed * MONSTER_HP_POWER) if hp_fixed is not None else None,
        "ac":             ac,
        "atk":            atk,
        # num_attacks: derived from atk value — only truly elite monsters attack
        # multiple times per turn. Thresholds chosen so most floor 1–12 monsters
        # attack once; high-tier threats (Fire Lizard, Dark Wizard etc.) twice or
        # three times.
        #   atk  1–19 → 1 attack   (nearly all normal monsters)
        #   atk 20–24 → 2 attacks  (Caveman, Fire Lizard, Banshee level threats)
        #   atk 25+   → 3 attacks  (Air Devil, Evil Necromancer, Dark Wizard)
        "num_attacks":    3 if atk >= 25 else (2 if atk >= 20 else 1),
        "damage":         _dmg_dice(base_dmg),
        "xp":             _scale_xp(base_xp),
        "speed":          speed,
        "special":        special,
        "spawn_freq":     spawn_freq,
        "loot_chance":    loot_chance,
        "color_hint":     color_hint,
        "base_hostility": base_hostility,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MONSTER TABLE — all 42 TDR originals, in data-table order.
# icon_id = 400 + table_index  (Gate Keeper is icon 443, not 441).
#
# Level range key:
#   ✓ observed  — confirmed by playtesting to floor 15
#   ✓ V4.0      — from DoD V4.0 binary (earlier, uncorrupted table)
#   † TDR only  — TDR binary; floors 16+ not yet playtested
# ─────────────────────────────────────────────────────────────────────────────

MONSTERS = [

    # ── Floors 1–15 ──────────────────────────────────────────────────────────

    _m("ice_whirlwind",    "Ice Whirlwind",    "W", 400,   # ✓ observed
       min_floor=9,   max_floor=15,
       base_hp=60,  ac= 9,  atk= 6,  base_dmg=10,
       base_xp=500,   speed=2,
       special=["cold_aura", "immune_cold"],
       spawn_freq=10,  loot_chance=0.15,
       color_hint=(140, 200, 255),
       base_hostility=HOSTILITY_HOSTILE),

    _m("sethron",          "Sethron",          "9", 401,   # ✓ observed
       min_floor=1,   max_floor=2,
       base_hp=8,   ac= 9,  atk= 4,  base_dmg=1,
       base_xp=50,    speed=1,
       special=[],
       spawn_freq=75,  loot_chance=0.20,
       color_hint=(120, 200, 180),
       base_hostility=HOSTILITY_NEUTRAL),

    _m("zambit",           "Zambit",           "Z", 402,   # ✓ observed
       min_floor=5,   max_floor=9,
       base_hp=30,  ac= 7,  atk= 9,  base_dmg=7,
       base_xp=195,   speed=1,
       special=[],
       spawn_freq=40,  loot_chance=0.25,
       color_hint=(160, 120, 200),
       base_hostility=HOSTILITY_HOSTILE),

    _m("wandering_eye",    "Wandering Eye",    "e", 403,   # ✓ both agree
       min_floor=3,   max_floor=30,
       base_hp=40,  ac= 6,  atk= 9,  base_dmg=8,
       base_xp=200,   speed=1,
       special=["confuse"],
       spawn_freq=3,   loot_chance=0.15,
       color_hint=(200, 80, 180),
       base_hostility=HOSTILITY_HOSTILE),

    _m("giant_bat",        "Giant Bat",        "b", 404,   # ✓ observed
       min_floor=2,   max_floor=6,
       base_hp=15,  ac= 8,  atk= 4,  base_dmg=2,
       base_xp=60,    speed=2,
       special=[],
       spawn_freq=20,  loot_chance=0.10,
       color_hint=(160, 100, 60),
       base_hostility=HOSTILITY_HOSTILE),

    _m("lizzog",           "Lizzog",           "l", 405,   # ✓ observed
       min_floor=3,   max_floor=10,
       base_hp=18,  ac= 7,  atk= 7,  base_dmg=4,
       base_xp=100,   speed=1,
       special=[],
       spawn_freq=40,  loot_chance=0.20,
       color_hint=(80, 180, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("schwein_hund",     "Schwein Hund",     "H", 406,   # ✓ obs min / V4.0 max
       min_floor=5,   max_floor=6,
       base_hp=15,  ac= 7,  atk= 6,  base_dmg=4,
       base_xp=125,   speed=2,
       special=[],
       spawn_freq=5,   loot_chance=0.20,
       color_hint=(200, 160, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("balitor",          "Balitor",          "B", 407,   # ✓ both agree
       min_floor=31,  max_floor=39,
       base_hp=87,  ac= 1,  atk=20,  base_dmg=26,
       base_xp=6500,  speed=1,
       special=[],
       spawn_freq=40,  loot_chance=0.50,
       color_hint=(200, 80, 40),
       base_hostility=HOSTILITY_HOSTILE),

    _m("giant_spider",     "Giant Spider",     "s", 408,   # ✓ observed
       min_floor=5,   max_floor=11,
       base_hp=15,  ac= 5,  atk= 7,  base_dmg=6,
       base_xp=120,   speed=1,
       special=[],
       spawn_freq=30,  loot_chance=0.20,
       color_hint=(80, 60, 40),
       base_hostility=HOSTILITY_HOSTILE),

    _m("alligog",          "Alligog",          "A", 409,   # ✓ observed
       min_floor=1,   max_floor=3,
       base_hp=8,   ac=10,  atk= 4,  base_dmg=1,
       base_xp=50,    speed=1,
       special=[],
       spawn_freq=50,  loot_chance=0.10,
       color_hint=(60, 160, 100),
       base_hostility=HOSTILITY_HOSTILE),

    # ── Deep floors (10–40) ──────────────────────────────────────────────────

    _m("zarmindor",        "Zarmindor",        "8", 410,   # ✓ both agree
       min_floor=28,  max_floor=35,
       base_hp=75,  ac= 1,  atk=15,  base_dmg=25,
       base_xp=6000,  speed=1,
       special=[],
       spawn_freq=40,  loot_chance=0.45,
       color_hint=(160, 60, 200),
       base_hostility=HOSTILITY_HOSTILE),

    _m("ogrillon",         "Ogrillon",         "O", 411,   # ✓ observed
       min_floor=9,   max_floor=15,
       base_hp=55,  ac= 9,  atk=12,  base_dmg=12,
       base_xp=800,   speed=1,
       special=[],
       spawn_freq=40,  loot_chance=0.35,
       color_hint=(120, 100, 60),
       base_hostility=HOSTILITY_HOSTILE),

    _m("firboleg",         "Firboleg",         "F", 412,   # ✓ observed
       min_floor=2,   max_floor=4,
       base_hp=17,  ac= 8,  atk= 9,  base_dmg=4,
       base_xp=90,    speed=1,
       special=[],
       spawn_freq=15,  loot_chance=0.20,
       color_hint=(180, 140, 80),
       base_hostility=HOSTILITY_HOSTILE),

    # ── NOTE: TDR v1.2.3 has a +1 data-table shift from here through Dark  ───
    # ── Wizard (#28). Level ranges below come from V4.0 binary / gameplay.  ──

    _m("electric_penguin", "Electric Penguin", "P", 413,   # ✓ V4.0
       min_floor=25,  max_floor=30,
       base_hp=45,  ac= 3,  atk=12,  base_dmg=14,
       base_xp=800,   speed=2,
       special=[],
       spawn_freq=5,   loot_chance=0.30,
       color_hint=(100, 160, 220),
       base_hostility=HOSTILITY_HOSTILE),

    _m("morrigan",         "Morrigan",         "M", 414,   # ✓ obs min / V4.0 max
       min_floor=12,  max_floor=17,
       base_hp=25,  ac=10,  atk= 8,  base_dmg=6,
       base_xp=150,   speed=1,
       special=[],
       spawn_freq=20,  loot_chance=0.25,
       color_hint=(220, 80, 120),
       base_hostility=HOSTILITY_HOSTILE),

    _m("caveman",          "Caveman",          "C", 415,   # ✓ observed — TDR icon 415 (table row 15)
       min_floor=2,   max_floor=5,
       base_hp=55,  ac= 4,  atk= 9,  base_dmg=7,   # ref: 12d8 HP, 5d5 dmg (avg 15)
       base_xp=250,   speed=1,                       # was 1500 (450 scaled) — rebalanced to 75 scaled
       special=["immune_fire"],                       # comparable to Zambit/Giant Spider tier
       spawn_freq=40,  loot_chance=0.30,
       color_hint=(160, 120, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("fire_lizard",      "Fire Lizard",      "f", 416,   # ✓ obs min / V4.0 max
       min_floor=13,  max_floor=19,
       base_hp=90,  ac=-1,  atk=23,  base_dmg=26,
       base_xp=8750,  speed=1,
       special=["fire_breath"],
       spawn_freq=40,  loot_chance=0.40,
       color_hint=(220, 80, 40),
       base_hostility=HOSTILITY_HOSTILE),

    _m("evil_cleric",      "Evil Cleric",      "c", 417,   # ✓ V4.0
       min_floor=33,  max_floor=39,
       base_hp=50,  ac= 3,  atk=10,  base_dmg=16,
       base_xp=1250,  speed=1,
       special=["fire_breath"],
       spawn_freq=50,  loot_chance=0.40,
       color_hint=(200, 60, 60),
       base_hostility=HOSTILITY_HOSTILE),

    _m("air_devil",        "Air Devil",        "a", 418,   # ✓ V4.0
       min_floor=17,  max_floor=25,
       base_hp=100, ac= 0,  atk=25,  base_dmg=27,
       base_xp=9000,  speed=2,
       special=[],
       spawn_freq=1,   loot_chance=0.50,
       color_hint=(180, 180, 220),
       base_hostility=HOSTILITY_HOSTILE),

    _m("black_unicorn",    "Black Unicorn",    "U", 419,   # ✓ V4.0
       min_floor=30,  max_floor=30,
       base_hp=120, ac=-2,  atk=25,  base_dmg=30,
       base_xp=10000, speed=2,
       special=["immune_fire"],
       spawn_freq=15,  loot_chance=0.55,
       color_hint=(60, 40, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("dragon",           "Dragon",           "D", 420,   # ✓ V4.0
       min_floor=34,  max_floor=39,
       base_hp=70,  ac= 6,  atk=15,  base_dmg=20,
       base_xp=2500,  speed=1,
       special=[],
       spawn_freq=20,  loot_chance=0.60,
       color_hint=(200, 60, 60),
       base_hostility=HOSTILITY_HOSTILE),

    _m("succubus",         "Succubus",         "S", 421,   # ✓ V4.0
       min_floor=18,  max_floor=24,
       base_hp=35,  ac= 7,  atk=12,  base_dmg=10,
       base_xp=495,   speed=1,
       special=[],
       spawn_freq=50,  loot_chance=0.35,
       color_hint=(200, 80, 160),
       base_hostility=HOSTILITY_HOSTILE),

    _m("skeleton_warrior", "Skeleton Warrior", "K", 422,   # ✓ observed
       min_floor=7,   max_floor=13,
       base_hp=75,  ac= 3,  atk=13,  base_dmg=21,
       base_xp=3500,  speed=1,
       special=[],
       spawn_freq=10,  loot_chance=0.30,
       color_hint=(200, 200, 180),
       base_hostility=HOSTILITY_HOSTILE),

    _m("reaper",           "Reaper",           "R", 423,   # ✓ V4.0
       min_floor=22,  max_floor=24,
       base_hp=65,  ac= 8,  atk= 9,  base_dmg=12,
       base_xp=2000,  speed=1,
       special=["head_smash"],
       spawn_freq=15,  loot_chance=0.35,
       color_hint=(80, 80, 100),
       base_hostility=HOSTILITY_HOSTILE),

    _m("black_pudding",    "Black Pudding",    "p", 424,   # ✓ V4.0
       min_floor=15,  max_floor=20,
       base_hp=25,  ac= 4,  atk= 7,  base_dmg=8,
       base_xp=500,   speed=1,
       special=["acid_splash"],
       spawn_freq=15,  loot_chance=0.10,
       color_hint=(40, 40, 40),
       base_hostility=HOSTILITY_HOSTILE),

    _m("giant_scorpion",   "Giant Scorpion",   "S", 425,   # ✓ observed
       min_floor=8,   max_floor=10,
       base_hp=40,  ac= 3,  atk=13,  base_dmg=18,
       base_xp=2750,  speed=1,
       special=[],
       spawn_freq=50,  loot_chance=0.25,
       color_hint=(200, 160, 40),
       base_hostility=HOSTILITY_HOSTILE),

    _m("fomor",            "Fomor",            "G", 426,   # ✓ V4.0
       min_floor=22,  max_floor=27,
       base_hp=57,  ac= 2,  atk= 9,  base_dmg=14,
       base_xp=2000,  speed=1,
       special=[],
       spawn_freq=15,  loot_chance=0.30,
       color_hint=(100, 140, 120),
       base_hostility=HOSTILITY_HOSTILE),

    _m("banshee",          "Banshee",          "N", 427,   # ✓ V4.0
       min_floor=18,  max_floor=23,
       base_hp=57,  ac= 2,  atk= 9,  base_dmg=14,
       base_xp=2000,  speed=1,
       special=["level_drain", "scream"],
       spawn_freq=0,   loot_chance=0.60,
       color_hint=(240, 240, 255),
       base_hostility=HOSTILITY_HOSTILE),

    # ── Floor 40 boss ─────────────────────────────────────────────────────────

    _m("dark_wizard",      "Dark Wizard",      "X", 428,   # ✓ TDR binary offset 0xc2a6
       min_floor=40,  max_floor=40,
       base_hp=800, ac=-5,  atk=15,  base_dmg=36,
       base_xp=32000, speed=1,
       special=["fire_breath", "immune_fire", "boss", "boss_escape"],
       spawn_freq=0,   loot_chance=1.0,
       color_hint=(120, 60, 200),
       base_hostility=HOSTILITY_HOSTILE,
       hp_fixed=800),

    # ── Floors 29+: TDR binary only († unverified by playtesting) ─────────────

    _m("drackone",         "Drackone",         "d", 429,   # † TDR only
       min_floor=4,   max_floor=4,
       base_hp=10,  ac= 9,  atk= 2,  base_dmg=14,
       base_xp=650,   speed=2,
       special=["cold_aura", "immune_cold"],
       spawn_freq=3,   loot_chance=0.25,
       color_hint=(100, 180, 220),
       base_hostility=HOSTILITY_HOSTILE),

    _m("freezing_sphere",  "Freezing Sphere",  "o", 430,   # † TDR only
       min_floor=12,  max_floor=17,
       base_hp=50,  ac= 2,  atk=23,  base_dmg=16,
       base_xp=850,   speed=2,
       special=[],
       spawn_freq=10,  loot_chance=0.20,
       color_hint=(180, 220, 255),
       base_hostility=HOSTILITY_HOSTILE),

    _m("crimean_warrior",  "Crimean Warrior",  "w", 431,   # ✓ observed
       min_floor=13,  max_floor=15,
       base_hp=65,  ac= 2,  atk=15,  base_dmg=22,
       base_xp=3600,  speed=1,
       special=[],
       spawn_freq=20,  loot_chance=0.35,
       color_hint=(160, 100, 60),
       base_hostility=HOSTILITY_HOSTILE),

    _m("witch",            "Witch",            "W", 432,   # † TDR only
       min_floor=10,  max_floor=14,
       base_hp=40,  ac= 4,  atk=12,  base_dmg=12,
       base_xp=750,   speed=1,
       special=["confuse"],
       spawn_freq=10,  loot_chance=0.35,
       color_hint=(140, 60, 180),
       base_hostility=HOSTILITY_HOSTILE),

    _m("amadon",           "Amadon",           "7", 433,   # ✓ observed
       min_floor=10,  max_floor=11,
       base_hp=90,  ac= 1,  atk=14,  base_dmg=27,
       base_xp=7450,  speed=1,
       special=["stat_drain"],
       spawn_freq=30,  loot_chance=0.45,
       color_hint=(60, 120, 200),
       base_hostility=HOSTILITY_HOSTILE),

    _m("vampire",          "Vampire",          "V", 434,   # † TDR only
       min_floor=26,  max_floor=33,
       base_hp=80,  ac= 2,  atk=20,  base_dmg=20,
       base_xp=5100,  speed=1,
       special=[],
       spawn_freq=25,  loot_chance=0.50,
       color_hint=(160, 40, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("centaur",          "Centaur",          "c", 435,   # † TDR only
       min_floor=27,  max_floor=35,
       base_hp=60,  ac= 1,  atk=19,  base_dmg=25,
       base_xp=5500,  speed=1,
       special=[],
       spawn_freq=10,  loot_chance=0.30,
       color_hint=(160, 120, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("evil_necromancer", "Evil Necromancer", "n", 436,   # † TDR only
       min_floor=20,  max_floor=25,
       base_hp=50,  ac= 2,  atk=27,  base_dmg=18,
       base_xp=3500,  speed=1,
       special=["necromancy"],
       spawn_freq=20,  loot_chance=0.40,
       color_hint=(80, 60, 120),
       base_hostility=HOSTILITY_HOSTILE),

    _m("shambling_mound",  "Shambling Mound",  "m", 437,   # † TDR only
       min_floor=16,  max_floor=25,
       base_hp=45,  ac= 3,  atk=20,  base_dmg=19,
       base_xp=1300,  speed=1,
       special=[],
       spawn_freq=2,   loot_chance=0.20,
       color_hint=(80, 120, 60),
       base_hostility=HOSTILITY_NEUTRAL),

    _m("drow",             "Drow",             "r", 438,   # † TDR only
       min_floor=11,  max_floor=16,
       base_hp=40,  ac= 4,  atk= 9,  base_dmg=10,
       base_xp=750,   speed=1,
       special=[],
       spawn_freq=30,  loot_chance=0.30,
       color_hint=(80, 60, 140),
       base_hostility=HOSTILITY_HOSTILE),

    _m("lion",             "Lion",             "L", 439,   # ✓ observed
       min_floor=12,  max_floor=15,
       base_hp=65,  ac= 2,  atk=15,  base_dmg=22,
       base_xp=3750,  speed=2,
       special=[],
       spawn_freq=5,   loot_chance=0.30,
       color_hint=(220, 180, 80),
       base_hostility=HOSTILITY_HOSTILE),

    _m("ettin",            "Ettin",            "E", 440,   # † TDR only
       min_floor=18,  max_floor=20,
       base_hp=70,  ac= 1,  atk= 9,  base_dmg=14,
       base_xp=3000,  speed=1,
       special=[],
       spawn_freq=5,   loot_chance=0.35,
       color_hint=(100, 80, 60),
       base_hostility=HOSTILITY_HOSTILE),

    # ── icon IDs 441–442: The Floor (TDR monster indices 41-42) ──────────────
    # Name "Floor" in TDR DATA_0. Camouflaged as floor tiles; NEUTRAL until
    # provoked. Two entries: one mid-dungeon, one deeper.
    _m("floor_a",          "The Floor",        ".", 441,   # ✓ TDR offset 0xc32e
       min_floor=18,  max_floor=20,
       base_hp=70,  ac= 1,  atk= 9,  base_dmg=14,
       base_xp=3000,  speed=1,
       special=[],
       spawn_freq=5,   loot_chance=0.30,
       color_hint=(180, 170, 140),
       base_hostility=HOSTILITY_NEUTRAL),

    _m("floor_b",          "The Floor",        ".", 442,   # ✓ TDR offset 0xc334
       min_floor=26,  max_floor=28,
       base_hp=85,  ac= 0,  atk= 9,  base_dmg=20,
       base_xp=4000,  speed=1,
       special=[],
       spawn_freq=5,   loot_chance=0.35,
       color_hint=(160, 152, 124),
       base_hostility=HOSTILITY_NEUTRAL),

    # ── icon ID 443: Gate Keeper ──────────────────────────────────────────────
    # spawn_freq=0: never random-spawned; game.py places one per section.
    # HP=1 and base stats are placeholders — overridden at spawn time using
    # GK_HP_TABLE / GK_AC_TABLE / GK_ATK_TABLE from constants.py.
    # XP=15000: confirmed from TDR binary word at 0xc33a bytes 4-5.
    _m("gate_keeper",      "Gate Keeper",      "G", 443,   # ✓ TDR offset 0xc33a
       min_floor=5,   max_floor=35,
       base_hp=1,   ac= 1,  atk= 1,  base_dmg=1,
       base_xp=15000, speed=1,
       special=["gate_keeper", "head_smash"],
       spawn_freq=0,   loot_chance=0.0,
       color_hint=(200, 180, 80),
       base_hostility=HOSTILITY_HOSTILE),
]


# ─────────────────────────────────────────────────────────────────────────────
# Lookup helpers
# ─────────────────────────────────────────────────────────────────────────────

MONSTER_BY_ID: dict = {m["id"]: m for m in MONSTERS}

# ── Save-game compatibility ────────────────────────────────────────────────────
# Monster IDs that existed before v0.401 (D&D placeholder creatures) mapped to
# the nearest TDR equivalent by floor range and threat level.
# Used by get_monster() so saved games from v0.309 and earlier load cleanly.
LEGACY_ID_MAP: dict = {
    "kobold":    "sethron",          # floor 1–2 light enemy
    "giant_rat": "alligog",          # floor 1–3 light enemy
    "orc":       "firboleg",         # floor 2–4 mid enemy
    "skeleton":  "lizzog",           # floor 3–10 mid enemy
    "zombie":    "morrigan",         # mid-depth undead feel
    "pirboleg":  "firboleg",         # was a typo of firboleg anyway
    "the_floor": "floor_a",          # now a proper entry; map old ID to floor_a
}


def get_monster(mid: str) -> dict:
    if mid in MONSTER_BY_ID:
        return MONSTER_BY_ID[mid]
    legacy = LEGACY_ID_MAP.get(mid)
    if legacy:
        return MONSTER_BY_ID[legacy]
    raise KeyError(f"Unknown monster id {mid!r} (not in current roster or legacy map)")


def monsters_for_floor(floor: int) -> list:
    """Return all monsters eligible to spawn on *floor*, excluding spawn_freq=0."""
    return [m for m in MONSTERS
            if m["min_floor"] <= floor <= m["max_floor"]
            and m["spawn_freq"] > 0]


def weighted_monsters_for_floor(floor: int) -> list:
    """
    Return a flat list where each monster appears spawn_freq times,
    ready for random.choice() in the dungeon populator.
    """
    pool = []
    for m in monsters_for_floor(floor):
        pool.extend([m] * m["spawn_freq"])
    return pool

# Create the lookup mapping needed by the sprite engine
MONSTER_BY_ID = {m["id"]: m for m in MONSTERS}

def get_monster(mid: str) -> dict:
    """Returns the monster data for a given ID."""
    if mid in MONSTER_BY_ID:
        return MONSTER_BY_ID[mid]
    
    # Optional: Legacy mapping if you have old save files
    LEGACY_ID_MAP = {"kobold": "sethron", "giant_rat": "alligog"}
    legacy = LEGACY_ID_MAP.get(mid)
    if legacy:
        return MONSTER_BY_ID[legacy]
        
    raise KeyError(f"Unknown monster id {mid!r}")