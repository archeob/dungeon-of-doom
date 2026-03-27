# entities/item.py — Item entity v0.109

from data.items import get_item
from constants import IC_POTION, IC_SCROLL, IC_WAND, IC_RING

# Categories that need identification before true name is shown
_NEEDS_ID = {IC_POTION, IC_SCROLL, IC_WAND, IC_RING}


class Item:
    def __init__(self, item_id: str, x: int, y: int, enchant: int = 0):
        self.id      = item_id
        data         = get_item(item_id)
        self.name    = data["name"]
        self.cat     = data["cat"]
        self.data    = dict(data)
        self.x       = x
        self.y       = y
        # Negative enchant implies cursed quality for weapons/armor
        self.enchant = enchant
        _enc_cats    = {"weapon", "armor", "ring"}
        if self.cat in _enc_cats:
            self.cursed = enchant < 0 or data.get("cursed", False)
        else:
            self.cursed = data.get("cursed", False)
        self.charges = data.get("charges", 0)
        self.throws  = data.get("max_throws", 0)

    def display_name(self, id_map: dict = None, identified: set = None) -> str:
        """Return the name shown to the player.

        For potions/scrolls/wands/rings: unidentified alias until identified.
        For weapons/armor: true name + enchant suffix.
        """
        iid = self.id
        if self.cat in _NEEDS_ID and id_map and (identified is None or iid not in identified):
            base = id_map.get(iid, self.name)
        else:
            base = self.name

        if self.enchant > 0:  base += f" +{self.enchant}"
        if self.enchant < 0:  base += f" {self.enchant}"
        if self.cursed and (identified is None or iid in (identified or set())):
            base += " {cursed}"
        return base

    def to_dict(self) -> dict:
        """Convert to the inventory dict format used by game/player."""
        d = dict(self.data)
        _enc_cats = {"weapon", "armor", "ring"}
        d.update({
            "item_id":      self.id,
            "identified":   False,
            "enchant_known": False,   # revealed by scroll or expert class on equip
            "cursed":       self.cursed,
            "enchant":      self.enchant,
            "charges":      self.charges,
            "throws":       self.throws,
        })
        return d

    @property
    def glyph(self) -> str:
        return {
            "weapon": "/", "armor": "]", "potion": "!",
            "scroll": "?", "ring":  "=", "wand":   "\\",
            "food":   "%", "jewel": "*", "misc":    "&",
        }.get(self.cat, ".")

    @property
    def color(self):
        return {
            "weapon":  (160, 160, 200),
            "armor":   (200, 160,  80),
            "potion":  (200,  80,  80),
            "scroll":  (200, 200, 120),
            "ring":    (220, 180,  40),
            "wand":    (160, 100, 200),
            "food":    (160, 200, 100),
            "jewel":   (100, 200, 220),
            "misc":    (200, 200, 200),
        }.get(self.cat, (200, 200, 200))
