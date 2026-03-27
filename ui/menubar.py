# ui/menubar.py — Mac-style menu bar with drop-down panels
# v0.101.20260307
#
# Menus match the original Dungeon of Doom (1985):
#   File | Control | Use | Inventory | Help
#
# All items are disabled (greyed out) for now — actions wired in later steps.
# Aesthetic: black-on-white, Chicago-style, matching the original Mac UI.

import pygame
from constants import (
    MENU_H, SCREEN_W, TOTAL_FLOORS,
    FONT_MONO, FONT_SZ_MD, FONT_SZ_SM,
    C_MENU_BG, C_MENU_TEXT, C_MENU_TEXT_DIM, C_MENU_SEP,
    C_MENU_HIGHLIGHT, C_MENU_HI_TEXT,
    C_MENU_DROP_BG, C_MENU_DROP_BRD,
    C_BLACK, C_WHITE,
)
from engine.game import GameState

# ── Menu data ─────────────────────────────────────────────────────────────────
# Each item is a dict:
#   {"label": str}                    — normal item (disabled for now)
#   {"label": str, "shortcut": "^X"} — item with keyboard shortcut
#   {"sep": True}                     — horizontal separator
#   {"label": str, "check": True}     — checkmark toggle item

_SEP = {"sep": True}

MENU_DATA = {
    "File": [
        {"label": "New…",       "action": "file_new"},
        {"label": "Open…",      "action": "file_open"},
        {"label": "Close",      "action": "file_close"},
        _SEP,
        {"label": "Save",       "action": "file_save"},
        {"label": "Save As…",   "action": "file_save_as"},
        _SEP,
        {"label": "Quit",       "action": "file_quit"},
    ],
    "Control": [
        {"label": "Pickup Mode",    "action": "ctrl_pickup_mode",  "check_key": "pickup_mode"},
        _SEP,
        {"label": "Sound",          "check_key": "sound_on"},
        {"label": "Pause",          "action": "ctrl_pause"},
        _SEP,
        {"label": "Adjust Volume…"},
    ],
    "Use": [
        {"label": "Drink Potion…",   "shortcut": "Q",  "action": "use_potion"},
        {"label": "Read Scroll…",    "shortcut": "R",  "action": "use_scroll"},
        {"label": "Zap Wand…",       "shortcut": "Z",  "action": "use_wand"},
        {"label": "Throw Item…",     "shortcut": "T",  "action": "use_throw"},
        {"label": "Eat Food…",       "shortcut": "E",  "action": "use_food"},
        _SEP,
        {"label": "Wear Armor…",     "shortcut": "^U", "action": "use_wear_armor"},
        {"label": "Wear Ring…",      "shortcut": "^J", "action": "use_wear_ring"},
        {"label": "Wield Weapon…",   "shortcut": "^M", "action": "use_wield"},
        _SEP,
        {"label": "Remove Armor…",   "shortcut": "^Y", "action": "use_remove_armor"},
        {"label": "Remove Rings…",   "shortcut": "^H", "action": "use_remove_rings"},
        {"label": "Remove Weapons…", "shortcut": "^N", "action": "use_remove_weapon"},
    ],
    "Inventory": [
        {"label": "Get an Item…",              "shortcut": "G",  "action": "inv_get_item"},
        _SEP,
        {"label": "Drop an Item…",             "shortcut": "D",  "action": "inv_drop_item"},
        {"label": "Drop Scrolls and Potions…", "action": "inv_drop_scrolls_potions"},
        {"label": "Drop Rings and Wands…",     "action": "inv_drop_rings_wands"},
        {"label": "Drop Armor and Weapons…",   "action": "inv_drop_armor_weapons"},
        {"label": "Drop Food and Other…",      "action": "inv_drop_food_other"},
        _SEP,
        {"label": "Drop ALL Items",            "action": "inv_drop_all"},
        {"label": "Drop Last Items Picked Up", "shortcut": "L",  "action": "inv_drop_last"},
        _SEP,
        {"label": "Inventory",                 "shortcut": "I",  "action": "inv_open"},
    ],
    "Help": [
        {"label": "File Menu"},
        {"label": "Edit and Control Menus"},
        {"label": "Use Menu"},
        {"label": "Inventory Menu"},
        {"label": "General"},
        {"label": "Keyboard Commands"},
        {"label": "Rumors"},
        _SEP,
        {"label": "Hall of Legends"},
    ],
}

MENU_ORDER = ["File", "Control", "Use", "Inventory", "Help"]

# ── Layout constants ───────────────────────────────────────────────────────────
_ITEM_H      = 26    # height of one menu item row
_SEP_H       = 9     # height of separator row
_PAD_X       = 18   # horizontal padding inside dropdown
_CHECK_W     = 18   # width reserved for checkmark column
_SHORTCUT_GAP= 32   # gap between label and shortcut text
_DROP_MIN_W  = 180  # minimum dropdown width
_TITLE_PAD   = 10   # horizontal padding around menu title in bar


# ── Font cache ────────────────────────────────────────────────────────────────
_fonts: dict = {}

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(FONT_MONO, size, bold=bold)
    return _fonts[key]

# DejaVu Sans Mono — used only for glyphs missing from Courier New/Liberation:
#   checkmark ✓ (U+2713), ballot box □ (U+2610), command ^ fallback
_DEJAVU_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_sym_fonts: dict = {}

def _sym_font(size: int) -> pygame.font.Font:
    if size not in _sym_fonts:
        try:
            _sym_fonts[size] = pygame.font.Font(_DEJAVU_MONO, size)
        except Exception:
            _sym_fonts[size] = _font(size)   # graceful fallback
    return _sym_fonts[size]


# ── MenuBar class ─────────────────────────────────────────────────────────────

class MenuBar:

    def __init__(self, surf: pygame.Surface):
        self.surf    = surf
        self.W       = surf.get_width()
        self._rects: list = []           # [(pygame.Rect, menu_name)]
        self._item_rects: list = []      # [(pygame.Rect, menu_name, item)] for dropdown
        self.active: str | None = None   # open menu name

    # ── Public API ────────────────────────────────────────────────────────────

    def hit_test(self, sx: int, sy: int) -> str | None:
        """Return menu name if screen point hits a title bar entry."""
        for rect, name in self._rects:
            if rect.collidepoint(sx, sy):
                return name
        return None

    def hit_test_item(self, sx: int, sy: int) -> dict | None:
        """Return the item dict clicked in the open dropdown, or None."""
        for rect, menu_name, item in self._item_rects:
            if item.get("sep"):
                continue
            if rect.collidepoint(sx, sy) and item.get("action"):
                return item
        return None

    def click_title(self, sx: int, sy: int) -> str | None:
        """Handle a click on the title bar row. Toggles dropdown."""
        name = self.hit_test(sx, sy)
        self.active = None if name == self.active else name
        return name

    # kept for backward compat
    def click(self, sx: int, sy: int) -> str | None:
        return self.click_title(sx, sy)

    def dismiss(self):
        self.active = None

    # ── Draw menu bar (title row) ─────────────────────────────────────────────

    def draw(self, game: GameState):
        s = self.surf
        s.fill(C_MENU_BG)

        # Bottom border
        pygame.draw.line(s, C_MENU_SEP, (0, MENU_H - 1), (self.W, MENU_H - 1), 1)

        f   = _font(FONT_SZ_MD, bold=True)
        ih  = f.size("A")[1]
        mid = (MENU_H - ih) // 2

        self._rects = []
        x = 14

        for name in MENU_ORDER:
            img = f.render(name, True, C_MENU_TEXT)
            iw  = img.get_width()
            rect = pygame.Rect(x - _TITLE_PAD, 0, iw + _TITLE_PAD * 2, MENU_H)

            if name == self.active:
                # Highlighted title: filled blue rect, white text
                pygame.draw.rect(s, C_MENU_HIGHLIGHT, rect)
                img = f.render(name, True, C_MENU_HI_TEXT)

            s.blit(img, (x, mid))
            # Rect is in surf coords = screen coords (surf_menu starts at 0,0)
            self._rects.append((rect, name))
            x += iw + _TITLE_PAD * 2 + 8

        # Right side: floor / turn info
        if game.player:
            fi   = _font(FONT_SZ_SM, bold=False)
            label = f"Floor {game.floor} / {TOTAL_FLOORS}   Turn {game.turn}"
            img   = fi.render(label, True, C_MENU_SEP)
            s.blit(img, (self.W - img.get_width() - 14,
                         (MENU_H - img.get_height()) // 2))

    # ── Draw dropdown (call from renderer AFTER drawing game, before flip) ────

    def draw_dropdown(self, screen: pygame.Surface, check_states: dict = None):
        """
        If a menu is open, draw its dropdown panel directly onto the screen
        surface so it renders on top of everything else.
        """
        if not self.active or self.active not in MENU_DATA:
            return

        items = MENU_DATA[self.active]

        # Find title rect for x-position
        title_rect = None
        for rect, name in self._rects:
            if name == self.active:
                title_rect = rect
                break
        if not title_rect:
            return

        f_item  = _font(FONT_SZ_MD, bold=False)
        f_check = _sym_font(FONT_SZ_MD)   # needs ✓ glyph
        f_short = _sym_font(FONT_SZ_SM)   # needs ^ shortcut glyph

        # Measure dropdown width
        max_label_w  = 0
        max_short_w  = 0
        for item in items:
            if item.get("sep"):
                continue
            lw = f_item.size(item["label"])[0]
            raw_sc = item.get("shortcut", "")
            sw = f_short.size(raw_sc)[0] if raw_sc else 0
            max_label_w = max(max_label_w, lw)
            max_short_w = max(max_short_w, sw)

        has_shortcuts = max_short_w > 0
        inner_w = (_CHECK_W + _PAD_X + max_label_w
                   + (_SHORTCUT_GAP + max_short_w if has_shortcuts else 0)
                   + _PAD_X)
        drop_w  = max(inner_w, _DROP_MIN_W)

        # Measure total height
        drop_h = 4  # top padding
        for item in items:
            drop_h += _SEP_H if item.get("sep") else _ITEM_H
        drop_h += 4  # bottom padding

        # Position: below the title, aligned to its left edge (but stay on screen)
        drop_x = title_rect.left
        drop_y = MENU_H
        if drop_x + drop_w > SCREEN_W:
            drop_x = SCREEN_W - drop_w - 2

        # Draw shadow (1px offset, semi-transparent sim with dark rect)
        shadow = pygame.Rect(drop_x + 3, drop_y + 3, drop_w, drop_h)
        shadow_surf = pygame.Surface((drop_w, drop_h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        screen.blit(shadow_surf, (drop_x + 3, drop_y + 3))

        # Draw panel
        panel = pygame.Rect(drop_x, drop_y, drop_w, drop_h)
        pygame.draw.rect(screen, C_MENU_DROP_BG, panel)
        pygame.draw.rect(screen, C_MENU_DROP_BRD, panel, 1)

        # Draw items
        self._item_rects = []   # rebuilt each frame
        cy = drop_y + 4
        for item in items:
            if item.get("sep"):
                line_y = cy + _SEP_H // 2
                pygame.draw.line(screen, C_MENU_SEP,
                                 (drop_x + 1, line_y),
                                 (drop_x + drop_w - 2, line_y), 1)
                self._item_rects.append((pygame.Rect(drop_x, cy, drop_w, _SEP_H),
                                         self.active, item))
                cy += _SEP_H
                continue

            item_rect = pygame.Rect(drop_x, cy, drop_w, _ITEM_H)
            self._item_rects.append((item_rect, self.active, item))

            # Active items (have "action" key) are black; disabled are grey
            col = C_MENU_TEXT if item.get("action") else C_MENU_TEXT_DIM

            # Checkmark column — drawn with pygame.draw (font-glyph independent)
            ck_key  = item.get("check_key", "")
            checked = (check_states or {}).get(ck_key, item.get("check", False))
            if ck_key or item.get("check"):
                bx = drop_x + _PAD_X + 1
                by = cy + (_ITEM_H - 12) // 2
                # Outer box
                pygame.draw.rect(screen, col, (bx, by, 12, 12), 1)
                if checked:
                    # Filled interior
                    pygame.draw.rect(screen, col, (bx+2, by+2, 8, 8))
                    # Tick mark: two lines for ✓ shape
                    pygame.draw.line(screen, C_MENU_DROP_BG, (bx+2, by+5), (bx+5, by+9), 2)
                    pygame.draw.line(screen, C_MENU_DROP_BG, (bx+5, by+9), (bx+10, by+2), 2)

            # Label
            lbl = f_item.render(item["label"], True, col)
            screen.blit(lbl, (drop_x + _CHECK_W + _PAD_X,
                               cy + (_ITEM_H - lbl.get_height()) // 2))

            # Keyboard shortcut (right-aligned)
            if item.get("shortcut"):
                sh = f_short.render(item["shortcut"], True, col)
                screen.blit(sh, (drop_x + drop_w - _PAD_X - sh.get_width(),
                                  cy + (_ITEM_H - sh.get_height()) // 2))

            cy += _ITEM_H
