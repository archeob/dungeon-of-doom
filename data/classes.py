# data/classes.py
# The seven character classes of Dungeon of Doom.

from constants import (S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA,
                       IC_WEAPON, IC_ARMOR, IC_POTION, IC_RING,
                       IC_SCROLL, IC_WAND, IC_JEWEL, IC_MISC)

# starting_kit format:
#   "equip"  : list of {"choices": [id, ...]}  — pick one per entry, equip it
#   "carry"  : list of {"choices": [id, ...], "count": N}  — pick N distinct items to carry
# All starting weapons/armour begin with enchant=0.

CLASSES = {
    "knight": {
        "name":        "Knight",
        "key":         "knight",
        "stats":       [17, 10, 12, 14, 16, 14],
        "base_hp":     22,
        "identify":    IC_ARMOR,
        "description": "A heavily armoured warrior. High strength and constitution.",
        "starting_kit": {
            "equip": [
                {"choices": ["mace", "long_sword", "two_handed_sword"]},
                {"choices": ["banded_armor", "plate_armor"]},
            ],
            "carry": [],
        },
    },
    "fighter": {
        "name":        "Fighter",
        "key":         "fighter",
        "stats":       [16, 10, 10, 15, 15, 11],
        "base_hp":     20,
        "identify":    IC_WEAPON,
        "description": "A trained soldier. Identifies weapons by touch.",
        "starting_kit": {
            "equip": [
                {"choices": ["long_sword", "two_handed_sword"]},
                {"choices": ["chain_armor", "banded_armor"]},
            ],
            "carry": [],
        },
    },
    "sage": {
        "name":        "Sage",
        "key":         "sage",
        "stats":       [10, 15, 17, 11, 12, 13],
        "base_hp":     14,
        "identify":    IC_SCROLL,
        "description": "A learned scholar. Automatically reads scrolls safely.",
        "starting_kit": {
            "equip": [
                {"choices": ["leather_armor"]},
                {"choices": ["dagger"]},
            ],
            "carry": [
                {"choices": ["scroll_identify", "scroll_enchant_weapon",
                             "scroll_protection", "scroll_magic_mapping",
                             "scroll_remove_curse", "scroll_intelligence",
                             "scroll_wisdom"],
                 "count": 3},
            ],
        },
    },
    "wizard": {
        "name":        "Wizard",
        "key":         "wizard",
        "stats":       [9,  17, 14, 12, 11, 12],
        "base_hp":     12,
        "identify":    IC_WAND,
        "description": "A master of arcane power. Wands never misfire in their hands.",
        "starting_kit": {
            "equip": [
                {"choices": ["leather_armor"]},
                {"choices": ["dagger"]},
            ],
            "carry": [
                {"choices": ["wand_striking", "wand_sleep", "wand_fear",
                             "wand_lightning", "wand_fire", "wand_ice"],
                 "count": 2},
            ],
        },
    },
    "alchemist": {
        "name":        "Alchemist",
        "key":         "alchemist",
        "stats":       [11, 14, 13, 13, 13, 12],
        "base_hp":     14,
        "identify":    IC_POTION,
        "description": "A brewer of potions. Never drinks a harmful potion by mistake.",
        "starting_kit": {
            "equip": [
                {"choices": ["leather_armor"]},
                {"choices": ["dagger"]},
            ],
            "carry": [
                {"choices": ["potion_healing", "potion_extra_healing", "potion_speed",
                             "potion_strength", "potion_dexterity", "potion_constitution",
                             "potion_resist_fire", "potion_resist_cold"],
                 "count": 3},
            ],
        },
    },
    "jeweler": {
        "name":        "Jeweler",
        "key":         "jeweler",
        "stats":       [11, 13, 11, 16, 12, 15],
        "base_hp":     13,
        "identify":    IC_RING,
        "description": "A dealer in gems and rings. Identifies rings at a glance.",
        "starting_kit": {
            "equip": [
                {"choices": ["leather_armor"]},
                {"choices": ["dagger"]},
            ],
            "carry": [
                {"choices": ["ring_regeneration", "ring_resist_fire",
                             "ring_resist_cold", "ring_xray"],
                 "count": 1},
            ],
        },
    },
    "jones": {
        "name":        "Jones",
        "key":         "jones",
        "stats":       [13, 13, 13, 13, 13, 13],
        "base_hp":     16,
        "identify":    None,
        "description": "Just a regular person. No special skills—or weaknesses.",
        "starting_kit": {
            "equip": [
                {"choices": ["leather_armor"]},
                {"choices": ["leather_whip"]},
            ],
            "carry": [
                {"choices": ["food_good", "food_bland"], "count": 1},
            ],
        },
    },
}

CLASS_ORDER = ["knight", "fighter", "sage", "wizard", "alchemist", "jeweler", "jones"]


def get_class(key: str) -> dict:
    return CLASSES[key]


def all_classes() -> list:
    return [CLASSES[k] for k in CLASS_ORDER]


def starting_stats(key: str) -> list:
    return list(CLASSES[key]["stats"])
