# ui/screens.py — Title, char creation, death/win screens
# v0.104.20260307

import pygame
from constants import *
from constants import DIFF_ORDER, DIFF_LABEL, DIFF_DESC
from data.classes import all_classes, CLASS_ORDER

# ── Font helpers ──────────────────────────────────────────────────────────────

_fonts = {}

def _font(size=FONT_SZ_MD, bold=True, mono=True):
    k = (size, bold, mono)
    if k not in _fonts:
        if mono:
            _fonts[k] = pygame.font.SysFont(FONT_MONO, size, bold=bold)
        else:
            _fonts[k] = pygame.font.SysFont("serif", size, bold=bold)
    return _fonts[k]

# FreeSerifBold — kept for buttons only
_GOTHIC_PATH = "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
_gothic_cache = {}

def _gothic(size):
    if size not in _gothic_cache:
        try:
            _gothic_cache[size] = pygame.font.Font(_GOTHIC_PATH, size)
        except Exception:
            _gothic_cache[size] = pygame.font.SysFont("serif", size, bold=True)
    return _gothic_cache[size]

# KaTeX Fraktur Bold — Old English display font for all headings/titles
import os as _os
_FRAKTUR_PATH = _os.path.join(_os.path.dirname(__file__), "..", "assets", "KaTeX_Fraktur-Bold.ttf")
_fraktur_cache = {}

def _fraktur(size):
    if size not in _fraktur_cache:
        try:
            _fraktur_cache[size] = pygame.font.Font(_FRAKTUR_PATH, size)
        except Exception:
            _fraktur_cache[size] = _gothic(size)   # graceful fallback
    return _fraktur_cache[size]


def _t(surf, txt, x, y, color=C_TEXT, size=FONT_SZ_MD, bold=True,
       center=False, mono=True):
    img = _font(size, bold, mono).render(str(txt), True, color)
    if center:
        x -= img.get_width() // 2
    surf.blit(img, (x, y))
    return img.get_width()


def _fraktur_text(surf, txt, cx, y, color=(0, 0, 0), size=90, shadow=True):
    """Render text in Fraktur (Old English), centred on cx, with optional drop-shadow."""
    f   = _fraktur(size)
    img = f.render(txt, True, color)
    x   = cx - img.get_width() // 2
    if shadow:
        sh = f.render(txt, True, (100, 100, 100))
        surf.blit(sh, (x + 3, y + 3))
    surf.blit(img, (x, y))
    return img.get_width(), img.get_height()

# Keep old name as alias so existing call sites still work
def _gothic_text(surf, txt, cx, y, color=(0, 0, 0), size=90, shadow=True):
    return _fraktur_text(surf, txt, cx, y, color, size, shadow)


# ── Shared drawing primitives ─────────────────────────────────────────────────

def _box(surf, x, y, w, h, bg=(255,255,255), border=(0,0,0), bw=2, radius=0):
    if bg:
        if radius:
            pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=radius)
        else:
            pygame.draw.rect(surf, bg, (x, y, w, h))
    if border and bw:
        if radius:
            pygame.draw.rect(surf, border, (x, y, w, h), bw, border_radius=radius)
        else:
            pygame.draw.rect(surf, border, (x, y, w, h), bw)


def _corner_ornaments(surf, x, y, w, h, size=18, color=(0,0,0)):
    """Draw small L-shaped corner marks inside a box for a decorative look."""
    corners = [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]
    dirs    = [(1,1),  (-1,1),   (1,-1),    (-1,-1)]
    for (cx2, cy2), (dx, dy) in zip(corners, dirs):
        pygame.draw.line(surf, color, (cx2, cy2), (cx2 + dx*size, cy2), 2)
        pygame.draw.line(surf, color, (cx2, cy2), (cx2, cy2 + dy*size), 2)


# ── Title Screen ──────────────────────────────────────────────────────────────

class TitleScreen:
    # Button layout
    _BTN_W = 340
    _BTN_H = 52
    _BTN_RADIUS = 6

    # Button action ids
    BTN_NEW    = "new_game"
    BTN_OPEN   = "open_game"
    BTN_RESUME = "resume_game"
    BTN_QUIT   = "quit"

    def __init__(self, surf):
        self.surf  = surf
        self.W     = surf.get_width()
        self.H     = surf.get_height()
        self._btn_rects: list = []   # [(pygame.Rect, action_id, enabled)]
        self._hover: str | None = None

    def handle_click(self, sx, sy) -> str | None:
        """Return action_id if an enabled button was clicked, else None."""
        for rect, action, enabled in self._btn_rects:
            if enabled and rect.collidepoint(sx, sy):
                return action
        return None

    def handle_motion(self, sx, sy):
        """Update hover state. Call on MOUSEMOTION."""
        self._hover = None
        for rect, action, enabled in self._btn_rects:
            if enabled and rect.collidepoint(sx, sy):
                self._hover = action
                break

    def draw(self, tick, has_active_game: bool = False):
        import os as _os
        from engine.save import RESUME_PATH as _RESUME_PATH
        _resume_enabled = has_active_game or _os.path.exists(_RESUME_PATH)
        s  = self.surf
        W, H = self.W, self.H
        cx = W // 2

        # ── Background ───────────────────────────────────────────────────────
        s.fill(C_WHITE)
        # Outer border
        pygame.draw.rect(s, C_BLACK, (0, 0, W, H), 3)
        # Inner inset border
        pygame.draw.rect(s, (80, 80, 80), (8, 8, W-16, H-16), 1)

        # ── Gothic title ─────────────────────────────────────────────────────
        TITLE_Y = 28
        tw, th = _gothic_text(s, "The Dungeon of Doom", cx, TITLE_Y,
                               color=C_BLACK, size=96, shadow=True)

        # Subtitle
        sub = "Original by John Raymonds & Woodrose Editions  ·  1985 Macintosh"
        _t(s, sub, cx, TITLE_Y + th + 10, (60, 60, 60),
           FONT_SZ_LG, bold=False, center=True, mono=False)

        # Ornamental rule under title
        rule_y = TITLE_Y + th + 46
        pygame.draw.line(s, C_BLACK, (60, rule_y), (W-60, rule_y), 2)
        # Diamond ornaments on the rule
        for ox in [cx - 200, cx, cx + 200]:
            pygame.draw.polygon(s, C_BLACK,
                [(ox, rule_y-5), (ox+5, rule_y), (ox, rule_y+5), (ox-5, rule_y)])

        # ── Layout geometry ───────────────────────────────────────────────────
        CONTENT_TOP  = rule_y + 16
        CONTENT_BTM  = H - 52        # above footer
        COL_GAP      = 30
        LEFT_W       = 680
        RIGHT_W      = W - LEFT_W - COL_GAP*3 - 60  # ≈860 at 1920
        LEFT_X       = 60
        RIGHT_X      = LEFT_X + LEFT_W + COL_GAP*2

        # ── LEFT COLUMN — Title illustration + credits ────────────────────────
        ART_H = 440
        # Try to load the title background image
        _art_loaded = False
        try:
            import os as _os2
            _art_path = _os2.path.normpath(_os2.path.join(
                _os2.path.dirname(__file__), "..", "assets", "sprites", "title_bg.png"))
            if _os2.path.isfile(_art_path):
                _art_img = pygame.image.load(_art_path).convert()
                # Scale to fill the art box proportionally (cover, not fit)
                _iw, _ih = _art_img.get_size()
                _scale = max(LEFT_W / _iw, ART_H / _ih)
                _sw, _sh = int(_iw * _scale), int(_ih * _scale)
                _art_img = pygame.transform.smoothscale(_art_img, (_sw, _sh))
                # Centre-crop to LEFT_W × ART_H
                _ox = (_sw - LEFT_W) // 2
                _oy = (_sh - ART_H)  // 2
                _crop = _art_img.subsurface(pygame.Rect(_ox, _oy, LEFT_W, ART_H))
                s.blit(_crop, (LEFT_X, CONTENT_TOP))
                # Thin border over image
                pygame.draw.rect(s, C_BLACK,
                                 (LEFT_X, CONTENT_TOP, LEFT_W, ART_H), 2)
                _art_loaded = True
        except Exception:
            pass
        if not _art_loaded:
            _box(s, LEFT_X, CONTENT_TOP, LEFT_W, ART_H,
                 bg=(245, 243, 238), border=C_BLACK, bw=2)
            _corner_ornaments(s, LEFT_X, CONTENT_TOP, LEFT_W, ART_H,
                               size=22, color=C_BLACK)
            art_cx = LEFT_X + LEFT_W // 2
            art_cy = CONTENT_TOP + ART_H // 2
            _box(s, LEFT_X+20, CONTENT_TOP+20, LEFT_W-40, ART_H-40,
                 bg=None, border=(160, 155, 145), bw=1)
            _t(s, "[ Game Illustration ]", art_cx, art_cy - 40,
               (140, 135, 125), FONT_SZ_LG, bold=False, center=True, mono=False)
            _gothic_text(s, "The Dungeon of Doom", art_cx, art_cy,
                         color=(160, 155, 145), size=42, shadow=False)
            _t(s, "Artwork to be added in a future update", art_cx, art_cy + 55,
               (170, 165, 155), FONT_SZ_SM, bold=False, center=True, mono=False)

        # Credits block below art
        cred_y = CONTENT_TOP + ART_H + 24
        credits = [
            ("Original Game", "John Raymonds & Woodrose Editions  ·  1985"),
            ("Platform",      "Apple Macintosh  ·  System 1.0"),
            ("Recreation",    "Python + Pygame  ·  2026"),
            ("Producer",      "Sébastien Racine"),
        ]
        for label, value in credits:
            _t(s, f"{label}:", LEFT_X, cred_y, (80, 80, 80),
               FONT_SZ_SM, bold=True, mono=False)
            _t(s, value, LEFT_X + 140, cred_y, (40, 40, 40),
               FONT_SZ_SM, bold=False, mono=False)
            cred_y += 24

        # ── RIGHT COLUMN — Hall of Fame + Buttons ─────────────────────────
        HOF_H = 358
        _box(s, RIGHT_X, CONTENT_TOP, RIGHT_W, HOF_H,
             bg=(248, 248, 248), border=C_BLACK, bw=2)
        _corner_ornaments(s, RIGHT_X, CONTENT_TOP, RIGHT_W, HOF_H,
                           size=22, color=C_BLACK)

        # Hall of Fame header
        hof_cx = RIGHT_X + RIGHT_W // 2
        _gothic_text(s, "Hall of Fame", hof_cx, CONTENT_TOP + 12,
                     color=C_BLACK, size=40, shadow=False)

        # Separator under header
        hsep_y = CONTENT_TOP + 60
        pygame.draw.line(s, (160, 160, 160),
                         (RIGHT_X+14, hsep_y), (RIGHT_X+RIGHT_W-14, hsep_y), 1)

        # Column headers
        COL_RANK    = RIGHT_X + 14
        COL_NAME    = RIGHT_X + 46
        COL_CLS     = RIGHT_X + 200
        COL_LV      = RIGHT_X + 244
        COL_FL      = RIGHT_X + 278
        COL_OUTCOME = RIGHT_X + 316
        COL_SCORE   = RIGHT_X + RIGHT_W - 14   # right-aligned
        HOF_MAX     = 10

        row_y = hsep_y + 8
        dim = (110, 110, 110)
        _t(s, "#",      COL_RANK,    row_y, dim, FONT_SZ_SM, bold=True,  mono=True)
        _t(s, "Name",   COL_NAME,    row_y, dim, FONT_SZ_SM, bold=True,  mono=False)
        _t(s, "Cls",    COL_CLS,     row_y, dim, FONT_SZ_SM, bold=True,  mono=True)
        _t(s, "Lv",     COL_LV,      row_y, dim, FONT_SZ_SM, bold=True,  mono=True)
        _t(s, "Fl",     COL_FL,      row_y, dim, FONT_SZ_SM, bold=True,  mono=True)
        _t(s, "Cause",  COL_OUTCOME, row_y, dim, FONT_SZ_SM, bold=True,  mono=False)
        _gh = _font(FONT_SZ_SM, bold=True, mono=True).render("Glory", True, dim)
        s.blit(_gh, (COL_SCORE - _gh.get_width(), row_y))
        row_y += 18
        pygame.draw.line(s, (200, 200, 200),
                         (RIGHT_X+14, row_y), (RIGHT_X+RIGHT_W-14, row_y), 1)
        row_y += 5

        from engine.hof import load_hof as _load_hof, short_outcome as _short_out, class_abbrev as _cls_ab
        _hof_entries = _load_hof()

        for _rank in range(1, HOF_MAX + 1):
            if _rank - 1 < len(_hof_entries):
                _e = _hof_entries[_rank - 1]
                _is_win   = "escaped" in _e["outcome"].lower() or "orb" in _e["outcome"].lower()
                _nc       = (175, 135, 25) if _is_win else (40, 40, 40)
                _sc       = (175, 135, 25) if _is_win else (40, 40, 40)
                _cc       = (135,  95, 15) if _is_win else (100, 100, 100)
                _t(s, f"{_rank}.",              COL_RANK,    row_y, (120,120,120), FONT_SZ_SM, bold=False, mono=True)
                _t(s, _e["name"][:18],          COL_NAME,    row_y, _nc,           FONT_SZ_SM, bold=False, mono=False)
                _t(s, _cls_ab(_e["class_key"]), COL_CLS,     row_y, (80,80,80),    FONT_SZ_SM, bold=False, mono=True)
                _t(s, str(_e["char_level"]),    COL_LV,      row_y, (80,80,80),    FONT_SZ_SM, bold=False, mono=True)
                _t(s, str(_e["dungeon_floor"]), COL_FL,      row_y, (80,80,80),    FONT_SZ_SM, bold=False, mono=True)
                _t(s, _short_out(_e["outcome"])[:13], COL_OUTCOME, row_y, _cc,     FONT_SZ_SM, bold=False, mono=False)
                _gs = _font(FONT_SZ_SM, bold=True, mono=True).render(f"{_e['glory']:,}", True, _sc)
                s.blit(_gs, (COL_SCORE - _gs.get_width(), row_y))
            else:
                _t(s, f"{_rank}.", COL_RANK, row_y, (170,170,170), FONT_SZ_SM, bold=False, mono=True)
                _t(s, "\u2014",   COL_NAME, row_y, (190,190,190), FONT_SZ_SM, bold=False, mono=False)
            row_y += 20

        # ── Buttons ───────────────────────────────────────────────────────
        BTN_AREA_TOP = CONTENT_TOP + HOF_H + 24
        BTN_AREA_TOP = CONTENT_TOP + HOF_H + 24
        BTN_X = RIGHT_X + (RIGHT_W - self._BTN_W) // 2
        BTN_GAP = 12

        buttons = [
            (self.BTN_NEW,    "New Game",     True),
            (self.BTN_OPEN,   "Open Game",   True),
            (self.BTN_RESUME, "Resume Game",  _resume_enabled),
            (self.BTN_QUIT,   "Quit",         True),
        ]

        self._btn_rects = []
        by = BTN_AREA_TOP
        for action, label, enabled in buttons:
            rect = pygame.Rect(BTN_X, by, self._BTN_W, self._BTN_H)
            self._btn_rects.append((rect, action, enabled))

            is_hover = (self._hover == action and enabled)
            is_quit  = (action == self.BTN_QUIT)

            if not enabled:
                bg_col  = (220, 220, 220)
                brd_col = (180, 180, 180)
                txt_col = (170, 170, 170)
            elif is_hover:
                bg_col  = C_BLACK
                brd_col = C_BLACK
                txt_col = C_WHITE
            elif is_quit:
                bg_col  = (248, 248, 248)
                brd_col = C_BLACK
                txt_col = C_BLACK
            else:
                bg_col  = C_WHITE
                brd_col = C_BLACK
                txt_col = C_BLACK

            _box(s, BTN_X, by, self._BTN_W, self._BTN_H,
                 bg=bg_col, border=brd_col, bw=2,
                 radius=self._BTN_RADIUS)

            # Subtle inner highlight for non-hover state
            if not is_hover and enabled:
                pygame.draw.rect(s, (200, 200, 200),
                    (BTN_X+3, by+3, self._BTN_W-6, self._BTN_H-6),
                    1, border_radius=self._BTN_RADIUS)

            # Button label in Gothic serif
            btn_cx = BTN_X + self._BTN_W // 2
            btn_cy = by + (self._BTN_H - _gothic(30).size(label)[1]) // 2
            _gothic_text(s, label, btn_cx, btn_cy,
                         color=txt_col, size=30, shadow=False)

            by += self._BTN_H + BTN_GAP

        # ── Footer ────────────────────────────────────────────────────────
        pygame.draw.line(s, (160,160,160), (60, CONTENT_BTM+4), (W-60, CONTENT_BTM+4), 1)
        _t(s, f"Version {VERSION}", 66, CONTENT_BTM + 12,
           (100, 100, 100), FONT_SZ_SM, bold=False, mono=True)
        _t(s, "Copyright © 1985 John Raymonds & Woodrose Editions",
           cx, CONTENT_BTM + 12,
           (100, 100, 100), FONT_SZ_SM, bold=False, center=True, mono=False)
        _rw = _font(FONT_SZ_SM, bold=False, mono=False).size("Python Recreation 2026")[0]
        _t(s, "Python Recreation 2026", W - 66 - _rw, CONTENT_BTM + 12,
           (100, 100, 100), FONT_SZ_SM, bold=False, mono=False)


# ── Char creation screen (white theme + mouse support) ───────────────────────

class CharCreateScreen:
    """
    New-game character creation screen.
    White background, Gothic header, mouse-clickable class rows and buttons.
    """
    _BTN_W  = 300
    _BTN_H  = 52
    _BTN_R  = 5
    BTN_BEGIN = "begin"
    BTN_BACK  = "back"

    def __init__(self, surf):
        self.surf    = surf
        self.W       = surf.get_width()
        self.H       = surf.get_height()
        self.classes = all_classes()
        # Hit-rect tables (rebuilt each draw)
        self._class_rects:  list = []   # [(pygame.Rect, index)]
        self._diff_rects:   list = []   # [(pygame.Rect, diff_key)]
        self._btn_rects:    list = []   # [(pygame.Rect, action)]
        self._name_rect:    pygame.Rect | None = None
        self._hover_class:  int | None = None
        self._hover_diff:   str | None = None
        self._hover_btn:    str | None = None

    # ── Mouse handling ────────────────────────────────────────────────────────

    def handle_motion(self, sx, sy):
        self._hover_class = None
        self._hover_diff  = None
        self._hover_btn   = None
        for rect, idx in self._class_rects:
            if rect.collidepoint(sx, sy):
                self._hover_class = idx
                return
        for rect, dk in self._diff_rects:
            if rect.collidepoint(sx, sy):
                self._hover_diff = dk
                return
        for rect, action in self._btn_rects:
            if rect.collidepoint(sx, sy):
                self._hover_btn = action
                return

    def handle_click(self, sx, sy, state: dict) -> str | None:
        """
        Returns:
          'begin'     — user clicked Begin (only if name filled + class valid)
          'back'      — user clicked Back
          'name'      — user clicked the name field
          None        — other / no action
        """
        # Class row
        for rect, idx in self._class_rects:
            if rect.collidepoint(sx, sy):
                state["selected_class"] = idx
                state["cursor_on"]      = "name"   # immediately move cursor to name
                return None

        # Difficulty button
        for rect, dk in self._diff_rects:
            if rect.collidepoint(sx, sy):
                state["difficulty"] = dk
                return None

        # Name field
        if self._name_rect and self._name_rect.collidepoint(sx, sy):
            state["cursor_on"] = "name"
            return None

        # Buttons
        for rect, action in self._btn_rects:
            if rect.collidepoint(sx, sy):
                if action == self.BTN_BEGIN:
                    if not state.get("name", "").strip():
                        state["cursor_on"] = "name"   # nudge to fill name
                        return None
                return action
        return None

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, state: dict, tick: int):
        s  = self.surf
        W, H = self.W, self.H
        cx = W // 2

        # ── Background ───────────────────────────────────────────────────────
        s.fill(C_WHITE)
        pygame.draw.rect(s, C_BLACK, (0, 0, W, H), 3)
        pygame.draw.rect(s, (80, 80, 80), (8, 8, W - 16, H - 16), 1)

        # ── Gothic header ─────────────────────────────────────────────────────
        hdr = _fraktur(72).render("Create Your Character", True, C_BLACK)
        s.blit(hdr, (cx - hdr.get_width() // 2, 20))
        rule_y = 20 + hdr.get_height() + 10
        pygame.draw.line(s, C_BLACK, (60, rule_y), (W - 60, rule_y), 2)
        for ox in [cx - 200, cx, cx + 200]:
            pygame.draw.polygon(s, C_BLACK,
                [(ox, rule_y-5),(ox+5,rule_y),(ox,rule_y+5),(ox-5,rule_y)])

        CONTENT_TOP = rule_y + 18
        name   = state.get("name", "")
        sel    = state.get("selected_class", 0)
        cursor = state.get("cursor_on", "name")

        # ── Layout: left=name+class list, right=stats ─────────────────────────
        LEFT_W  = 860
        LEFT_X  = 60
        RIGHT_X = LEFT_X + LEFT_W + 40
        RIGHT_W = W - RIGHT_X - 60

        # ── Name input ────────────────────────────────────────────────────────
        name_lbl = _fraktur(28).render("Name:", True, C_BLACK)
        s.blit(name_lbl, (LEFT_X, CONTENT_TOP))

        NF_X = LEFT_X + name_lbl.get_width() + 14
        NF_W = 480
        NF_H = 44
        NF_Y = CONTENT_TOP - 4
        focused_name = (cursor == "name")

        self._name_rect = pygame.Rect(NF_X, NF_Y, NF_W, NF_H)
        pygame.draw.rect(s, (245, 245, 245), self._name_rect)
        border_col = C_BLACK if focused_name else (160, 160, 160)
        pygame.draw.rect(s, border_col, self._name_rect, 2 if focused_name else 1)

        caret = "|" if focused_name and tick % 60 < 32 else ""
        name_img = _font(FONT_SZ_LG, bold=False, mono=False).render(
            name + caret or ("_" if not name else name + caret),
            True, C_BLACK)
        s.blit(name_img, (NF_X + 10, NF_Y + (NF_H - name_img.get_height()) // 2))

        # ── Class list ────────────────────────────────────────────────────────
        cls_lbl = _fraktur(24).render("Choose Class:", True, (60, 60, 60))
        CLS_TOP = CONTENT_TOP + NF_H + 20
        s.blit(cls_lbl, (LEFT_X, CLS_TOP))
        CLS_ROW_Y = CLS_TOP + cls_lbl.get_height() + 8
        ROW_H = 62
        ROW_W = LEFT_W

        self._class_rects = []
        for i, cls in enumerate(self.classes):
            ry   = CLS_ROW_Y + i * (ROW_H + 4)
            rect = pygame.Rect(LEFT_X, ry, ROW_W, ROW_H)
            self._class_rects.append((rect, i))

            isel   = (i == sel)
            ihover = (self._hover_class == i)

            if isel:
                bg  = (20, 20, 20)
                tc  = C_WHITE
                tc2 = (160, 160, 160)
                bd  = C_BLACK
            elif ihover:
                bg  = (240, 240, 240)
                tc  = C_BLACK
                tc2 = (80, 80, 80)
                bd  = C_BLACK
            else:
                bg  = (250, 250, 250)
                tc  = (30, 30, 30)
                tc2 = (120, 120, 120)
                bd  = (180, 180, 180)

            pygame.draw.rect(s, bg, rect)
            pygame.draw.rect(s, bd, rect, 1 if not isel else 2)

            # Class name in Gothic, description in serif
            cn_img = _fraktur(26).render(cls["name"], True, tc)
            s.blit(cn_img, (LEFT_X + 16, ry + 8))
            cd_img = _font(FONT_SZ_MD, bold=False, mono=False).render(
                cls["description"], True, tc2)
            s.blit(cd_img, (LEFT_X + 16, ry + ROW_H - cd_img.get_height() - 8))

        # ── Stats panel (right column) ─────────────────────────────────────────
        STAT_BOX_W = RIGHT_W
        STAT_BOX_H = len(self.classes) * (ROW_H + 4) + cls_lbl.get_height() + 8 + NF_H + 20
        STAT_BOX_Y = CONTENT_TOP

        pygame.draw.rect(s, (248, 248, 248),
                         (RIGHT_X, STAT_BOX_Y, STAT_BOX_W, STAT_BOX_H))
        pygame.draw.rect(s, (180, 180, 180),
                         (RIGHT_X, STAT_BOX_Y, STAT_BOX_W, STAT_BOX_H), 1)

        if sel < len(self.classes):
            cls  = self.classes[sel]
            sy   = STAT_BOX_Y + 14
            scx  = RIGHT_X + STAT_BOX_W // 2

            cls_hdr = _fraktur(32).render(cls["name"], True, C_BLACK)
            s.blit(cls_hdr, (scx - cls_hdr.get_width() // 2, sy))
            sy += cls_hdr.get_height() + 6
            pygame.draw.line(s, (160,160,160), (RIGHT_X+14,sy), (RIGHT_X+STAT_BOX_W-14,sy), 1)
            sy += 12

            stats = cls["stats"]
            for j, (sn, sv) in enumerate(zip(STAT_NAMES, stats)):
                vc = (20, 140, 20) if sv >= 16 else C_HP_LOW if sv <= 8 else C_LTEXT
                lbl_img = _font(FONT_SZ_LG, bold=False, mono=True).render(
                    f"{sn}:", True, (80, 80, 80))
                val_img = _font(FONT_SZ_LG, bold=True, mono=True).render(
                    f"{sv:2d}", True, vc)
                s.blit(lbl_img, (RIGHT_X + 20, sy))
                s.blit(val_img, (RIGHT_X + 90, sy))
                # Mini pip bar
                pip_x = RIGHT_X + 130
                for p2 in range(20):
                    col_pip = vc if p2 < sv - 3 else (220, 220, 220)
                    pygame.draw.rect(s, col_pip,
                        (pip_x + p2 * (STAT_BOX_W - 155) // 20, sy + 4,
                         (STAT_BOX_W - 165) // 20 - 1, 14))
                sy += 30

            pygame.draw.line(s, (160,160,160),
                (RIGHT_X+14, sy), (RIGHT_X+STAT_BOX_W-14, sy), 1)
            sy += 10
            hp_img = _font(FONT_SZ_MD, bold=True, mono=True).render(
                f"Starting HP: {cls['base_hp']}", True, C_HP_FULL)
            s.blit(hp_img, (RIGHT_X + 20, sy)); sy += 24
            ident = cls.get("identify")
            if ident:
                id_img = _font(FONT_SZ_MD, bold=False, mono=True).render(
                    f"Identifies: {ident}s", True, C_LTEXT_ACCENT)
                s.blit(id_img, (RIGHT_X + 20, sy))

        # ── Difficulty selector ────────────────────────────────────────────────
        sel_diff = state.get("difficulty", DIFF_ADVENTURER)
        DIFF_ROW_Y = STAT_BOX_Y + STAT_BOX_H + 16
        DIFF_LABEL_W = (LEFT_W + 40) // 3 - 8   # three equal buttons across left col width
        DIFF_H = 38
        self._diff_rects = []

        for di, dk in enumerate(DIFF_ORDER):
            dx2 = LEFT_X + di * (DIFF_LABEL_W + 8)
            drect = pygame.Rect(dx2, DIFF_ROW_Y, DIFF_LABEL_W, DIFF_H)
            self._diff_rects.append((drect, dk))
            is_sel   = (dk == sel_diff)
            is_hov   = (self._hover_diff == dk)
            if is_sel:
                bg2, bd2, tc2 = (20, 20, 20), C_BLACK, C_WHITE
            elif is_hov:
                bg2, bd2, tc2 = (240, 240, 240), C_BLACK, C_BLACK
            else:
                bg2, bd2, tc2 = (250, 250, 250), (180, 180, 180), (80, 80, 80)
            pygame.draw.rect(s, bg2, drect)
            pygame.draw.rect(s, bd2, drect, 1 if not is_sel else 2)
            lbl_surf = _fraktur(18).render(DIFF_LABEL[dk], True, tc2)
            s.blit(lbl_surf, (dx2 + (DIFF_LABEL_W - lbl_surf.get_width()) // 2,
                               DIFF_ROW_Y + (DIFF_H - lbl_surf.get_height()) // 2))

        # Difficulty description line
        diff_desc_y = DIFF_ROW_Y + DIFF_H + 5
        desc_txt = DIFF_DESC.get(sel_diff, "")
        desc_surf = _font(FONT_SZ_SM, bold=False, mono=False).render(desc_txt, True, (100, 100, 100))
        s.blit(desc_surf, (LEFT_X, diff_desc_y))

        # ── Buttons ────────────────────────────────────────────────────────────
        BTNS_Y = diff_desc_y + 22
        begin_enabled = bool(name.strip())
        BTN_GAP = 20
        total_w = self._BTN_W * 2 + BTN_GAP
        b1x = cx - total_w // 2
        b2x = b1x + self._BTN_W + BTN_GAP

        self._btn_rects = []
        for (bx, label, action, enabled) in [
            (b1x, "Begin",        self.BTN_BEGIN, begin_enabled),
            (b2x, "Back to Menu", self.BTN_BACK,  True),
        ]:
            rect = pygame.Rect(bx, BTNS_Y, self._BTN_W, self._BTN_H)
            self._btn_rects.append((rect, action))
            is_hover = (self._hover_btn == action)

            if not enabled:
                bg, bd, tc = (220,220,220), (180,180,180), (170,170,170)
            elif is_hover:
                bg, bd, tc = C_BLACK, C_BLACK, C_WHITE
            else:
                bg, bd, tc = C_WHITE, C_BLACK, C_BLACK

            pygame.draw.rect(s, bg, rect, border_radius=self._BTN_R)
            pygame.draw.rect(s, bd, rect, 2, border_radius=self._BTN_R)
            if not is_hover and enabled:
                pygame.draw.rect(s, (200,200,200), rect.inflate(-6,-6), 1,
                                 border_radius=self._BTN_R)
            lbl_img = _gothic(28).render(label, True, tc)
            s.blit(lbl_img, (bx + (self._BTN_W - lbl_img.get_width()) // 2,
                              BTNS_Y + (self._BTN_H - lbl_img.get_height()) // 2))

        # ── Footer hint ───────────────────────────────────────────────────────
        hint = "Click a class to select  ·  Click name field or press Tab  ·  Enter to begin  ·  Esc to go back"
        hint_img = _font(FONT_SZ_SM, bold=False, mono=False).render(hint, True, (120,120,120))
        s.blit(hint_img, (cx - hint_img.get_width() // 2, H - 30))


# ── Overlay (death / win) ─────────────────────────────────────────────────────

class OverlayScreen:
    """Full-screen white-theme result screen. Matches the title / char-create aesthetic."""

    _BTN_W  = 300
    _BTN_H  = 52
    _BTN_R  = 5
    BTN_CLOSE = "close"

    def __init__(self, surf):
        self.surf = surf
        self.W    = surf.get_width()
        self.H    = surf.get_height()
        self._hover:     str | None = None
        self._btn_rects: list       = []   # [(pygame.Rect, action)]

    # ── Mouse handling ────────────────────────────────────────────────────────

    def handle_motion(self, sx, sy):
        self._hover = None
        for rect, action in self._btn_rects:
            if rect.collidepoint(sx, sy):
                self._hover = action
                break

    def handle_click(self, sx, sy) -> str | None:
        for rect, action in self._btn_rects:
            if rect.collidepoint(sx, sy):
                return action
        return None

    # ── Glory / HoF breakdown ─────────────────────────────────────────────────

    def _draw_glory_panel(self, s, game, bx, by, bw, accent_col) -> int:
        """Draw glory total + breakdown table + HoF rank. Returns new y below panel."""
        from engine.hof import compute_glory
        glory, bd = compute_glory(game)

        glory_str = f"GLORY:  {glory:,}"
        _t(s, glory_str, bx + bw//2, by, accent_col,
           FONT_SZ_TTL, center=True, bold=True, mono=True)
        by += 54

        PTS_X = bx + bw - 28
        dim   = (110, 110, 110)
        for key in ("depth", "level", "xp", "items", "explore", "victory"):
            pts, count, label = bd[key]
            if pts == 0 and key == "victory":
                continue
            _t(s, f"{label} ({count})", bx + 28, by, dim, FONT_SZ_SM, bold=False, mono=False)
            ps = _font(FONT_SZ_SM, bold=True, mono=True).render(f"+{pts:,}", True, dim)
            s.blit(ps, (PTS_X - ps.get_width(), by))
            by += 20

        pygame.draw.line(s, (200, 200, 200), (bx+20, by+3), (bx+bw-20, by+3), 1)
        by += 12

        hof_result = getattr(game, "hof_result", None)
        if hof_result:
            _entry, rank = hof_result
            if rank is not None:
                _t(s, f"Hall of Fame  —  Rank #{rank}", bx + bw//2, by,
                   accent_col, FONT_SZ_LG, center=True, bold=True, mono=False)
            else:
                _t(s, "Score not high enough for the Hall of Fame.",
                   bx + bw//2, by, (150, 150, 150), FONT_SZ_SM, center=True, mono=False)
        return by + 28

    # ── Shared draw ───────────────────────────────────────────────────────────

    def _draw_screen(self, game, title_txt, accent_col, summary_rows):
        """
        summary_rows : list of (text, color, font_size, bold)
        accent_col   : colour used for title, glory total, HoF rank line
        """
        s    = self.surf
        W, H = self.W, self.H
        cx   = W // 2

        # ── White background + borders (same as title/char-create) ───────────
        s.fill(C_WHITE)
        pygame.draw.rect(s, C_BLACK,      (0, 0, W, H), 3)
        pygame.draw.rect(s, (80, 80, 80), (8, 8, W-16, H-16), 1)

        # ── Fraktur heading ───────────────────────────────────────────────────
        tw, th = _fraktur_text(s, title_txt, cx, 28,
                               color=accent_col, size=96, shadow=False)
        rule_y = 28 + th + 10
        pygame.draw.line(s, C_BLACK, (60, rule_y), (W-60, rule_y), 2)
        for ox in [cx - 200, cx, cx + 200]:
            pygame.draw.polygon(s, C_BLACK,
                [(ox, rule_y-5), (ox+5, rule_y), (ox, rule_y+5), (ox-5, rule_y)])

        # ── Character summary lines ───────────────────────────────────────────
        sy = rule_y + 26
        for txt, col, fsz, bold in summary_rows:
            _t(s, txt, cx, sy, col, fsz, center=True, bold=bold, mono=False)
            sy += fsz + 10

        # ── Glory panel box ───────────────────────────────────────────────────
        BOX_W = 740
        BOX_X = cx - BOX_W // 2
        BOX_Y = sy + 14
        BOX_H = 250

        pygame.draw.rect(s, (248, 248, 248), (BOX_X, BOX_Y, BOX_W, BOX_H))
        pygame.draw.rect(s, (190, 190, 190), (BOX_X, BOX_Y, BOX_W, BOX_H), 1)
        _corner_ornaments(s, BOX_X, BOX_Y, BOX_W, BOX_H, size=18, color=(180, 180, 180))
        self._draw_glory_panel(s, game, BOX_X, BOX_Y + 16, BOX_W, accent_col)

        # ── Close button ──────────────────────────────────────────────────────
        BTN_Y = BOX_Y + BOX_H + 30
        BTN_X = cx - self._BTN_W // 2
        rect  = pygame.Rect(BTN_X, BTN_Y, self._BTN_W, self._BTN_H)
        self._btn_rects = [(rect, self.BTN_CLOSE)]

        is_hover = (self._hover == self.BTN_CLOSE)
        if is_hover:
            bg, bd, tc = C_BLACK, C_BLACK, C_WHITE
        else:
            bg, bd, tc = C_WHITE, C_BLACK, C_BLACK

        pygame.draw.rect(s, bg, rect, border_radius=self._BTN_R)
        pygame.draw.rect(s, bd, rect, 2, border_radius=self._BTN_R)
        if not is_hover:
            pygame.draw.rect(s, (200, 200, 200), rect.inflate(-6, -6), 1,
                             border_radius=self._BTN_R)
        lbl = _gothic(28).render("Close", True, tc)
        s.blit(lbl, (BTN_X + (self._BTN_W - lbl.get_width()) // 2,
                     BTN_Y + (self._BTN_H - lbl.get_height()) // 2))

        # ── Footer hint ───────────────────────────────────────────────────────
        hint = "Click  Close  or press  Esc  to return to the main menu"
        hi = _font(FONT_SZ_SM, bold=False, mono=False).render(hint, True, (130, 130, 130))
        s.blit(hi, (cx - hi.get_width() // 2, H - 30))

    # ── Public draw methods ───────────────────────────────────────────────────

    def draw_death(self, game):
        p     = game.player
        cause = getattr(game, "death_cause", "") or "Unknown cause"
        self._draw_screen(game, "You Have Died", C_HP_LOW, [
            (f"{p.name}  —  {_class_name(p.class_key)}  Lv.{p.level}",
             C_LTEXT, FONT_SZ_LG, True),
            (cause,
             C_HP_LOW, FONT_SZ_MD, False),
            (f"Dungeon Floor {game.floor}  /  {TOTAL_FLOORS}",
             C_TEXT_DIM, FONT_SZ_MD, False),
        ])

    def draw_win(self, game):
        p = game.player
        self._draw_screen(game, "Victory!", (160, 130, 20), [
            (f"{p.name}  —  {_class_name(p.class_key)}  Lv.{p.level}",
             C_LTEXT, FONT_SZ_LG, True),
            ("You retrieved the Orb of Carnos!",
             C_GOLD, FONT_SZ_MD, False),
            (f"Dungeon Floor {game.floor}  /  {TOTAL_FLOORS}",
             C_TEXT_DIM, FONT_SZ_MD, False),
        ])


def _class_name(key):
    from data.classes import get_class
    return get_class(key)["name"]
