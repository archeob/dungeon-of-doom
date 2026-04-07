# data/items.py — Full item table v0.109 (from spreadsheet DoD_items.xlsx)
#
# Schema per category:
#   weapon : id, name, cat, slot, base_dmg, max_enchant, hands, weight, value
#   armor  : id, name, cat, slot, base_ac,  max_enchant, weight, value
#   potion : id, name, cat, effect, temporary, message, power, weight, value
#   scroll : id, name, cat, effect, temporary, message, weight, value
#   wand   : id, name, cat, effect, charges, message, weight, value
#   ring   : id, name, cat, slot, effect, cursed, max_enchant, message, weight, value
#   food   : id, name, cat, food_val, message, weight, value
#   gem    : id, name, cat, weight, value
#   misc   : id, name, cat, weight, value, quest/fake

from constants import (IC_WEAPON, IC_ARMOR, IC_POTION, IC_SCROLL,
                       IC_RING, IC_WAND, IC_FOOD, IC_JEWEL, IC_MISC)

# ── Identification pools (shuffled per run in game.py) ─────────────────────────

POTION_COLORS = [
    "Blue", "Brown", "Clear", "Cyan", "Dark", "Glowing", "Golden",
    "Green", "Hot Pink", "Magenta", "Oily", "Orange", "Red",
    "Silver", "Swirly", "White", "Yellow",
]

SCROLL_NAMES = [
    "Anul-nathrack", "Ballani", "Binga-Sedu", "Bogus-Mondus",
    "Bonziana", "Kelebunga", "Morgana", "Naui-Bailut",
    "Oha-Noa", "Owe-Stoas", "Papyrus", "Shach-Abra",
    "Schlema-Nusae", "Vellum", "Xancha-Mora", "Zelphiri",
]

WAND_MATERIALS = [
    "Bamboo", "Brass", "Bronze", "Copper", "Ebony",
    "Iron", "Ivory", "Maple", "Silver", "Tin", "Wooden",
]

RING_GEMS = [
    "Diamond", "Emerald", "Gold", "Jade", "Opal", "Pearl", "Ruby",
]

# Ordered lists of IDs — order must match the colour/name lists above
POTION_IDS = [
    "potion_confusion", "potion_extra_healing", "potion_resist_fire",
    "potion_healing", "potion_invisibility", "potion_levitation",
    "potion_poison", "potion_speed", "potion_muscle",
    "potion_resist_cold", "potion_dexterity", "potion_constitution",
    "potion_charisma", "potion_blindness", "potion_worthless",
    "potion_strength", "potion_life",
]

SCROLL_IDS = [
    "scroll_gain_level", "scroll_identify", "scroll_enchant_armor",
    "scroll_magic_mapping", "scroll_teleport", "scroll_enchant_weapon",
    "scroll_protection", "scroll_wishing", "scroll_intelligence",
    "scroll_wisdom", "scroll_remove_curse", "scroll_amnesia",
    "scroll_joke", "scroll_words",
    "scroll_scare", "scroll_charm",
]

WAND_IDS = [
    "wand_lightning", "wand_fire", "wand_ice", "wand_death",
    "wand_striking", "wand_fear", "wand_digging", "wand_sleep",
    "wand_polymorph", "wand_teleport", "wand_invisibility",
]

RING_IDS = [
    "ring_resist_fire", "ring_resist_cold", "ring_regeneration",
    "ring_slowness", "ring_hunger", "ring_xray", "ring_monster",
]

# ── Item table ─────────────────────────────────────────────────────────────────

ITEMS = [

    # ── WEAPONS ──────────────────────────────────────────────────────────────
    # base_dmg = max face of 1d{base_dmg} roll; hands = 1 or 2
    {"id":"dagger",          "name":"Dagger",           "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(1,4),  "base_dmg":1, "max_enchant":4, "hands":1, "weight":2,  "value":10},
    {"id":"leather_whip",    "name":"Leather Whip",     "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(1,4),  "base_dmg":2, "max_enchant":4, "hands":1, "weight":3,  "value":20},
    {"id":"long_sword",      "name":"Long Sword",        "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(1,8),  "base_dmg":3, "max_enchant":4, "hands":1, "weight":5,  "value":60},
    {"id":"mace",            "name":"Mace",              "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(2,4),  "base_dmg":4, "max_enchant":4, "hands":1, "weight":8,  "value":80},
    {"id":"two_handed_sword","name":"Two-Handed Sword",  "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(1,12), "base_dmg":5, "max_enchant":4, "hands":2, "weight":10, "value":120},
    {"id":"death_blade",     "name":"Death Blade",       "cat":IC_WEAPON,
     "slot":"weapon", "dmg_dice":(2,6),  "base_dmg":6, "max_enchant":4, "hands":1, "weight":5,  "value":200},
    {"id":"sling",           "name":"Sling",             "cat":IC_WEAPON,
     "slot":"offhand","base_dmg":0, "max_enchant":0, "hands":1, "weight":2,  "value":15,
     "effect":"throw_bonus"},

    # ── THROWING ITEMS ────────────────────────────────────────────────────────
    {"id":"small_rock",      "name":"Small Rock",        "cat":IC_WEAPON,
     "slot":"throw", "base_dmg":1, "max_throws":45, "weight":5,  "value":0},
    {"id":"large_rock",      "name":"Large Rock",        "cat":IC_WEAPON,
     "slot":"throw", "base_dmg":2, "max_throws":20, "weight":10, "value":0},
    {"id":"dart",            "name":"Dart",              "cat":IC_WEAPON,
     "slot":"throw", "base_dmg":3, "max_throws":20, "weight":5,  "value":5},
    {"id":"spear",           "name":"Spear",             "cat":IC_WEAPON,
     "slot":"throw", "base_dmg":4, "max_throws":30, "weight":15, "value":15},
    {"id":"mac_plus",        "name":"Macintosh Plus",    "cat":IC_WEAPON,
     "slot":"throw", "base_dmg":5, "max_throws":1,  "weight":5,  "value":0},

    # ── ARMOR ─────────────────────────────────────────────────────────────────
    # base_ac added to armour class; higher = better protection
    {"id":"leather_armor",   "name":"Leather Armor",     "cat":IC_ARMOR,
     "slot":"armor",    "base_ac":1, "max_enchant":4, "weight":3,  "value":30},
    {"id":"chain_armor",     "name":"Chain Armor",       "cat":IC_ARMOR,
     "slot":"armor",    "base_ac":2, "max_enchant":4, "weight":6,  "value":100},
    {"id":"banded_armor",    "name":"Banded Armor",      "cat":IC_ARMOR,
     "slot":"armor",    "base_ac":3, "max_enchant":4, "weight":9,  "value":160},
    {"id":"plate_armor",     "name":"Plate Armor",       "cat":IC_ARMOR,
     "slot":"armor",    "base_ac":4, "max_enchant":4, "weight":15, "value":250},
    {"id":"elven_cloak",     "name":"Elven Cloak",       "cat":IC_ARMOR,
     "slot":"cloak",    "base_ac":1, "max_enchant":4, "weight":2,  "value":150},
    {"id":"shield",          "name":"Shield",            "cat":IC_ARMOR,
     "slot":"offhand",  "base_ac":1, "max_enchant":2, "weight":5,  "value":50},
    {"id":"helmet",          "name":"Helmet",            "cat":IC_ARMOR,
     "slot":"helmet",   "base_ac":1, "max_enchant":2, "weight":2,  "value":40},
    {"id":"gloves",          "name":"Gloves",            "cat":IC_ARMOR,
     "slot":"gauntlets","base_ac":1, "max_enchant":2, "weight":1,  "value":30},

    # ── POTIONS ───────────────────────────────────────────────────────────────
    {"id":"potion_confusion",    "name":"Potion of Confusion",
     "cat":IC_POTION, "effect":"confuse",       "temporary":True,
     "message":"Huh, what? Where?",              "power":20, "weight":1, "value":0},
    {"id":"potion_extra_healing","name":"Potion of Extra Healing",
     "cat":IC_POTION, "effect":"heal_major",    "temporary":False,
     "message":"You feel much better!",          "power":30, "weight":1, "value":150},
    {"id":"potion_resist_fire",  "name":"Potion of Resist Fire",
     "cat":IC_POTION, "effect":"resist_fire",   "temporary":True,
     "message":"You feel very cold.",            "power":40, "weight":1, "value":80},
    {"id":"potion_healing",      "name":"Potion of Healing",
     "cat":IC_POTION, "effect":"heal",          "temporary":False,
     "message":"You feel better.",              "power":15, "weight":1, "value":50},
    {"id":"potion_invisibility", "name":"Potion of Invisibility",
     "cat":IC_POTION, "effect":"invisible",     "temporary":True,
     "message":"Where did you go?",             "power":30, "weight":1, "value":100},
    {"id":"potion_levitation",   "name":"Potion of Levitation",
     "cat":IC_POTION, "effect":"levitate",      "temporary":True,
     "message":"You start to float.",           "power":25, "weight":1, "value":0},
    {"id":"potion_poison",       "name":"Potion of Poison",
     "cat":IC_POTION, "effect":"poison_drink",  "temporary":False,
     "message":"You feel sick.",                "power":5,  "weight":1, "value":0},
    {"id":"potion_speed",        "name":"Potion of Speed",
     "cat":IC_POTION, "effect":"haste",         "temporary":True,
     "message":"You are moving faster.",        "power":30, "weight":1, "value":80},
    {"id":"potion_muscle",       "name":"Potion of Muscle",
     "cat":IC_POTION, "effect":"str_up",        "temporary":False,
     "message":"You feel stronger!",            "power":1,  "weight":1, "value":100},
    {"id":"potion_resist_cold",  "name":"Potion of Resist Cold",
     "cat":IC_POTION, "effect":"resist_cold",   "temporary":True,
     "message":"You feel very warm.",           "power":40, "weight":1, "value":80},
    {"id":"potion_dexterity",    "name":"Potion of Dexterity",
     "cat":IC_POTION, "effect":"dex_up",        "temporary":False,
     "message":"You feel more skillful!",       "power":1,  "weight":1, "value":100},
    {"id":"potion_constitution", "name":"Potion of Constitution",
     "cat":IC_POTION, "effect":"con_up",        "temporary":False,
     "message":"You feel strange.",             "power":1,  "weight":1, "value":100},
    {"id":"potion_charisma",     "name":"Potion of Charisma",
     "cat":IC_POTION, "effect":"cha_up",        "temporary":False,
     "message":"Nothing seems to happen.",      "power":1,  "weight":1, "value":60},
    {"id":"potion_blindness",    "name":"Potion of Blindness",
     "cat":IC_POTION, "effect":"blind",         "temporary":True,
     "message":"I can't see!!!",               "power":20, "weight":1, "value":0},
    {"id":"potion_worthless",    "name":"Potion of Worthlessness",
     "cat":IC_POTION, "effect":"nothing",       "temporary":False,
     "message":"Nothing happens.",             "power":0,  "weight":1, "value":0},
    {"id":"potion_strength",     "name":"Potion of Strength",
     "cat":IC_POTION, "effect":"str_restore",   "temporary":False,
     "message":"You feel strong!!!",           "power":0,  "weight":1, "value":80},
    {"id":"potion_life",         "name":"Potion of Life",
     "cat":IC_POTION, "effect":"life_restore",  "temporary":False,
     "message":"You feel normal.",             "power":0,  "weight":1, "value":80},

    # ── SCROLLS ───────────────────────────────────────────────────────────────
    {"id":"scroll_gain_level",    "name":"Scroll of Gain Level",
     "cat":IC_SCROLL, "effect":"gain_level",    "temporary":False,
     "message":"You feel experienced!",         "weight":1, "value":200},
    {"id":"scroll_identify",      "name":"Scroll of Identify",
     "cat":IC_SCROLL, "effect":"identify",      "temporary":False,
     "message":"It's an identify scroll!",      "weight":1, "value":60},
    {"id":"scroll_enchant_armor", "name":"Scroll of Enchant Armor",
     "cat":IC_SCROLL, "effect":"enchant_armor", "temporary":False,
     "message":"Your armor glows!",             "weight":1, "value":120},
    {"id":"scroll_magic_mapping", "name":"Scroll of Magic Mapping",
     "cat":IC_SCROLL, "effect":"map_floor",     "temporary":False,
     "message":"There's a map on it!",          "weight":1, "value":100},
    {"id":"scroll_teleport",      "name":"Scroll of Teleportation",
     "cat":IC_SCROLL, "effect":"teleport",      "temporary":False,
     "message":"You're somewhere else!",        "weight":1, "value":80},
    {"id":"scroll_enchant_weapon","name":"Scroll of Enchant Weapon",
     "cat":IC_SCROLL, "effect":"enchant_weapon","temporary":False,
     "message":"Your weapon glows!",            "weight":1, "value":120},
    {"id":"scroll_protection",    "name":"Scroll of Protection",
     "cat":IC_SCROLL, "effect":"protect",       "temporary":True,
     "message":"You feel protected.",           "power":20, "weight":1, "value":100},
    {"id":"scroll_wishing",       "name":"Scroll of Wishing",
     "cat":IC_SCROLL, "effect":"wish",          "temporary":False,
     "message":"Wish for an object!",           "weight":1, "value":500},
    {"id":"scroll_intelligence",  "name":"Scroll of Intelligence",
     "cat":IC_SCROLL, "effect":"int_up",        "temporary":False,
     "message":"You feel intelligent!",         "weight":1, "value":100},
    {"id":"scroll_wisdom",        "name":"Scroll of Wisdom",
     "cat":IC_SCROLL, "effect":"wis_up",        "temporary":False,
     "message":"You feel wiser!",               "weight":1, "value":100},
    {"id":"scroll_remove_curse",  "name":"Scroll of Remove Curse",
     "cat":IC_SCROLL, "effect":"remove_curse",  "temporary":False,
     "message":"Your body glows.",              "weight":1, "value":80},
    {"id":"scroll_amnesia",       "name":"Scroll of Amnesia",
     "cat":IC_SCROLL, "effect":"amnesia",       "temporary":False,
     "message":"I forgot!!!",                   "weight":1, "value":0},
    {"id":"scroll_joke",          "name":"Scroll of Jokes",
     "cat":IC_SCROLL, "effect":"nothing",       "temporary":False,
     "message":"That was funny!",               "weight":1, "value":0},
    {"id":"scroll_words",         "name":"Scroll of Words",
     "cat":IC_SCROLL, "effect":"nothing",       "temporary":False,
     "message":"Nothing happens.",             "weight":1, "value":0},

    {
     "id":"scroll_scare",          "name":"Scroll of Scare Monster",
     "cat":IC_SCROLL, "effect":"scare_monsters",  "temporary":False,
     "message":"The monsters cower in terror!",
     "power":20,   "weight":1, "value":120,
    },
    {
     "id":"scroll_charm",          "name":"Scroll of Charm Monster",
     "cat":IC_SCROLL, "effect":"charm_monsters",  "temporary":False,
     "message":"A calming aura radiates from the scroll.",
     "power":30,   "weight":1, "value":150,
    },

    # ── WANDS ─────────────────────────────────────────────────────────────────
    {"id":"wand_lightning",   "name":"Wand of Lightning",
     "cat":IC_WAND, "effect":"wand_lightning",  "charges":5,  "dmg":8,
     "message":"A lightning bolt is released from the wand!",  "weight":1, "value":150},
    {"id":"wand_fire",        "name":"Wand of Fire",
     "cat":IC_WAND, "effect":"wand_fire",       "charges":7,  "dmg":6,
     "message":"A burst of flame is released from the wand!", "weight":1, "value":150},
    {"id":"wand_ice",         "name":"Wand of Ice",
     "cat":IC_WAND, "effect":"wand_ice",        "charges":7,  "dmg":6,
     "message":"A frosty beam is released from the wand!",   "weight":1, "value":150},
    {"id":"wand_death",       "name":"Wand of Death",
     "cat":IC_WAND, "effect":"wand_death",      "charges":3,  "dmg":999,
     "message":"A beam of death is released from the wand!", "weight":1, "value":500},
    {"id":"wand_striking",    "name":"Wand of Striking",
     "cat":IC_WAND, "effect":"wand_striking",   "charges":10, "dmg":4,
     "message":"It hits the monster!",                        "weight":1, "value":100},
    {"id":"wand_fear",        "name":"Wand of Fear",
     "cat":IC_WAND, "effect":"wand_fear",       "charges":8,  "dmg":0,
     "message":"The monster is frightened!",                  "weight":1, "value":120},
    {"id":"wand_digging",     "name":"Wand of Digging",
     "cat":IC_WAND, "effect":"wand_digging",    "charges":4,  "dmg":0,
     "message":"The wall crumbles!",                          "weight":1, "value":100},
    {"id":"wand_sleep",       "name":"Wand of Sleep",
     "cat":IC_WAND, "effect":"wand_sleep",      "charges":4,  "dmg":0,
     "message":"The monster falls asleep.",                   "weight":1, "value":120},
    {"id":"wand_polymorph",   "name":"Wand of Polymorph",
     "cat":IC_WAND, "effect":"wand_polymorph",  "charges":5,  "dmg":0,
     "message":"The monster's form blurs!",                   "weight":1, "value":200},
    {"id":"wand_teleport",    "name":"Wand of Teleport",
     "cat":IC_WAND, "effect":"wand_teleport",   "charges":5,  "dmg":0,
     "message":"The monster disappears!",                     "weight":1, "value":120},
    {"id":"wand_invisibility","name":"Wand of Invisibility",
     "cat":IC_WAND, "effect":"wand_invisibility","charges":5, "dmg":0,
     "message":"The monster disappears!",                     "weight":1, "value":100},

    # ── RINGS ─────────────────────────────────────────────────────────────────
    {"id":"ring_resist_fire", "name":"Ring of Resist Fire",
     "cat":IC_RING, "slot":"ring", "effect":"ring_resist_fire",
     "cursed":False, "max_enchant":2,
     "message":"You feel strange.", "weight":1, "value":100},
    {"id":"ring_resist_cold", "name":"Ring of Resist Cold",
     "cat":IC_RING, "slot":"ring", "effect":"ring_resist_cold",
     "cursed":False, "max_enchant":2,
     "message":"You feel strange.", "weight":1, "value":100},
    {"id":"ring_regeneration","name":"Ring of Regeneration",
     "cat":IC_RING, "slot":"ring", "effect":"ring_regen",
     "cursed":False, "max_enchant":2,
     "message":"You feel strange.", "weight":1, "value":300},
    {"id":"ring_slowness",    "name":"Ring of Slowness",
     "cat":IC_RING, "slot":"ring", "effect":"ring_slow",
     "cursed":True,  "max_enchant":0,
     "message":"You feel different.", "weight":1, "value":0},
    {"id":"ring_hunger",      "name":"Ring of Hunger",
     "cat":IC_RING, "slot":"ring", "effect":"ring_hunger",
     "cursed":True,  "max_enchant":0,
     "message":"You feel strange.", "weight":1, "value":0},
    {"id":"ring_xray",        "name":"Ring of X-Ray",
     "cat":IC_RING, "slot":"ring", "effect":"ring_xray",
     "cursed":False, "max_enchant":2,
     "message":"Your vision changes.", "weight":1, "value":200},
    {"id":"ring_monster",     "name":"Ring of Monster Attraction",
     "cat":IC_RING, "slot":"ring", "effect":"ring_monster",
     "cursed":True,  "max_enchant":0,
     "message":"You feel strange.", "weight":1, "value":0},

    # ── FOOD ──────────────────────────────────────────────────────────────────
    {"id":"food_rotten",   "name":"Food Ration",     "cat":IC_FOOD,
     "subtype":"rotten",  "food_val":0,   "poisonous":True,
     "message":"This food is rotten!",           "weight":3, "value":0},
    {"id":"food_bland",    "name":"Food Ration",     "cat":IC_FOOD,
     "subtype":"bland",   "food_val":400,
     "message":"Tastes nothing.",                "weight":3, "value":3},
    {"id":"food_good",     "name":"Food Ration",     "cat":IC_FOOD,
     "subtype":"good",    "food_val":600,
     "message":"Tastes good!",                   "weight":3, "value":5},
    {"id":"fruit",         "name":"Fruit",           "cat":IC_FOOD,
     "subtype":"fruit",   "food_val":200,
     "message":"Yum!",                           "weight":1, "value":2},
    {"id":"spider",        "name":"Spider",          "cat":IC_FOOD,
     "subtype":"spider",  "food_val":200,
     "message":"Yuck!",                          "weight":1, "value":0},
    {"id":"lizard",        "name":"Lizard",          "cat":IC_FOOD,
     "subtype":"lizard",  "food_val":600,
     "message":"Surprisingly filling!",          "weight":5, "value":2},

    # ── GEMS ──────────────────────────────────────────────────────────────────
    {"id":"diamond", "name":"Diamond", "cat":IC_JEWEL, "weight":2, "value":15000},
    {"id":"ruby",    "name":"Ruby",    "cat":IC_JEWEL, "weight":2, "value":6000},
    {"id":"emerald", "name":"Emerald", "cat":IC_JEWEL, "weight":2, "value":5000},

    # ── QUEST ITEM ────────────────────────────────────────────────────────────
    {"id":"orb_of_carnos", "name":"Orb of Carnos", "cat":IC_MISC,
     "weight":10, "value":0, "quest":True},
    {"id":"plastic_orb",   "name":"Plastic Orb",   "cat":IC_MISC,
     "weight":1,  "value":0, "fake":True},
]

ITEM_BY_ID = {i["id"]: i for i in ITEMS}

def get_item(iid: str) -> dict:
    return ITEM_BY_ID[iid]

def items_by_category(cat: str) -> list:
    return [i for i in ITEMS if i["cat"] == cat]

def items_for_floor(floor: int, rng) -> list:
    """Weighted pool of items appropriate for the given floor depth."""
    from constants import (IC_WEAPON, IC_ARMOR, IC_POTION, IC_SCROLL,
                           IC_WAND, IC_RING, IC_FOOD, IC_JEWEL)
    pool = []
    # Food always available
    pool += [i for i in ITEMS if i["cat"] == IC_FOOD] * 3
    # Weapons scaled to floor
    for it in ITEMS:
        if it["cat"] == IC_WEAPON and it.get("base_dmg", 0) <= max(1, floor // 5 + 2):
            pool.append(it)
    # Armor scaled to floor
    for it in ITEMS:
        if it["cat"] == IC_ARMOR and it.get("base_ac", 0) <= max(1, floor // 8 + 1):
            pool.append(it)
    # Potions always
    pool += items_by_category(IC_POTION) * 2
    # Scrolls from floor 2
    if floor >= 2:
        pool += items_by_category(IC_SCROLL) * 2
    # Wands from floor 5
    if floor >= 5:
        pool += items_by_category(IC_WAND)
    # Rings from floor 8
    if floor >= 8:
        pool += items_by_category(IC_RING)
    # Gems from floor 15
    if floor >= 15:
        pool += items_by_category(IC_JEWEL) * 2
    return pool


def items_by_category_for_floor(cat: str, floor: int) -> list:
    """Return eligible items of a single category for the given floor depth.
    Used by the per-category spawn system in dungeon._populate()."""
    from constants import IC_WEAPON, IC_ARMOR
    if cat == IC_WEAPON:
        # Corrected unlock: floor//4+2 gives gradual progression
        #   floors 1-3  → max_dmg=2  (Dagger, Leather Whip)
        #   floors 4-7  → max_dmg=3  (+ Long Sword)
        #   floors 8-11 → max_dmg=4  (+ Mace)
        #   floors 12-15→ max_dmg=5  (+ Two-Handed Sword)
        #   floors 16+  → max_dmg=6  (+ Death Blade)
        max_dmg = max(2, floor // 4 + 2)
        return [i for i in ITEMS
                if i["cat"] == IC_WEAPON
                and i.get("slot") != "throw"
                and i.get("slot") != "offhand"
                and i.get("base_dmg", 0) <= max_dmg]
    elif cat == IC_ARMOR:
        max_ac = max(1, floor // 8 + 1)
        return [i for i in ITEMS
                if i["cat"] == IC_ARMOR
                and i.get("base_ac", 0) <= max_ac]
    else:
        return [i for i in ITEMS if i["cat"] == cat]


def throwing_items_for_floor(floor: int) -> list:
    """Return throwing-slot items eligible for the given floor.
    All throwing items are available from floor 1 except the Mac Plus (floor 15+)."""
    from constants import IC_WEAPON
    return [i for i in ITEMS
            if i["cat"] == IC_WEAPON
            and i.get("slot") == "throw"
            and (i["id"] != "mac_plus" or floor >= 15)]
