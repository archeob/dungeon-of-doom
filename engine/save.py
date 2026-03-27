# engine/save.py — Save / Load for Dungeon of Doom
# v0.103.20260307
#
# Format: JSON, extension .dod
# Philosophy: the dungeon floors are deterministic (seed-based), so we only
# save the *delta* from generation: live monster/item spawn tables, and the
# FOV walked/explored sets per visited floor.  On load we regenerate each
# floor from its seed (same tiles, same stair positions) then overlay the
# saved spawn tables.  This keeps files small and robust.

import json
import os
from typing import Optional

from constants import VERSION

# ── Resume slot path (Hero difficulty auto-save) ──────────────────────────────
# Lives next to main.py, never packaged in zips — created by the game at runtime.
RESUME_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resume.dod")
)


# ── Serialisers ───────────────────────────────────────────────────────────────

def _item_to_dict(obj) -> dict | None:
    """Safely convert an inventory/equipped slot value to a plain dict."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        # Ensure newer fields are present even on older save dicts
        obj.setdefault("enchant_known", False)
        obj.setdefault("fuzzy_enchant", obj.get("fuzzy_enchant"))  # may be absent
        # Remove None fuzzy_enchant to keep saves clean
        if obj.get("fuzzy_enchant") is None:
            obj.pop("fuzzy_enchant", None)
        return obj
    # Live Item object — extract serialisable fields
    return {
        "item_id":       obj.id,
        "name":          obj.name,
        "cat":           obj.cat,
        "identified":    obj.identified,
        "cursed":        obj.cursed,
        "enchant":       obj.enchant,
        "enchant_known": getattr(obj, "enchant_known", False),
        "charges":       obj.charges,
    }


def _player_to_dict(p) -> dict:
    return {
        "name":         p.name,
        "class_key":    p.class_key,
        "x": p.x, "y": p.y,
        "stats":        list(p.stats),
        "max_hp":       p.max_hp,
        "hp":           p.hp,
        "level":        p.level,
        "xp":           p.xp,
        "xp_next":      p.xp_next,
        "gold":         p.gold,
        "food":         p.food,
        "starving":     p.starving,
        "stuffed":      p.stuffed,
        "alive":        p.alive,
        "won":          p.won,
        "poisoned":     p.poisoned,
        "confused":     p.confused,
        "blinded":      p.blinded,
        "hasted":       p.hasted,
        "stunned":      getattr(p, "stunned", False),
        "slowed":       getattr(p, "slowed", False),
        "status_turns": p.status_turns,
        "equipped":     {k: _item_to_dict(v) for k, v in p.equipped.items()},
        "inventory":    [_item_to_dict(i) for i in p.inventory],
    }


def _player_from_dict(d: dict):
    from entities.player import Player
    from data.classes import get_class
    cls  = get_class(d["class_key"])
    p    = Player(d["name"], d["class_key"], d["stats"], cls["base_hp"])
    # Overwrite everything with saved values
    p.x, p.y         = d["x"], d["y"]
    p.stats          = list(d["stats"])
    p.max_hp         = d["max_hp"]
    p.hp             = d["hp"]
    p.level          = d["level"]
    p.xp             = d["xp"]
    p.xp_next        = d["xp_next"]
    p.gold           = d["gold"]
    p.food           = d["food"]
    p.starving       = d["starving"]
    p.stuffed        = d.get("stuffed", False)
    p.alive          = d["alive"]
    p.won            = d["won"]
    p.poisoned       = d["poisoned"]
    p.confused       = d["confused"]
    p.blinded        = d["blinded"]
    p.hasted         = d["hasted"]
    p.stunned        = d.get("stunned", False)
    p.slowed         = d.get("slowed", False)
    p.status_turns   = dict(d["status_turns"])
    p.inventory      = list(d["inventory"])
    # Reconcile equipped pointers so they reference the SAME dict objects
    # that are already in p.inventory (load creates separate dicts otherwise,
    # causing items to appear twice in the inventory screen).
    _inv_idx = {}
    for inv_item in p.inventory:
        iid = inv_item.get("item_id")
        if iid:
            _inv_idx[iid] = inv_item
    raw_equipped = d.get("equipped", {})
    p.equipped = {}
    for slot, eq_dict in raw_equipped.items():
        if eq_dict is None:
            p.equipped[slot] = None
        else:
            iid = eq_dict.get("item_id") if isinstance(eq_dict, dict) else None
            # Use the inventory reference if possible; fall back to raw dict
            p.equipped[slot] = _inv_idx.get(iid, eq_dict) if iid else eq_dict
    return p


def _log_to_list(log) -> list:
    # Store as [[text, [r,g,b]], ...]
    return [[text, list(color)] for text, color in log._lines]


def _log_from_list(items: list):
    from engine.game import MessageLog
    ml = MessageLog()
    for text, color in reversed(items):   # recent() reads from front; add reverses
        ml.add(text, tuple(color))
    return ml


# ── Public API ────────────────────────────────────────────────────────────────

def save_game(game, path: str) -> None:
    """
    Serialise game to JSON at path.
    Caller must call game._save_floor_state() first so current-floor
    monsters/items are flushed back to the level's spawn tables.
    """
    # Floor data: only visited levels (those in the cache)
    floors_data = {}
    for floor_num, lv in game.cache._levels.items():
        floors_data[str(floor_num)] = {
            "monster_spawns": list(lv.monster_spawns),
            "item_spawns":    list(lv.item_spawns),
            # Tile modifications (wand of Digging, boulder pushes) — stored as
            # [[x, y, tile_type], ...] for JSON serialisation.
            "tile_mods": [[x, y, t] for (x, y), t in lv.tile_mods.items()],
        }

    # FOV data: walked + explored per floor
    fov_data = {}
    for floor_num, fov_map in game._fov_maps.items():
        fov_data[str(floor_num)] = {
            "walked":   [list(t) for t in fov_map.walked],
            "explored": [list(t) for t in fov_map.explored],
        }

    doc = {
        "save_version": VERSION,
        "turn":         game.turn,
        "floor":        game.floor,
        "phase":        game.phase,
        "base_seed":    game.cache.base_seed,
        "game_id":      getattr(game, "game_id", game.cache.base_seed),
        "stat_xp_earned": getattr(game, "stat_xp_earned", 0),
        "difficulty":   getattr(game, "difficulty", "adventurer"),
        "id_map":       game.id_map,
        "identified":   list(game.identified),
        "pending_identify": game.pending_identify,
        "gk_sections_cleared": list(getattr(game, "gk_sections_cleared", set())),
        "player":       _player_to_dict(game.player),
        "log":          _log_to_list(game.log),
        "floors":       floors_data,
        "fov":          fov_data,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

    game.save_path = path
    game.dirty     = False


def load_game(path: str):
    """
    Deserialise a .dod JSON file and return a fully restored GameState.
    Raises ValueError on format mismatch, OSError on file errors.
    """
    from engine.game import GameState, PHASE_PLAYING
    from engine.dungeon import FloorCache

    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    if "save_version" not in doc or "player" not in doc:
        raise ValueError("Not a valid Dungeon of Doom save file.")

    game = GameState()
    game.turn   = doc["turn"]
    game.floor          = doc["floor"]
    game.phase          = doc["phase"]
    game.id_map         = doc.get("id_map", {})
    game.identified     = set(doc.get("identified", []))
    game.pending_identify = doc.get("pending_identify", 0)
    game.gk_sections_cleared = set(doc.get("gk_sections_cleared", []))
    game.game_id        = doc.get("game_id", doc.get("base_seed", 0))
    game.stat_xp_earned = doc.get("stat_xp_earned", 0)
    game.difficulty     = doc.get("difficulty", "adventurer")
    game.player = _player_from_dict(doc["player"])
    game.log    = _log_from_list(doc["log"])

    # Rebuild floor cache from seed — regenerates all floors deterministically
    game.cache  = FloorCache(doc["base_seed"])

    # Overlay saved spawn tables onto regenerated levels
    for floor_str, fdata in doc["floors"].items():
        floor_num = int(floor_str)
        lv = game.cache.get(floor_num)   # generates if not cached
        lv.monster_spawns = list(fdata["monster_spawns"])
        lv.item_spawns    = list(fdata["item_spawns"])
        # Reapply tile modifications (dug walls, boulders) onto the fresh level
        for entry in fdata.get("tile_mods", []):
            x, y, tile_type = entry
            lv.tile_mods[(x, y)] = tile_type
            lv.set(x, y, tile_type)

    # Restore FOV maps
    from engine.fov import FovMap
    from constants import MAP_COLS, MAP_ROWS
    for floor_str, fdata in doc["fov"].items():
        floor_num = int(floor_str)
        fov_map   = FovMap(MAP_COLS, MAP_ROWS)
        fov_map.walked   = {tuple(t) for t in fdata["walked"]}
        fov_map.explored = {tuple(t) for t in fdata["explored"]}
        game._fov_maps[floor_num] = fov_map

    # Load current floor entities
    game.level = game.cache.get(game.floor)
    game._spawn_entities(game.level)

    # Recompute FOV from player's current position
    game._update_fov()

    game.save_path = path
    game.dirty     = False
    return game
