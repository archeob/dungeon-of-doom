# ui/inventory.py — Inventory overlay v0.204
#
# Keys:  ↑↓ / a–t  navigate   U/Return  use   E  equip/remove   D  drop   ESC  close
# Mouse: click row to select; click action button or ×; double-click row for default action

import pygame, os
from constants import (SCREEN_W, SCREEN_H, FONT_FRAKTUR,
                       IC_WEAPON, IC_ARMOR, IC_POTION,
                       IC_SCROLL, IC_WAND, IC_RING,
                       IC_FOOD, IC_JEWEL, IC_MISC,
                       C_BLACK, C_WHITE, C_HP_FULL, C_HP_LOW,
                       C_LTEXT, C_LTEXT_DIM, C_LTEXT_ACCENT,
                       C_LPANEL_LINE)

# ── Geometry ──────────────────────────────────────────────────────────────────
_PAD  = 30
_TH   = 52        # title bar height
_SBH  = 44        # status bar height
_LW   = 680       # left column width
_RX   = _PAD + _LW + 20
_RW   = SCREEN_W - _RX - _PAD
_IY   = _TH + 8
_IH   = SCREEN_H - _IY - _SBH - 4
_LH   = 22        # item row height
_CH   = 20        # category header height

_CAT_ORDER = [
    (IC_WEAPON, "Weapons"),
    (IC_ARMOR,  "Armor"),
    (IC_RING,   "Rings"),
    (IC_WAND,   "Wands"),
    (IC_POTION, "Potions"),
    (IC_SCROLL, "Scrolls"),
    (IC_FOOD,   "Food"),
    (IC_JEWEL,  "Gems"),
    (IC_MISC,   "Other"),
]

# Verb shown on the primary action button per category
_USE_VERB = {
    IC_POTION: "Drink",
    IC_SCROLL: "Read",
    IC_FOOD:   "Eat",
    IC_WAND:   "Zap",
}

# ── Font cache ────────────────────────────────────────────────────────────────
_FC: dict = {}
_GOTHIC_PATH = "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
_GOTHIC_CACHE: dict = {}

def _draw_scroll_indicators(scr, items, scroll_offset, vis_rows, pad, iy, ih, lw):
    """Draw ▲/▼ arrows and 'N-M / total' counter when list overflows."""
    total = len(items)
    if total <= vis_rows:
        return
    col_dim  = (140, 140, 140)
    col_act  = (60,  60, 180)
    arr_x    = pad + lw + 2
    top_y    = pad + iy
    bot_y    = pad + iy + ih - 14

    # Up arrow
    if scroll_offset > 0:
        pygame.draw.polygon(scr, col_act,
            [(arr_x+6, top_y+2), (arr_x, top_y+10), (arr_x+12, top_y+10)])
    # Down arrow
    if scroll_offset + vis_rows < total:
        pygame.draw.polygon(scr, col_act,
            [(arr_x, bot_y), (arr_x+12, bot_y), (arr_x+6, bot_y+10)])
    # Counter
    lo  = scroll_offset + 1
    hi  = min(scroll_offset + vis_rows, total)
    txt = _mono(12).render(f"{lo}-{hi}/{total}", True, col_dim)
    scr.blit(txt, (arr_x - txt.get_width()//2 + 6,
                   pad + iy + ih // 2 - txt.get_height() // 2))


def _frak(sz):
    k = ("frak", sz)
    if k not in _FC:
        path = os.path.join(os.path.dirname(__file__), "..", FONT_FRAKTUR)
        try:    _FC[k] = pygame.font.Font(path, sz)
        except: _FC[k] = pygame.font.Font(None, sz)
    return _FC[k]

def _mono(sz, bold=False):
    k = ("mono", sz, bold)
    if k not in _FC:
        _FC[k] = pygame.font.SysFont("Courier New", sz, bold=bold)
    return _FC[k]

def _gothic(sz):
    if sz not in _GOTHIC_CACHE:
        try:    _GOTHIC_CACHE[sz] = pygame.font.Font(_GOTHIC_PATH, sz)
        except: _GOTHIC_CACHE[sz] = pygame.font.SysFont("serif", sz, bold=True)
    return _GOTHIC_CACHE[sz]

# ── Detail lines ──────────────────────────────────────────────────────────────

def _item_detail_lines(item: dict, game) -> list:
    lines = []
    cat  = item.get("cat", "")
    nm   = game.item_display_name(item)
    lines.append((nm, C_BLACK))
    lines.append(("", C_LTEXT_DIM))

    cat_labels = {IC_WEAPON:"Weapon", IC_ARMOR:"Armor", IC_RING:"Ring",
                  IC_WAND:"Wand", IC_POTION:"Potion", IC_SCROLL:"Scroll",
                  IC_FOOD:"Food", IC_JEWEL:"Gem", IC_MISC:"Misc"}
    lines.append((cat_labels.get(cat, cat.title()), C_LTEXT_DIM))

    if cat == IC_WEAPON:
        enc       = item.get("enchant", 0)
        enc_known = item.get("enchant_known", False)
        bd        = item.get("base_dmg", 0)
        hands     = item.get("hands", 1)
        slot      = item.get("slot", "weapon")
        if slot == "throw":
            lines.append((f"Throwing — dmg 1–{bd}", C_LTEXT))
            lines.append((f"Throws left: {item.get('throws', item.get('max_throws',0))}", C_LTEXT))
        else:
            n, d = item.get("dmg_dice", (1, bd)) if bd else item.get("dmg_dice", (1, 4))
            eff_d = d + enc if enc_known else d
            dice_str = f"{n}d{eff_d}"
            dmg_range = f"{n}–{n*eff_d}"
            hand_lbl = "1-hand" if hands == 1 else "2-hand"
            lines.append((f"{hand_lbl}  ·  {dice_str}  ({dmg_range})", C_LTEXT))
        if enc != 0 and enc_known:
            lines.append((f"Enchant: {'+'if enc>0 else ''}{enc}",
                          C_HP_FULL if enc > 0 else C_HP_LOW))

    elif cat == IC_ARMOR:
        ac   = item.get("base_ac", 0)
        enc  = item.get("enchant", 0)
        slot = item.get("slot", "armor")
        slot_nm = {"armor":"Body","cloak":"Cloak","offhand":"Off-hand",
                   "helmet":"Head","gauntlets":"Hands"}.get(slot, slot.title())
        lines.append((f"{slot_nm}  ·  AC +{ac + enc}", C_LTEXT))
        if enc > 0:
            lines.append((f"Enchanted: +{enc}", C_HP_FULL))

    elif cat == IC_RING:
        iid = item.get("item_id","")
        if iid in game.identified:
            lines.append((item.get("message",""), C_LTEXT))
        lines.append(("Wear with [E]", C_LTEXT_DIM))

    elif cat == IC_WAND:
        iid = item.get("item_id","")
        ch  = item.get("charges", 0)
        if iid in game.identified:
            lines.append((f"Charges: {ch}", C_LTEXT))
            lines.append((item.get("message",""), C_LTEXT_DIM))
        else:
            lines.append((f"Charges: {'?' if ch else 'empty'}", C_LTEXT_DIM))

    elif cat in (IC_POTION, IC_SCROLL):
        iid = item.get("item_id","")
        if iid in game.identified:
            lines.append((item.get("message",""), C_LTEXT))

    elif cat == IC_FOOD:
        fv = item.get("food_val", 0)
        lines.append((f"Nutrition: {fv}", C_LTEXT))
        lines.append((item.get("message",""), C_LTEXT_DIM))

    elif cat == IC_JEWEL:
        lines.append((f"Value: {item.get('value',0)} gp", (180,140,20)))

    wt = item.get("weight", 0)
    if wt:
        lines.append(("", C_LTEXT_DIM))
        lines.append((f"Weight: {wt}", C_LTEXT_DIM))

    if item.get("cursed"):
        lines.append(("CURSED", C_HP_LOW))

    p = game.player
    for slot, eq in p.equipped.items():
        if eq is item:
            slot_nm = {"weapon":"Weapon","offhand":"Off-hand","armor":"Armor",
                       "cloak":"Cloak","helmet":"Helmet","gauntlets":"Gauntlets",
                       "ring_l":"Left ring","ring_r":"Right ring"}.get(slot, slot)
            lines.append(("", C_LTEXT_DIM))
            lines.append((f"[Equipped — {slot_nm}]", C_HP_FULL))
            break

    return lines


# ── Gothic button (title-screen style) ────────────────────────────────────────

_BTN_H      = 42
_BTN_RADIUS = 6

def _draw_gothic_btn(scr, label: str, rect: pygame.Rect,
                     enabled: bool = True, hover: bool = False,
                     danger: bool = False):
    """Draw a button in the same style as the title screen."""
    if not enabled:
        bg_col  = (220, 220, 220)
        brd_col = (180, 180, 180)
        txt_col = (170, 170, 170)
    elif hover:
        bg_col  = C_BLACK
        brd_col = C_BLACK
        txt_col = C_WHITE
    elif danger:
        bg_col  = (248, 240, 240)
        brd_col = (180, 60, 60)
        txt_col = (160, 40, 40)
    else:
        bg_col  = C_WHITE
        brd_col = C_BLACK
        txt_col = C_BLACK

    pygame.draw.rect(scr, bg_col,  rect, border_radius=_BTN_RADIUS)
    pygame.draw.rect(scr, brd_col, rect, 2, border_radius=_BTN_RADIUS)

    # Subtle inner highlight line (non-hover only)
    if not hover and enabled:
        inner = pygame.Rect(rect.x+3, rect.y+3, rect.w-6, rect.h-6)
        pygame.draw.rect(scr, (200, 200, 200), inner, 1,
                         border_radius=_BTN_RADIUS)

    # Label
    img = _gothic(22).render(label, True, txt_col)
    scr.blit(img, (rect.x + (rect.w - img.get_width())  // 2,
                   rect.y + (rect.h - img.get_height()) // 2))


# ── Inventory Screen ──────────────────────────────────────────────────────────

class InventoryScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen        = screen
        self.selected      = 0
        self.scroll_offset = 0          # first visible item index
        self._row_rects:  list   = []
        self._btn_rects:  dict   = {}
        self._close_rect          = None
        self._hover_btn:  str    = ""

    # ── List helpers ──────────────────────────────────────────────────────────

    def _build_list(self, game) -> list:
        """Build the ordered inventory display list.

        Items are grouped by category (per _CAT_ORDER), then sorted within each
        group so:
          1. Equipped items appear first (they carry a [WPN]/[ARM]/etc. badge).
          2. Remaining items sorted by display name — identical aliases cluster.
        """
        p = game.player
        equipped_ids = {id(eq) for eq in p.equipped.values() if eq is not None}

        seen    = set()
        ordered = []
        for cat, _ in _CAT_ORDER:
            group = [item for item in p.inventory
                     if item.get("cat") == cat and id(item) not in seen]
            # Sort: equipped first, then by display name for clustering
            group.sort(key=lambda it: (
                0 if id(it) in equipped_ids else 1,
                game.item_display_name(it)
            ))
            for item in group:
                seen.add(id(item))
                ordered.append(item)

        # Fallback: equipped items not already in inventory list
        for slot, eq in p.equipped.items():
            if eq is not None and id(eq) not in seen:
                seen.add(id(eq))
                ordered.append(eq)
        return ordered

    def navigate(self, delta: int, game):
        items = self._build_list(game)
        if items:
            self.selected = (self.selected + delta) % len(items)
            self._ensure_visible(game)

    def scroll(self, delta: int, game):
        items = self._build_list(game)
        vis = self._visible_rows()
        max_off = max(0, len(items) - vis)
        self.scroll_offset = max(0, min(max_off, self.scroll_offset + delta))

    def _visible_rows(self) -> int:
        return max(1, (_IH // _LH) - 3)

    def _ensure_visible(self, game):
        vis = self._visible_rows()
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + vis:
            self.scroll_offset = self.selected - vis + 1

    def select_by_letter(self, letter: str, game):
        idx = ord(letter.lower()) - ord('a')
        items = self._build_list(game)
        if 0 <= idx < len(items):
            self.selected = idx

    def current_item(self, game):
        items = self._build_list(game)
        if items and 0 <= self.selected < len(items):
            return items[self.selected]
        return None

    # ── Mouse handling ────────────────────────────────────────────────────────

    def handle_motion(self, mx: int, my: int):
        self._hover_btn = ""
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(mx, my):
                self._hover_btn = name; return

    def handle_click(self, mx: int, my: int, game) -> str:
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(mx, my):
                return name
        for rect, idx in self._row_rects:
            if rect.collidepoint(mx, my):
                prev = self.selected
                self.selected = idx
                if game.pending_identify > 0:
                    return 'identify'   # single click identifies in identify-mode
                if idx == prev:         # second click on already-selected row → activate
                    item = self.current_item(game)
                    if item:
                        cat = item.get("cat","")
                        if cat in (IC_POTION, IC_SCROLL, IC_FOOD, IC_WAND):
                            return 'use'
                        if cat in (IC_WEAPON, IC_ARMOR, IC_RING):
                            return 'equip'
                return ''               # first click → select only
        panel = pygame.Rect(_PAD, _PAD, SCREEN_W - _PAD*2, SCREEN_H - _PAD*2)
        if not panel.collidepoint(mx, my):
            return 'close'
        return ''

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, game):
        scr  = self.screen
        W, H = SCREEN_W, SCREEN_H
        p    = game.player

        self._row_rects = []
        self._btn_rects = {}

        # Dark overlay + white panel
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        scr.blit(overlay, (0, 0))
        pygame.draw.rect(scr, C_WHITE, (_PAD, _PAD, W-_PAD*2, H-_PAD*2))
        pygame.draw.rect(scr, C_BLACK, (_PAD, _PAD, W-_PAD*2, H-_PAD*2), 2)

        # ── Title bar ──────────────────────────────────────────────────────────
        pygame.draw.line(scr, C_BLACK, (_PAD, _PAD+_TH), (W-_PAD, _PAD+_TH), 1)

        ti = _frak(34).render("Inventory", True, C_BLACK)
        scr.blit(ti, (_PAD+14, _PAD+(_TH-ti.get_height())//2))

        # Item count — right-aligned in title bar
        wt_cur  = p.carried_weight
        wt_cap  = p.carry_capacity
        cnt_txt = f"{wt_cur} / {wt_cap} wt  ·  {len(p.inventory)} items"
        cnt     = _mono(15).render(cnt_txt, True, C_LTEXT_DIM)
        cnt_x   = W - _PAD - cnt.get_width() - 14
        scr.blit(cnt, (cnt_x, _PAD + (_TH - cnt.get_height())//2))
        self._close_rect = None   # no × button; Close is a gothic button below

        # Identify-mode banner (centred in space between title and count)
        if game.pending_identify > 0:
            ban = _mono(14, bold=True).render(
                f"Select an item to identify  ({game.pending_identify} remaining)",
                True, C_LTEXT_ACCENT)
            ban_x = _PAD + 14 + ti.get_width() + 20
            ban_max_w = cnt_x - ban_x - 10
            if ban.get_width() > ban_max_w:
                ban = ban.subsurface((0, 0, ban_max_w, ban.get_height()))
            scr.blit(ban, (ban_x, _PAD + (_TH - ban.get_height())//2))

        # Vertical divider
        div_x = _PAD + _LW + 10
        pygame.draw.line(scr, C_LPANEL_LINE,
                         (div_x, _PAD+_TH+4), (div_x, H-_PAD-_SBH-4), 1)

        # ── Item list (left column) ────────────────────────────────────────────
        items    = self._build_list(game)
        y        = _PAD + _IY
        prev_cat = None

        for idx, item in enumerate(items):
            cat = item.get("cat","")
            cat_changed = (cat != prev_cat)
            if cat_changed:
                if prev_cat is not None:
                    y += 4 if idx >= self.scroll_offset else 0

            if idx < self.scroll_offset:
                if cat_changed:
                    prev_cat = cat
                continue

            if y > _PAD + _IY + _IH - _LH:
                break

            if cat_changed:
                lbl = dict(_CAT_ORDER)
                hdr = _mono(13).render(lbl.get(cat, cat.upper()), True, C_LTEXT_DIM)
                scr.blit(hdr, (_PAD+14, y))
                y += _CH
                prev_cat = cat

            row_rect = pygame.Rect(_PAD+2, y-1, _LW+6, _LH)
            self._row_rects.append((row_rect, idx))

            selected = (idx == self.selected)
            if selected:
                pygame.draw.rect(scr, (0, 0, 120), row_rect)
                txt_col = C_WHITE
            else:
                txt_col = C_LTEXT

            ch   = chr(ord('a') + idx) if idx < 26 else '?'
            lbdg = _mono(14, bold=True).render(f"{ch})", True,
                         C_WHITE if selected else C_LTEXT_DIM)
            scr.blit(lbdg, (_PAD+14, y+2))

            eq_badge = ""
            for slot, eq in p.equipped.items():
                if eq is item:
                    eq_badge = {"weapon":"WPN","offhand":"OFF","armor":"ARM",
                                "cloak":"CLK","helmet":"HLM","gauntlets":"GLV",
                                "ring_l":"RL","ring_r":"RR"}.get(slot,"EQ")
                    eq_badge = f"[{eq_badge}]"
                    break

            nm_img = _mono(14, bold=selected).render(
                game.item_display_name(item), True, txt_col)
            scr.blit(nm_img, (_PAD+36, y+2))

            if eq_badge:
                eb = _mono(12).render(eq_badge, True,
                                      C_WHITE if selected else C_HP_FULL)
                scr.blit(eb, (_PAD+14+_LW-eb.get_width()-8, y+4))

            y += _LH

        if not items:
            empty = _mono(16).render("Your pack is empty.", True, C_LTEXT_DIM)
            scr.blit(empty, (_PAD+_LW//2-empty.get_width()//2,
                             _PAD+_IY+_IH//2))

        # Scroll indicators
        _draw_scroll_indicators(scr, items, self.scroll_offset,
                                self._visible_rows(), _PAD, _IY, _IH, _LW)

        # ── Right column layout ────────────────────────────────────────────────
        # Total right column height (excluding title bar and status bar)
        right_top    = _PAD + _IY + 4
        btn_h_total  = _BTN_H + 18          # buttons + separator gap
        right_bottom = H - _PAD - _SBH - btn_h_total
        right_h      = right_bottom - right_top

        # Split: upper 48% = item detail, lower 52% = equipment slots
        split_h    = int(right_h * 0.46)
        detail_top = right_top
        detail_bot = right_top + split_h
        slots_top  = detail_bot + 8
        slots_bot  = right_bottom - 4

        # ── Upper pane: item detail ────────────────────────────────────────────
        cur = self.current_item(game)
        if cur:
            detail = _item_detail_lines(cur, game)
            dy = detail_top
            for i, (txt, col) in enumerate(detail):
                if dy + 20 > detail_bot:
                    break      # clip to upper pane
                if not txt:
                    dy += 6; continue
                img = (_frak(22) if i == 0 else _mono(14)).render(txt, True, col)
                if img.get_width() > _RW - 4:
                    img = img.subsurface((0, 0, _RW-4, img.get_height()))
                scr.blit(img, (_RX, dy))
                dy += img.get_height() + (5 if i == 0 else 3)

        # Divider between upper and lower pane
        pygame.draw.line(scr, C_LPANEL_LINE, (_RX, detail_bot+2), (W-_PAD-4, detail_bot+2), 1)

        # ── Lower pane: equipment slots ────────────────────────────────────────
        # Slot definitions: (display_label, equipped_key)
        _SLOT_GROUPS = [
            # group label, list of (display, slot_key)
            ("Weapons", [
                ("Main Hand",  "weapon"),
                ("Off Hand",   "offhand"),
            ]),
            ("Armor", [
                ("Head",       "helmet"),
                ("Body",       "armor"),
                ("Cloak",      "cloak"),
                ("Feet",       "gauntlets"),
            ]),
            ("Rings", [
                ("Right Hand", "ring_r"),
                ("Left Hand",  "ring_l"),
            ]),
            ("Missiles", [
                ("Readied",    "missile"),
            ]),
        ]

        sy       = slots_top
        SLH      = 19     # slot row height
        SLH_HDR  = 16     # group header height
        SLH_GAP  = 4      # gap after group

        # Header label
        hdr_lbl = _mono(12, bold=True).render("EQUIPMENT", True, C_LTEXT_DIM)
        scr.blit(hdr_lbl, (_RX, sy))
        sy += SLH_HDR + 2

        for grp_label, slots in _SLOT_GROUPS:
            if sy + SLH_HDR > slots_bot:
                break
            # Group label
            gl = _mono(11).render(grp_label.upper(), True, C_LTEXT_DIM)
            scr.blit(gl, (_RX, sy))
            sy += SLH_HDR - 2

            for disp, slot_key in slots:
                if sy + SLH > slots_bot:
                    break
                eq_item = p.equipped.get(slot_key)
                is_selected = (eq_item is not None and eq_item is cur)

                # Row background for selected equipped item
                row_r = pygame.Rect(_RX - 2, sy - 1, _RW, SLH)
                if is_selected:
                    pygame.draw.rect(scr, (230, 245, 230), row_r)

                # Slot label (fixed width ~100px)
                lbl_col  = C_LTEXT_DIM
                lbl_img  = _mono(12).render(f"{disp}:", True, lbl_col)
                scr.blit(lbl_img, (_RX, sy))

                # Item name or em-dash
                name_x = _RX + 100
                if eq_item:
                    nm  = game.item_display_name(eq_item)
                    # Truncate to fit
                    max_w = W - _PAD - name_x - 4
                    ni = _mono(12, bold=True).render(nm, True, (40,120,40))
                    if ni.get_width() > max_w:
                        ni = ni.subsurface((0, 0, max_w, ni.get_height()))
                else:
                    ni = _mono(12).render("—", True, (180, 180, 180))
                scr.blit(ni, (name_x, sy))
                sy += SLH

            sy += SLH_GAP

        # ── Action buttons ─────────────────────────────────────────────────────
        if cur:
            cat   = cur.get("cat","")
            BTN_W = 150
            BTN_GAP = 10
            btn_y = H - _PAD - _SBH - _BTN_H - 6

            pygame.draw.line(scr, C_LPANEL_LINE,
                             (_RX, btn_y - 6), (W-_PAD-4, btn_y - 6), 1)

            bx = _RX
            def _gbtn(action, label, danger=False):
                nonlocal bx
                r = pygame.Rect(bx, btn_y, BTN_W, _BTN_H)
                self._btn_rects[action] = r
                hover = (self._hover_btn == action)
                _draw_gothic_btn(scr, label, r, hover=hover, danger=danger)
                bx += BTN_W + BTN_GAP

            if cat in (IC_POTION, IC_SCROLL, IC_FOOD, IC_WAND):
                _gbtn('use', _USE_VERB.get(cat, "Use"))
            equippable = cat in (IC_WEAPON, IC_ARMOR, IC_RING)
            if equippable:
                equipped = any(eq is cur for eq in p.equipped.values())
                slot = cur.get("slot","")
                if slot == "throw":
                    _gbtn('throw', 'Throw')
                    _gbtn('equip', 'Unready' if equipped else 'Ready')
                else:
                    _gbtn('equip', 'Remove'  if equipped else 'Equip')
            _gbtn('drop', 'Drop', danger=True)
            _gbtn('close', 'Close')

        # ── Status bar ────────────────────────────────────────────────────────
        sb_y = H - _PAD - _SBH + 4
        pygame.draw.line(scr, C_BLACK, (_PAD, sb_y), (W-_PAD, sb_y), 1)
        hint = _mono(13).render(
            "[↑↓ / a–t] select   [U] use   [E] equip/remove   [D] drop   [ESC / Close] close",
            True, C_LTEXT_DIM)
        scr.blit(hint, (_PAD+14, sb_y+10))


# ── Wish popup overlay ────────────────────────────────────────────────────────

class WishPopup:
    """Full-screen darkening + centred input box for the wish scroll."""

    _W = 700
    _H = 180

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def draw(self, game):
        scr  = self.screen
        W, H = SCREEN_W, SCREEN_H

        # Darken
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        scr.blit(overlay, (0, 0))

        # Box
        bx = (W - self._W) // 2
        by = (H - self._H) // 2
        pygame.draw.rect(scr, C_WHITE, (bx, by, self._W, self._H), border_radius=8)
        pygame.draw.rect(scr, C_BLACK, (bx, by, self._W, self._H), 2, border_radius=8)

        # Title
        uses_left = 3 - getattr(game, "wish_uses", 0)
        title = _frak(28).render("What is your wish?", True, C_BLACK)
        scr.blit(title, (bx + (self._W - title.get_width()) // 2, by + 14))

        hint = _mono(12).render(
            f"Type item name (+ +N for enchant, plural for ×2 scrolls/potions)  "
            f"[Enter] confirm   [Esc] cancel   {uses_left}/3 uses remain",
            True, C_LTEXT_DIM)
        scr.blit(hint, (bx + (self._W - hint.get_width()) // 2, by + 50))

        # Input field
        fx = bx + 30; fy = by + 88; fw = self._W - 60; fh = 36
        pygame.draw.rect(scr, (245, 245, 255), (fx, fy, fw, fh), border_radius=4)
        pygame.draw.rect(scr, C_BLACK,         (fx, fy, fw, fh), 2, border_radius=4)

        text    = getattr(game, "wish_input", "")
        ti = _gothic(22).render(text + "|", True, (30, 30, 120))
        scr.blit(ti, (fx + 10, fy + (fh - ti.get_height()) // 2))

        # Remaining wish counter dots
        dot_y = by + self._H - 22
        for i in range(3):
            cx = bx + self._W // 2 - 24 + i * 24
            filled = i < uses_left
            col = (80, 80, 200) if filled else (200, 200, 200)
            pygame.draw.circle(scr, col, (cx, dot_y), 7)
            pygame.draw.circle(scr, C_BLACK, (cx, dot_y), 7, 1)



# ═══════════════════════════════════════════════════════════════════════════════
# QuickUseScreen — fast consumable use overlay, styled like InventoryScreen
# ═══════════════════════════════════════════════════════════════════════════════

_QU_VERB = {
    IC_POTION: ("Potions",  "Drink"),
    IC_SCROLL: ("Scrolls",  "Read"),
    IC_WAND:   ("Wands",    "Zap"),
    IC_FOOD:   ("Food",     "Eat"),
    "throw":   ("Missiles", "Throw"),
}


class QuickUseScreen:
    """Consumable-use overlay that shares exact visual style with InventoryScreen.
    Shows only one item category; click or press letter to use instantly."""

    def __init__(self, screen: pygame.Surface):
        self.screen       = screen
        self.selected     = 0
        self.scroll_offset = 0
        self._row_rects:  list = []
        self._btn_rects:  dict = {}
        self._close_rect        = None
        self._hover_btn:  str  = ""

    # ── List helpers ──────────────────────────────────────────────────────────

    def _build_list(self, game) -> list:
        cat = getattr(game, "quick_use_cat", IC_POTION)
        if cat == "throw":
            return [it for it in game.player.inventory if it.get("slot") == "throw"]
        return [it for it in game.player.inventory if it.get("cat") == cat]

    def navigate(self, delta: int, game):
        items = self._build_list(game)
        if items:
            self.selected = (self.selected + delta) % len(items)
            self._ensure_visible(game)

    def scroll(self, delta: int, game):
        items   = self._build_list(game)
        vis     = max(1, _IH // _LH - 1)
        max_off = max(0, len(items) - vis)
        self.scroll_offset = max(0, min(max_off, self.scroll_offset + delta))

    def _ensure_visible(self, game):
        vis = max(1, _IH // _LH - 1)
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + vis:
            self.scroll_offset = self.selected - vis + 1

    def current_item(self, game):
        items = self._build_list(game)
        if items and 0 <= self.selected < len(items):
            return items[self.selected]
        return None

    # ── Mouse handling ────────────────────────────────────────────────────────

    def handle_motion(self, mx: int, my: int):
        self._hover_btn = ""
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(mx, my):
                self._hover_btn = name; return

    def handle_click(self, mx: int, my: int, game) -> str:
        """Return action string: 'use', 'close', 'select', or ''."""
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(mx, my):
                return name          # 'use', 'close'
        for rect, idx in self._row_rects:
            if rect.collidepoint(mx, my):
                if idx == self.selected:
                    return "use"     # click already-selected row = use it
                else:
                    self.selected = idx
                    return "select"
        # Click outside the panel = close
        panel = pygame.Rect(_PAD, _PAD, SCREEN_W - _PAD * 2, SCREEN_H - _PAD * 2)
        if not panel.collidepoint(mx, my):
            return "close"
        return ""

    # ── Keyboard handling ─────────────────────────────────────────────────────

    def _activate(self, item, game) -> bool:
        """Activate selected item: throw-select enters aim, others use immediately.
        Returns True when the overlay should close."""
        if getattr(game, "quick_use_cat", "") == "throw":
            game.begin_throw_aim(item)
            return True    # overlay closes; PHASE_THROW_AIM takes over
        msg, col = game.use_item(item)
        game.log.add(msg, col)
        return True

    def handle_key(self, key: int, game) -> bool:
        """Returns True if the overlay should close."""
        if key == pygame.K_ESCAPE:
            return True
        items = self._build_list(game)
        # U / Enter = activate selected
        if key in (pygame.K_u, pygame.K_RETURN):
            item = self.current_item(game)
            if item:
                return self._activate(item, game)
            return True
        # Navigate
        if key in (pygame.K_UP, pygame.K_k):
            self.navigate(-1, game); return False
        if key in (pygame.K_DOWN, pygame.K_j):
            self.navigate(+1, game); return False
        # Letter select — activate immediately
        if pygame.K_a <= key <= pygame.K_z:
            idx = key - pygame.K_a
            if 0 <= idx < len(items):
                self.selected = idx
                return self._activate(items[idx], game)
        return False

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, game):
        scr  = self.screen
        W, H = SCREEN_W, SCREEN_H

        self._row_rects = []
        self._btn_rects = {}

        cat = getattr(game, "quick_use_cat", IC_POTION)
        items = self._build_list(game)
        cat_label, verb = _QU_VERB.get(cat, ("Items", "Use"))

        # ── Same dark overlay + white panel as InventoryScreen ────────────────
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        scr.blit(overlay, (0, 0))
        pygame.draw.rect(scr, C_WHITE, (_PAD, _PAD, W - _PAD * 2, H - _PAD * 2))
        pygame.draw.rect(scr, C_BLACK, (_PAD, _PAD, W - _PAD * 2, H - _PAD * 2), 2)

        # ── Title bar ──────────────────────────────────────────────────────────
        pygame.draw.line(scr, C_BLACK, (_PAD, _PAD + _TH), (W - _PAD, _PAD + _TH), 1)

        ti = _frak(34).render(cat_label, True, C_BLACK)
        scr.blit(ti, (_PAD + 14, _PAD + (_TH - ti.get_height()) // 2))

        # Item count — right-aligned in title bar (no × button)
        cnt_txt = f"{len(items)} item(s)"
        cnt = _mono(15).render(cnt_txt, True, C_LTEXT_DIM)
        cnt_x = W - _PAD - cnt.get_width() - 14
        scr.blit(cnt, (cnt_x, _PAD + (_TH - cnt.get_height()) // 2))
        self._close_rect = None   # Close is a gothic button in the action area

        # Vertical divider (same position as InventoryScreen)
        div_x = _PAD + _LW + 10
        pygame.draw.line(scr, C_LPANEL_LINE,
                         (div_x, _PAD + _TH + 4), (div_x, H - _PAD - _SBH - 4), 1)

        # ── Item list — identical geometry to InventoryScreen ─────────────────
        y   = _PAD + _IY
        vis = max(1, _IH // _LH - 1)

        for idx, item in enumerate(items):
            if idx < self.scroll_offset:
                continue
            if y > _PAD + _IY + _IH - _LH:
                break

            row_rect = pygame.Rect(_PAD + 2, y - 1, _LW + 6, _LH)
            self._row_rects.append((row_rect, idx))

            selected = (idx == self.selected)
            if selected:
                pygame.draw.rect(scr, (0, 0, 120), row_rect)
                txt_col = C_WHITE
            else:
                txt_col = C_LTEXT

            ch   = chr(ord('a') + idx) if idx < 26 else '?'
            lbdg = _mono(14, bold=True).render(
                f"{ch})", True, C_WHITE if selected else C_LTEXT_DIM)
            scr.blit(lbdg, (_PAD + 14, y + 2))

            nm_img = _mono(14, bold=selected).render(
                game.item_display_name(item), True, txt_col)
            scr.blit(nm_img, (_PAD + 36, y + 2))

            y += _LH

        if not items:
            msg = f"You have no {cat_label.lower()}."
            empty = _mono(16).render(msg, True, C_LTEXT_DIM)
            scr.blit(empty, (_PAD + _LW // 2 - empty.get_width() // 2,
                             _PAD + _IY + _IH // 2))

        # Scroll indicators
        _draw_scroll_indicators(scr, items, self.scroll_offset,
                                max(1, _IH // _LH - 1), _PAD, _IY, _IH, _LW)

        # ── Right column: item detail (same as InventoryScreen upper pane) ─────
        cur      = self.current_item(game)
        btn_area = _BTN_H + 24
        det_bot  = H - _PAD - _SBH - btn_area

        if cur:
            detail = _item_detail_lines(cur, game)
            dy = _PAD + _IY + 4
            for i, (txt, col) in enumerate(detail):
                if dy + 20 > det_bot:
                    break
                if not txt:
                    dy += 6; continue
                img = (_frak(22) if i == 0 else _mono(14)).render(txt, True, col)
                if img.get_width() > _RW - 4:
                    img = img.subsurface((0, 0, _RW - 4, img.get_height()))
                scr.blit(img, (_RX, dy))
                dy += img.get_height() + (5 if i == 0 else 3)

        # ── Action buttons: verb + Close ──────────────────────────────────────────
        btn_y = H - _PAD - _SBH - _BTN_H - 6
        pygame.draw.line(scr, C_LPANEL_LINE,
                         (_RX, btn_y - 6), (W - _PAD - 4, btn_y - 6), 1)
        _qbx = _RX
        def _qbtn(action, label, danger=False):
            nonlocal _qbx
            r = pygame.Rect(_qbx, btn_y, 150, _BTN_H)
            self._btn_rects[action] = r
            _draw_gothic_btn(scr, label, r, hover=(self._hover_btn == action), danger=danger)
            _qbx += 150 + 10
        if cur:
            _qbtn("use", verb)
        _qbtn("close", "Close")

        # ── Status bar ──────────────────────────────────────────────────────────────────
        sb_y = H - _PAD - _SBH + 4
        pygame.draw.line(scr, C_BLACK, (_PAD, sb_y), (W - _PAD, sb_y), 1)
        n = len(items)
        last_ch = chr(ord('a') + max(0, n - 1)) if n else 'a'
        hint = _mono(13).render(
            f"[a\u2013{last_ch}] select & use   "
            f"[U / Enter] {verb}   [ESC / Close] close",
            True, C_LTEXT_DIM)
        scr.blit(hint, (_PAD + 14, sb_y + 10))
