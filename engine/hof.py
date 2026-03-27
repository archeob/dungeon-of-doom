# engine/hof.py — Hall of Fame  (v0.305.20260310)
#
# Stores the top-10 runs in  dod/hof.json  (next to main.py).
# The data file is NEVER packaged in release zips — it is created at runtime
# on first submission and survives every version update automatically.
#
# Score formula (Glory):
#   depth_glory   = floor_reached   × 100
#   level_glory   = char_level      × 150
#   xp_glory      = xp_earned_total × 2    (cumulative across levels)
#   id_glory      = items_identified× 25
#   explore_glory = floors_well_explored × 50  (≥100 tiles walked on floor)
#   victory_bonus = 5 000 flat

import json
import os
from datetime import date

from constants import (
    DIFF_ARCHITECT, DIFF_GLORY_MULT, CLASS_GLORY_BONUS,
)

# ── File location ─────────────────────────────────────────────────────────────
HOF_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "hof.json")
)
HOF_MAX = 10

_CLASS_ABBREV = {
    "knight":    "Knt",
    "fighter":   "Ftr",
    "sage":      "Sge",
    "wizard":    "Wzd",
    "alchemist": "Alc",
    "jeweler":   "Jwl",
    "jones":     "Jns",
}


# ── Glory calculation ─────────────────────────────────────────────────────────

def compute_glory(game) -> tuple:
    """Return (total_glory: int, breakdown: dict).
    Applies difficulty multiplier then class bonus.
    Architect always returns 0.
    """
    from engine.game import PHASE_WIN
    p = game.player

    difficulty = getattr(game, "difficulty", "adventurer")
    if difficulty == DIFF_ARCHITECT:
        # No glory for Architect
        bd_zero = {k: (0, 0, lbl) for k, lbl in [
            ("depth",   "Floor reached"),
            ("level",   "Character level"),
            ("xp",      "XP earned"),
            ("items",   "Items identified"),
            ("explore", "Floors explored"),
            ("victory", "Victory bonus"),
        ]}
        return 0, bd_zero

    depth_gl   = game.floor * 100
    level_gl   = p.level * 150
    xp_gl      = getattr(game, "stat_xp_earned", 0) * 2
    id_gl      = len(game.identified) * 25
    explore_gl = sum(
        50 for fov in game._fov_maps.values()
        if len(fov.walked) >= 100
    )
    won        = (game.phase == PHASE_WIN) or getattr(p, "won", False)
    victory_gl = 5000 if won else 0

    raw_total = depth_gl + level_gl + xp_gl + id_gl + explore_gl + victory_gl

    # Difficulty multiplier
    diff_mult  = DIFF_GLORY_MULT.get(difficulty, 1.0)
    # Class bonus (additive percentage on top of difficulty-adjusted total)
    class_bonus = CLASS_GLORY_BONUS.get(p.class_key.lower(), 0.0)
    total = int(raw_total * diff_mult * (1.0 + class_bonus))

    breakdown = {
        "depth":   (int(depth_gl   * diff_mult * (1 + class_bonus)), game.floor,             "Floor reached"),
        "level":   (int(level_gl   * diff_mult * (1 + class_bonus)), p.level,                "Character level"),
        "xp":      (int(xp_gl      * diff_mult * (1 + class_bonus)), getattr(game, "stat_xp_earned", 0), "XP earned"),
        "items":   (int(id_gl      * diff_mult * (1 + class_bonus)), len(game.identified),   "Items identified"),
        "explore": (int(explore_gl * diff_mult * (1 + class_bonus)), explore_gl // 50,       "Floors explored"),
        "victory": (int(victory_gl * diff_mult * (1 + class_bonus)), 1 if won else 0,        "Victory bonus"),
    }
    return total, breakdown


# ── Outcome helpers ───────────────────────────────────────────────────────────

def short_outcome(outcome: str) -> str:
    """≤12-char abbreviation for the HoF table cell."""
    s = outcome.lower()
    if "escaped" in s or "orb" in s:
        return "Victory!"
    if "poison" in s:
        return "Poisoned"
    if "starv" in s:
        return "Starvation"
    if s.startswith("slain by "):
        monster = outcome[len("Slain by "):]
        if monster.lower().startswith("the "):
            monster = monster[4:]
        return monster[:12]
    return outcome.split()[0][:12] if outcome else "Unknown"


def class_abbrev(class_key: str) -> str:
    return _CLASS_ABBREV.get(class_key.lower(), class_key[:3].capitalize())


# ── Persistence ───────────────────────────────────────────────────────────────

def load_hof() -> list:
    """Load and return the HoF list. Returns [] if absent or corrupt."""
    try:
        with open(HOF_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        for entry in data:
            entry.setdefault("class_name",    entry.get("class_key", "?").capitalize())
            entry.setdefault("char_level",     1)
            entry.setdefault("dungeon_floor",  1)
            entry.setdefault("outcome",        "Unknown")
            entry.setdefault("turns",          0)
            entry.setdefault("date",           "")
            entry.setdefault("glory",          0)
            entry.setdefault("game_id",        0)
        return sorted(data, key=lambda e: e["glory"], reverse=True)[:HOF_MAX]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def _write(entries: list) -> None:
    try:
        with open(HOF_PATH, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except OSError:
        pass


def submit_entry(game) -> tuple:
    """
    Compute glory, insert into HoF if it qualifies, write to disk.
    Returns (entry_dict, rank_1_to_10_or_None).
    Deduplicates by game_id — same run can only occupy one slot.
    Architect difficulty is always excluded.
    """
    from data.classes import get_class

    p           = game.player
    difficulty  = getattr(game, "difficulty", "adventurer")

    # Architect mode — never enters the Hall of Fame
    if difficulty == DIFF_ARCHITECT:
        return {"name": p.name, "glory": 0}, None

    glory, _bd  = compute_glory(game)
    game_id     = getattr(game, "game_id", 0)
    death_cause = getattr(game, "death_cause", "")
    class_key   = p.class_key
    try:
        class_name = get_class(class_key)["name"]
    except Exception:
        class_name = class_key.capitalize()

    entry = {
        "game_id":       game_id,
        "name":          p.name,
        "class_key":     class_key,
        "class_name":    class_name,
        "char_level":    p.level,
        "dungeon_floor": game.floor,
        "glory":         glory,
        "outcome":       death_cause or "Unknown",
        "turns":         game.turn,
        "date":          date.today().isoformat(),
        "difficulty":    difficulty,
    }

    entries = load_hof()

    # Deduplicate: replace only if new score is better
    same_run = [e for e in entries if e.get("game_id") == game_id]
    if same_run:
        if glory <= same_run[0]["glory"]:
            rank = next(
                (i + 1 for i, e in enumerate(entries)
                 if e.get("game_id") == game_id),
                None
            )
            return same_run[0], rank
        entries = [e for e in entries if e.get("game_id") != game_id]

    entries.append(entry)
    entries.sort(key=lambda e: e["glory"], reverse=True)
    entries = entries[:HOF_MAX]
    _write(entries)

    rank = next(
        (i + 1 for i, e in enumerate(entries)
         if e.get("game_id") == game_id),
        None
    )
    return entry, rank
