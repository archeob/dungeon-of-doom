# ui/panels.py — Right game panel v0.108
#
# Panel: 528 × 864  (STATS_W=528, VP_PX=864 — same height as dungeon)
#
#  ┌──────────────────────────────────────────┐ y=4
#  │     Character Name  (Fraktur 40pt)       │ h=52
#  └──────────────────────────────────────────┘
#  ──────────────────────────────── rule  y=60
#  Map (Frak 22pt)  │  Str: 17  18pt      y=66
#  180×180 tiles    │  Int: 10            y=92
#  (MM=3)           │  Wis: 12
#                   │  Dex: 14
#                   │  Con: 16
#                   │  Chr: 14           y≈272
#  ──────────────────────────────── rule  y=276
#  Max HP        56                       y=282
#  Dungeon Level  2                       y=301
#  XP Level       5                       y=320
#  Experience 44/79                       y=339
#  HP: [████████████████████░] 56/56      y=364
#  FD: [████████░░░░░░░░░░░░░]            y=382
#  XP: [░░░░░░░░░░░░░░░░░░░░░]            y=400
#  ──────────────────────────────── rule  y=416
#  ATK +8   —  (weapon name)              y=422
#  AC   7   —  (armor name)               y=440
#  ──────────────────────────────── rule  y=462
#  Information  (Fraktur 22pt)            y=468
#  ▶ The Orc is slain!  +15 XP            y=496
#  …10 messages at LH=22 each…           →716

import pygame, os
from constants import *
from engine.game import MessageLog, GameState
from data.classes import get_class

# ── Layout constants (y-values relative to panel surface) ──────────────────────
_M  = 10   # margin

# Name box
_NM_Y = 4
_NM_H = 52
_R1_Y = _NM_Y + _NM_H + 4        # 60

# Upper section (map + attributes)
_CT       = _R1_Y + 6             # 66
_HDR_FZ   = 22                    # Fraktur pt for "Map" and "Information"
_LBL_H    = 26                    # approx pixel height of 22pt Fraktur

_MAP_LBL_Y = _CT                  # 66
_MAP_Y     = _CT + _LBL_H        # 92   tiles start flush under label
_MAP_MM    = 3
_MAP_PX    = MAP_COLS * _MAP_MM   # 180
_MAP_X     = _M                   # 10
_MAP_BOT   = _MAP_Y + _MAP_PX    # 272

_SX_ATTR   = _MAP_X + _MAP_PX + _M   # 200  attribute column x
_ATTR_FS   = 18                        # attribute font size

_R2_Y      = _MAP_BOT + 4        # 276

# Secondary stats block
_BSY  = _R2_Y + 6                # 282
_LH_D = 19                       # label+value row height

_Y_MHP = _BSY                    # 282  Max HP
_Y_DLV = _Y_MHP + _LH_D         # 301  Dungeon Level
_Y_XLV = _Y_DLV + _LH_D         # 320  XP Level
_Y_EXP = _Y_XLV + _LH_D         # 339  Experience

# Bars (6px gap after last label row)
_LH_B  = 18
_Y_HP  = _Y_EXP + _LH_D + 6     # 364
_Y_FD  = _Y_HP  + _LH_B         # 382
_Y_XP  = _Y_FD  + _LH_B         # 400
_Y_WT  = _Y_XP  + 14            # 414  Weight bar row
_Y_R3  = _Y_WT  + 22            # 436  rule below weight bar (18px row + 4 gap)

# Equipment rows with ATK/AC inline (no Gold, no Turn)
_Y_WPN = _Y_R3  + 6             # 442  ATK value + weapon name
_Y_ARM = _Y_WPN + 18            # 460  AC value  + armor name
_FLAG_Y = _Y_ARM + 18           # 478  status flags (if any)

# Info section — rule/header/messages y-positions are computed dynamically
# in draw() after the actual flag count is known, to avoid overlap.
_INF_LH      = 22   # message line height
_INF_LH_FLAG = 18   # flag row height

# Bar geometry (depends on panel width at runtime, but _BX is fixed)
_BX = _M + 38   # bar left edge (space for "HP:" label)

# ── Font cache ─────────────────────────────────────────────────────────────────
_FC: dict = {}

def _fraktur(size: int) -> pygame.font.Font:
    k = ("frak", size)
    if k not in _FC:
        path = os.path.join(os.path.dirname(__file__), "..", FONT_FRAKTUR)
        try:
            _FC[k] = pygame.font.Font(path, size)
        except Exception:
            _FC[k] = pygame.font.Font(
                "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf", size)
    return _FC[k]

def _mono(size: int, bold: bool = False) -> pygame.font.Font:
    k = ("mono", size, bold)
    if k not in _FC:
        _FC[k] = pygame.font.SysFont(FONT_MONO, size, bold=bold)
    return _FC[k]

def _serif(size: int, bold: bool = False) -> pygame.font.Font:
    k = ("serif", size, bold)
    if k not in _FC:
        _FC[k] = pygame.font.SysFont("serif", size, bold=bold)
    return _FC[k]

def _blit_c(surf, img, cx, y):
    surf.blit(img, (cx - img.get_width() // 2, y))

def _hrule(surf, y, x0, x1, col=C_LPANEL_LINE):
    pygame.draw.line(surf, col, (x0, y), (x1, y), 1)

def _bar(surf, x, y, w, h, pct, chi, clo, bg=(220, 220, 220)):
    pct = max(0.0, min(1.0, pct))
    col = chi if pct > 0.5 else C_HP_MID if pct > 0.25 else clo
    pygame.draw.rect(surf, bg, (x, y, w, h))
    pygame.draw.rect(surf, col, (x, y, max(2, int(w * pct)), h))
    pygame.draw.rect(surf, C_LPANEL_LINE, (x, y, w, h), 1)


# ── Stats Panel ────────────────────────────────────────────────────────────────

class StatsPanel:
    def __init__(self, surf: pygame.Surface):
        self.surf = surf
        self.W    = surf.get_width()   # 528
        self.H    = surf.get_height()  # 864

    def draw(self, game: GameState):
        s = self.surf
        W = self.W
        s.fill(C_WHITE)

        if not game.player:
            pygame.draw.rect(s, C_LPANEL_BORD, (0, 0, W, self.H), 1)
            return

        p   = game.player
        BW  = W - _BX - _M            # bar width

        # ── NAME BOX ──────────────────────────────────────────────────────────
        pygame.draw.rect(s, C_WHITE, (_M, _NM_Y, W - _M*2, _NM_H))
        pygame.draw.rect(s, C_BLACK, (_M, _NM_Y, W - _M*2, _NM_H), 2)
        name_img = _fraktur(40).render(p.name, True, C_BLACK)
        _blit_c(s, name_img, W // 2,
                _NM_Y + (_NM_H - name_img.get_height()) // 2)

        # ── RULE 1 ─────────────────────────────────────────────────────────────
        _hrule(s, _R1_Y, _M, W - _M, C_BLACK)

        # ── MAP label — Fraktur, BLACK, centred over map area ─────────────────
        map_lbl = _fraktur(_HDR_FZ).render("Map", True, C_BLACK)
        _blit_c(s, map_lbl, _MAP_X + _MAP_PX // 2, _MAP_LBL_Y)

        # ── MAP ────────────────────────────────────────────────────────────────
        self._draw_map(s, game)

        # ── ATTRIBUTES (right of map) ──────────────────────────────────────────
        self._draw_attrs(s, p)

        # ── RULE 2 ─────────────────────────────────────────────────────────────
        _hrule(s, _R2_Y, _M, W - _M, C_BLACK)

        # ── SECONDARY STATS (returns bottom y after any status flags) ─────────
        bot_y = self._draw_secondary(s, game, p, BW)

        # ── RULE → INFO (dynamic so flags never push into header) ─────────────
        r5_y    = bot_y + 4
        inf_y   = r5_y  + 6
        inf_msg = inf_y + _LBL_H + 2
        _hrule(s, r5_y, _M, W - _M, C_BLACK)
        self._draw_info(s, game, inf_y, inf_msg)

        # Panel border
        pygame.draw.rect(s, C_LPANEL_BORD, (0, 0, W, self.H), 1)

    # ── Black-on-white mini-map ────────────────────────────────────────────────

    def _draw_map(self, surf, game: GameState):
        MM = _MAP_MM;  MX = _MAP_X;  MY = _MAP_Y
        if not game.player or not game.level:
            return
        lv = game.level;  fov = game.fov;  p = game.player

        pygame.draw.rect(surf, C_WHITE, (MX, MY, _MAP_PX, _MAP_PX))

        for (tx, ty) in fov.walked:
            tile = lv.get(tx, ty)
            rx   = MX + tx * MM
            ry   = MY + ty * MM
            if tile == T_WALL:
                pygame.draw.rect(surf, (40, 40, 40), (rx, ry, MM, MM))
            elif tile == T_STAIR_UP:
                pygame.draw.rect(surf, C_BLACK, (rx+1, ry+1, MM-2, MM-2))
                pygame.draw.polygon(surf, C_WHITE,
                    [(rx+MM//2, ry+1), (rx+1, ry+MM-1), (rx+MM-1, ry+MM-1)])
            elif tile == T_STAIR_DOWN:
                pygame.draw.rect(surf, C_BLACK, (rx+1, ry+1, MM-2, MM-2))
                pygame.draw.polygon(surf, C_WHITE,
                    [(rx+MM//2, ry+MM-1), (rx+1, ry+1), (rx+MM-1, ry+1)])
            else:
                pygame.draw.rect(surf, C_BLACK, (rx, ry, MM-1, MM-1))

        # Player dot
        px_x = MX + p.x * MM;  px_y = MY + p.y * MM
        pygame.draw.rect(surf, C_BLACK, (px_x-1, px_y-1, MM+2, MM+2))
        pygame.draw.rect(surf, C_WHITE, (px_x+1, px_y+1, MM-2, MM-2))

    # ── Six attributes right of map ────────────────────────────────────────────

    def _draw_attrs(self, surf, p):
        SX   = _SX_ATTR;  FS = _ATTR_FS
        ABBR = ["Str", "Int", "Wis", "Dex", "Con", "Chr"]
        lh   = _mono(FS).get_height() + 4
        sy   = _MAP_Y
        for i, abbr in enumerate(ABBR):
            v  = p.stats[i]
            vc = (20, 140, 20) if v >= 16 else C_HP_LOW if v <= 8 else C_LTEXT
            lbl = _mono(FS, bold=False).render(f"{abbr}:", True, C_LTEXT_DIM)
            val = _mono(FS, bold=True ).render(f"{v:2d}",  True, vc)
            surf.blit(lbl, (SX, sy))
            surf.blit(val, (SX + lbl.get_width() + 6, sy))
            sy += lh

    # ── Secondary stats: label+value, bars, equipment ─────────────────────────

    def _draw_secondary(self, surf, game, p, BW):
        M  = _M;  W = self.W
        fl = _mono(FONT_SZ_SM, bold=False)
        fv = _mono(FONT_SZ_SM, bold=True)

        # Compute value column x: just past the longest label + gap
        LABELS = ["Max HP", "Dungeon Level", "XP Level", "Experience"]
        val_x  = M + max(fl.size(l)[0] for l in LABELS) + 10

        def _lv(surf, lbl, val, y, vc=C_LTEXT):
            ls = fl.render(lbl, True, C_LTEXT_DIM)
            vs = fv.render(str(val), True, vc)
            surf.blit(ls, (M, y))
            surf.blit(vs, (val_x, y))

        _lv(surf, "Max HP",       p.max_hp,              _Y_MHP)
        _lv(surf, "Dungeon Level", game.floor,            _Y_DLV)
        _lv(surf, "XP Level",      p.level,              _Y_XLV)
        _lv(surf, "Experience",    f"{p.xp}/{p.xp_next}", _Y_EXP)

        # HP bar
        surf.blit(fv.render("HP:", True, C_LTEXT), (M, _Y_HP))
        _bar(surf, _BX, _Y_HP + 2, BW, 15, p.hp_pct, C_HP_FULL, C_HP_LOW)
        hp_n = _mono(FONT_SZ_SM - 2).render(f"{p.hp}/{p.max_hp}", True, C_WHITE)
        surf.blit(hp_n, (_BX + BW - hp_n.get_width() - 2, _Y_HP + 4))

        # Food bar
        surf.blit(fv.render("FD:", True, C_LTEXT), (M, _Y_FD))
        _bar(surf, _BX, _Y_FD + 2, BW, 15, p.food_pct, C_FOOD_OK, C_FOOD_LOW)

        # XP bar
        surf.blit(_mono(FONT_SZ_SM, bold=True).render("XP:", True, C_LTEXT_ACCENT),
                  (M, _Y_XP))
        _bar(surf, _BX, _Y_XP + 2, BW, 10, p.xp_pct,
             C_LTEXT_ACCENT, C_LTEXT_ACCENT, bg=(210, 215, 235))

        # Weight / encumbrance bar  (uses _Y_WT constant, room below XP bar)
        wt_cur = p.carried_weight
        wt_cap = p.carry_capacity
        wt_pct = min(1.0, wt_cur / wt_cap) if wt_cap else 0.0
        if p.overburdened:   wt_col = C_HP_LOW
        elif p.encumbered:   wt_col = (210, 140, 20)
        else:                wt_col = (80,  160,  80)
        surf.blit(fv.render("WT:", True, C_LTEXT_DIM), (M, _Y_WT))
        _bar(surf, _BX, _Y_WT + 2, BW, 10, wt_pct, wt_col, C_HP_LOW, bg=(210,215,220))
        wt_txt = _mono(FONT_SZ_SM - 3).render(f"{wt_cur}/{wt_cap}", True, C_WHITE)
        surf.blit(wt_txt, (_BX + BW - wt_txt.get_width() - 2, _Y_WT + 3))

        # Thin rule
        _hrule(surf, _Y_R3, M, W - M)

        # ── Equipment with ATK / AC inline ────────────────────────────────────
        # Format: "ATK +8   Long Sword"
        #         "AC   7   Chain Mail"
        def equip_line(y, stat_lbl, stat_val, slot_k, slot_lbl):
            item = p.equipped.get(slot_k)
            nm   = (item["name"] if isinstance(item, dict) and "name" in item
                    else item.name if item else "—")
            # Stat name+value in fixed-width mono
            sv = fv.render(f"{stat_lbl} {stat_val}", True, C_LTEXT)
            # Equipment label + name
            el = fl.render(f"  {slot_lbl}:", True, C_LTEXT_DIM)
            en = _serif(FONT_SZ_SM).render(nm, True, C_LTEXT)
            surf.blit(sv, (M, y))
            stat_w = sv.get_width()
            surf.blit(el, (M + stat_w, y))
            surf.blit(en, (M + stat_w + el.get_width() + 4, y))

        equip_line(_Y_WPN, "ATK", f"+{p.attack_bonus}", "weapon", "Wpn")
        equip_line(_Y_ARM, "AC", f" {p.armor_class}",  "armor",  "Arm")

        # ── Nearby monster hostility summary ──────────────────────────────────
        fy = self._draw_nearby_hostility(surf, game, p, _FLAG_Y)

        # Status flags — filled diamond bullet, spatially separated from text.
        # Text blitted at M+12, diamond drawn in the 12-px left margin after blit.
        _SFLAG_W = 12
        for f in p.status_summary():
            fi = _mono(FONT_SZ_SM, bold=True).render(f, True, C_HP_LOW)
            lh = fi.get_height()
            surf.blit(fi, (M + _SFLAG_W, fy))
            # Diamond drawn after blit, entirely within left margin
            ds = 5; cx = M + ds; cy = fy + lh // 2
            pygame.draw.polygon(surf, C_HP_LOW, [
                (cx,      cy - ds),
                (cx + ds, cy),
                (cx,      cy + ds),
                (cx - ds, cy),
            ])
            fy += lh + 2
        return fy   # bottom y after flags (or _FLAG_Y if no flags)

    # ── Nearby monster hostility ───────────────────────────────────────────────

    def _draw_nearby_hostility(self, surf, game, p, start_y: int) -> int:
        """Draw a compact hostility status for visible monsters.
        Returns the y position after the last line drawn."""
        from constants import (HOSTILITY_AFRAID, HOSTILITY_NEUTRAL,
                               HOSTILITY_CAUTIOUS, HOSTILITY_HOSTILE,
                               HOSTILITY_DOT_COLOR)
        M = _M

        # Collect visible monsters
        visible_monsters = [
            m for m in game._floor_monsters()
            if (m.x, m.y) in game.fov.visible and m.alive
        ]
        if not visible_monsters:
            return start_y

        # Sort by distance to player
        visible_monsters.sort(
            key=lambda m: abs(m.x - p.x) + abs(m.y - p.y)
        )

        # Map hostility int → label
        _H_LABEL = {
            HOSTILITY_AFRAID:   "AFRAID",
            HOSTILITY_NEUTRAL:  "NEUTRAL",
            HOSTILITY_CAUTIOUS: "WARY",
            HOSTILITY_HOSTILE:  "HOSTILE",
        }

        fy    = start_y
        f_lbl = _mono(FONT_SZ_SM - 1, bold=False)
        f_mon = _mono(FONT_SZ_SM - 1, bold=True)
        DOT_R = 4
        shown = 0
        max_show = 4   # show at most 4 visible monsters

        for m in visible_monsters[:max_show]:
            h   = getattr(m, "current_hostility", HOSTILITY_HOSTILE)
            col = HOSTILITY_DOT_COLOR.get(h, (200, 80, 80))
            if getattr(m, "charmed", False):
                col = HOSTILITY_DOT_COLOR[HOSTILITY_NEUTRAL]
                h   = HOSTILITY_NEUTRAL
            lbl = _H_LABEL.get(h, "HOSTILE")

            # Dot
            dot_cx = M + DOT_R + 2
            dot_cy = fy + f_mon.get_linesize() // 2
            pygame.draw.circle(surf, (20, 20, 20), (dot_cx, dot_cy), DOT_R + 1)
            pygame.draw.circle(surf, col,          (dot_cx, dot_cy), DOT_R)

            # Monster name + hostility label
            name_txt = f_mon.render(m.name, True, (60, 60, 60))
            sep_txt  = f_lbl.render(" — ", True, (140, 140, 140))
            stat_txt = f_lbl.render(lbl, True, col)

            x = M + DOT_R * 2 + 6
            surf.blit(name_txt, (x, fy))
            x += name_txt.get_width()
            surf.blit(sep_txt,  (x, fy))
            x += sep_txt.get_width()
            surf.blit(stat_txt, (x, fy))

            fy += f_mon.get_linesize() + 1
            shown += 1

        if len(visible_monsters) > max_show:
            more = len(visible_monsters) - max_show
            etc = f_lbl.render(f"  + {more} more monster{'s' if more>1 else ''}…", True, (140,140,140))
            surf.blit(etc, (M, fy))
            fy += f_lbl.get_linesize() + 1

        # Small gap before status flags
        return fy + 3

    # ── Information panel ─────────────────────────────────────────────────────

    def _draw_info(self, surf, game: GameState, inf_y: int, inf_msg: int):
        W = self.W
        hdr = _fraktur(_HDR_FZ).render("Information", True, C_BLACK)
        surf.blit(hdr, (_M, inf_y))

        # Fill ALL available space below the header with messages
        avail   = self.H - inf_msg - 2
        n_fit   = max(1, avail // _INF_LH)
        messages = game.log.recent(n_fit)
        if not messages:
            return

        f_new  = _mono(FONT_SZ_SM, bold=True)
        f_old  = _mono(FONT_SZ_SM, bold=False)
        # _BULL_W: pixels reserved for the bullet marker to the left of text.
        # Text is always blitted at _M + _BULL_W so the polygon never touches it.
        _BULL_W = 12
        clip_w = W - _M * 2 - _BULL_W

        for i, (text, color) in enumerate(messages):
            iy = inf_msg + i * _INF_LH
            if iy + _INF_LH > self.H - 2:
                break
            if i == 0:
                col = tuple(max(0, min(255, int(ch * 0.70))) for ch in color)
                img = f_new.render(text, True, col)
            else:
                fade = max(55, 185 - i * 20)
                img  = f_old.render(text, True, (fade, fade, fade))

            if img.get_width() > clip_w:
                img = img.subsurface((0, 0, clip_w, img.get_height()))

            # Blit text in the right zone (x = _M + _BULL_W) — no polygon overlap
            surf.blit(img, (_M + _BULL_W, iy))

            # Draw the newest-message bullet (filled triangle) in the LEFT margin.
            # Drawn AFTER blit so x-ranges are guaranteed separate.
            if i == 0:
                th = img.get_height()
                bx = _M + 2;  by = iy + th // 2;  bs = max(3, th // 4)
                pygame.draw.polygon(surf, col, [
                    (bx,          by - bs),
                    (bx + bs * 2, by),
                    (bx,          by + bs),
                ])


# ── MessagePanel stub ──────────────────────────────────────────────────────────

class MessagePanel:
    """1×1 stub — not drawn."""
    def __init__(self, surf): self.surf = surf
    def draw(self, log: MessageLog): pass
