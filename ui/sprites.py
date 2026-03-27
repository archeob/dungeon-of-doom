# ui/sprites.py — v0.301  light Mac-style greyscale sprites
# Drawn at 3× internal resolution (288 px), smoothscaled to 96 px.
# Palette: near-white fills with dark outlines/details — faithful to the
# original 1985 Dungeon of Doom Mac aesthetic.

import pygame, math
from constants import TILE

T  = TILE   # 96  — display / output size
S  = 3      # internal scale factor
TS = T * S  # 288 — internal drawing canvas

# ── Greyscale helpers ─────────────────────────────────────────────────────────
def g(v):      return (v, v, v)
def ga(v, a):  return (v, v, v, a)
TR = (0,0,0,0)

# ── Canvas ────────────────────────────────────────────────────────────────────
def _canvas(alpha=False):
    if alpha:
        s = pygame.Surface((TS, TS), pygame.SRCALPHA)
        s.fill(TR)
    else:
        s = pygame.Surface((TS, TS))
        s.fill(g(255))
    return s

def _down(s) -> pygame.Surface:
    return pygame.transform.smoothscale(s, (T, T))

# ── Scale helpers (tile-space coords → internal px) ──────────────────────────
def px(x):     return x * S
def pw(w):     return max(1, w * S)

# ── Draw primitives ───────────────────────────────────────────────────────────
def fill(s, x, y, w, h, col):
    pygame.draw.rect(s, col, (px(x), px(y), pw(w), pw(h)))

def circle(s, cx, cy, r, col, width=0):
    pygame.draw.circle(s, col, (px(cx), px(cy)), pw(r),
                       pw(width) if width else 0)

def line(s, x1, y1, x2, y2, col, w=1):
    pygame.draw.line(s, col, (px(x1),px(y1)), (px(x2),px(y2)), pw(w))

def poly(s, pts, col):
    pygame.draw.polygon(s, col, [(px(x),px(y)) for x,y in pts])

def outline(s, x, y, w, h, col, thick=1):
    pygame.draw.rect(s, col, (px(x),px(y),pw(w),pw(h)), pw(thick))

def grad_v(s, x, y, w, h, top_v, bot_v):
    ph = pw(h)
    for i in range(ph):
        t = i / max(1, ph-1)
        v = int(top_v + (bot_v - top_v)*t)
        pygame.draw.line(s, g(v),
                         (px(x),   px(y)+i),
                         (px(x)+pw(w)-1, px(y)+i))

def grad_circle(s, cx, cy, r, hi_v, lo_v):
    pr = pw(r)
    for i in range(pr, -1, -1):
        t = (pr-i) / max(1, pr)
        v = int(hi_v + (lo_v - hi_v)*t)
        pygame.draw.circle(s, g(v), (px(cx),px(cy)), i)

# ── Stipple / dither helper (Mac-style light texture) ────────────────────────
def stipple(s, x, y, w, h, col_a, col_b, period=2):
    """Checkerboard of two greys — approximates Mac screen dithering."""
    for ry in range(px(y), px(y)+pw(h)):
        for rx in range(px(x), px(x)+pw(w)):
            s.set_at((rx, ry), col_a if (rx+ry) % period == 0 else col_b)


# ══════════════════════════════════════════════════════════════════════════════
#  TILE SPRITES
# ══════════════════════════════════════════════════════════════════════════════

def tile_wall(lit=True) -> pygame.Surface:
    """Stone wall — mid-grey brick faces, dark mortar, light bevel."""
    base_v   = 185 if lit else 148
    hi_v     = min(255, base_v + 50)
    lo_v     = max(0,   base_v - 35)
    mortar_v = max(0,   base_v - 90)

    s = _canvas()
    fill(s, 0, 0, 96, 96, g(base_v))

    # Three brick rows (32 px each)
    for row in range(3):
        ry = row * 32
        # Mortar bed at top of each row
        fill(s, 0, ry, 96, 2, g(mortar_v))
        # Top highlight on brick face
        fill(s, 1, ry+2, 94, 4, g(hi_v))
        # Main face — gentle gradient
        grad_v(s, 1, ry+6, 94, 22, base_v, lo_v)
        # Bottom shadow
        fill(s, 1, ry+28, 94, 2, g(lo_v - 20))
        # Vertical joint (staggered)
        jx = (48 + row*16) % 96
        fill(s, jx, ry+2, 2, 28, g(mortar_v))

    # Outer bevel
    fill(s, 0,  0, 96,  2, g(hi_v+20))
    fill(s, 0,  0,  2, 96, g(hi_v+20))
    fill(s, 0, 94, 96,  2, g(mortar_v))
    fill(s, 94, 0,  2, 96, g(mortar_v))

    return _down(s)

def tile_wall_dim(): return tile_wall(lit=False)


def _floor_base(lit, alt) -> pygame.Surface:
    """Stone floor — nearly white slab with fine grout border."""
    if not alt:
        base_v = 240 if lit else 190
    else:
        base_v = 225 if lit else 175
    grout_v = max(0, base_v - 60)
    hi_v    = min(255, base_v + 10)
    lo_v    = max(0,   base_v - 20)

    s = _canvas()
    # Grout surround
    fill(s, 0, 0, 96, 96, g(grout_v))
    # Slab face
    grad_v(s, 2, 2, 92, 92, hi_v, lo_v)
    # Inner highlight edges
    fill(s, 2,  2, 92,  3, g(hi_v))
    fill(s, 2,  2,  3, 92, g(min(255, hi_v+5)))
    # Inner shadow edges
    fill(s, 2, 88, 92,  4, g(lo_v - 8))
    fill(s, 88, 2,  4, 90, g(lo_v - 6))
    # Subtle surface chips
    chip_v = max(0, base_v - 18)
    for gx, gy in [(12,14),(29,8),(46,22),(62,11),(77,18),
                    (9,51),(34,48),(53,62),(70,45),(85,58),
                    (20,75),(49,82),(65,70)]:
        if gx < 90 and gy < 90:
            fill(s, gx, gy, 3, 2, g(chip_v))

    return _down(s)

def tile_floor_light(lit=True): return _floor_base(lit, False)
def tile_floor_grey(lit=True):  return _floor_base(lit, True)


def tile_stair_down() -> pygame.Surface:
    s = _canvas()
    grad_v(s, 0, 0, 96, 96, 245, 210)
    fill(s, 0, 0, 96, 2, g(80)); fill(s, 0, 94, 96, 2, g(60))
    fill(s, 0, 0,  2, 96, g(80)); fill(s, 94, 0,  2, 96, g(60))
    c = 48
    for n,(x1,x2,y) in enumerate([
        (c-5,c+5,c-26),(c-12,c+12,c-13),(c-19,c+19,c),
        (c-26,c+26,c+13),(c-33,c+33,c+26)
    ]):
        thick = 4+n
        top_v = 50; bot_v = 35
        grad_v(s, x1, y, x2-x1, thick, top_v, bot_v)
    return _down(s)

def tile_stair_up() -> pygame.Surface:
    s = _canvas()
    grad_v(s, 0, 0, 96, 96, 248, 215)
    fill(s, 0, 0, 96, 2, g(80)); fill(s, 0, 94, 96, 2, g(60))
    fill(s, 0, 0,  2, 96, g(80)); fill(s, 94, 0,  2, 96, g(60))
    c = 48
    for n,(x1,x2,y) in enumerate([
        (c-33,c+33,c-26),(c-26,c+26,c-13),(c-19,c+19,c),
        (c-12,c+12,c+13),(c-5,c+5,c+26)
    ]):
        thick = 4+(4-n)
        grad_v(s, x1, y, x2-x1, thick, 45, 30)
    return _down(s)


def tile_boulder() -> pygame.Surface:
    """Boulder — a roughly rounded stone resting on the floor.
    Palette: lit floor background, medium-grey rock body with top highlight
    and bottom shadow, dark fissure cracks to show partial destruction.
    Drawn at 3× (288 px) then smoothscaled to 96 px for AA edges.
    """
    # Floor background (same as tile_floor_light lit)
    s = _canvas()
    grout_v = 180
    fill(s, 0, 0, 96, 96, g(grout_v))
    grad_v(s, 2, 2, 92, 92, 250, 230)

    # Rock body — slightly-irregular filled ellipse, built as layered rects
    # Centre (48, 50), roughly 36 wide × 32 tall
    cx, cy = 48, 50
    rock_hi  = 175   # top highlight
    rock_mid = 135   # mid tone
    rock_lo  = 90    # bottom shadow
    shadow   = 55    # cast shadow under boulder
    crack    = 45    # fissure lines

    # Cast shadow on floor (slightly offset down-right)
    for i in range(5):
        alpha = 60 - i * 10
        w = 30 - i * 2
        fill(s, cx - w//2 + 3, cy + 14 + i, w, 2, g(rock_lo - 20))

    # Draw rock as a series of horizontal bands — widest at equator
    bands = [
        # (y_offset_from_cy, half_width, value)
        (-16,  8, rock_mid),
        (-13, 16, rock_mid),
        (-10, 22, rock_mid + 10),
        ( -7, 27, rock_hi),
        ( -4, 30, rock_hi),
        ( -1, 32, rock_hi - 5),
        (  2, 32, rock_mid),
        (  5, 31, rock_mid - 10),
        (  8, 28, rock_lo + 15),
        ( 11, 24, rock_lo + 5),
        ( 14, 18, rock_lo),
        ( 16, 10, rock_lo - 10),
    ]
    for dy, hw, v in bands:
        fill(s, cx - hw, cy + dy, hw * 2, 3, g(v))

    # Top specular highlight — small bright patch top-left of centre
    fill(s, cx - 14, cy - 14, 12, 5, g(210))
    fill(s, cx - 12, cy - 10, 8, 3, g(195))

    # Dark cracks — irregular fissure lines showing partial destruction
    # Main diagonal crack, top-right to lower-left
    line(s, cx + 6, cy - 12, cx - 2, cy + 2,  g(crack), 2)
    line(s, cx - 2, cy + 2,  cx + 4, cy + 10, g(crack), 2)
    # Secondary crack branching left
    line(s, cx - 2, cy + 2,  cx - 10, cy + 6, g(crack), 1)
    # Small chip crack upper area
    line(s, cx + 8, cy - 6, cx + 14, cy - 2, g(crack), 1)

    # Thin dark outline around rock body for silhouette clarity
    outline(s, cx - 32, cy - 17, 64, 34, g(70), thick=1)

    return _down(s)




def sprite_player() -> pygame.Surface:
    s = _canvas(alpha=True)
    c = 48

    # Armour: dark body, lighter highlights
    ARM_D  = 35     # deep shadow
    ARM_M  = 75     # main armour face
    ARM_H  = 130    # highlight / lit edge
    ARM_R  = 175    # brightest rim catch
    BLADE  = 235    # sword blade near-white
    BLADE_H= 255
    GUARD  = 155
    GRIP   = 45
    SHLD_D = 50
    SHLD_M = 95
    SHLD_R = 145
    CROSS  = 200

    # ── Sword blade (behind body) ─────────────────────────────────────────────
    for i in range(42):
        bx, by = c+24+i, 58-i
        line(s, bx, by, bx+3, by, g(BLADE), 3)
        line(s, bx, by, bx, by-1, g(BLADE_H), 1)
    for i in range(5):
        circle(s, c+65+i, 17-i, 1, g(BLADE))

    # ── Shield ────────────────────────────────────────────────────────────────
    poly(s, [(c-44,32),(c-28,32),(c-28,60),(c-36,72)], g(SHLD_M))
    poly(s, [(c-44,32),(c-44,60),(c-36,72),(c-28,60),(c-28,32)], g(SHLD_D))
    outline(s, c-44, 32, 16, 30, g(SHLD_R), 1)
    line(s, c-44, 45, c-28, 45, g(CROSS), 2)
    line(s, c-37, 32, c-37, 60, g(CROSS), 2)

    # ── Crossguard ────────────────────────────────────────────────────────────
    fill(s, c+16, 55, 26, 6, g(GUARD))
    fill(s, c+16, 55, 26, 2, g(min(255,GUARD+40)))

    # ── Grip + pommel ─────────────────────────────────────────────────────────
    for t in range(3):
        fill(s, c+26+t, 61, 2, 12, g(GRIP))
    grad_circle(s, c+29, 74, 5, ARM_H, ARM_M)

    # ── Gorget ────────────────────────────────────────────────────────────────
    grad_v(s, c-8, 31, 16, 6, ARM_H, ARM_M)

    # ── Pauldrons ─────────────────────────────────────────────────────────────
    for px2 in (c-26, c+12):
        grad_v(s, px2, 34, 14, 10, ARM_H, ARM_M)
        fill(s, px2, 34, 14, 2, g(ARM_R))
        fill(s, px2, 43, 14, 2, g(ARM_D))

    # ── Cuirass ───────────────────────────────────────────────────────────────
    grad_v(s, c-18, 37, 36, 26, ARM_H, ARM_M)
    fill(s, c-2,  38, 4, 25, g(ARM_R))
    fill(s, c-18, 37, 2, 26, g(ARM_R))
    fill(s, c+16, 37, 2, 26, g(ARM_R))
    fill(s, c-18, 37, 36, 2, g(ARM_R))
    fill(s, c-17, 62, 34,  2, g(ARM_D))

    # ── Sword arm ─────────────────────────────────────────────────────────────
    grad_v(s, c+18, 38, 10, 20, ARM_H, ARM_M)
    grad_circle(s, c+23, 53, 7, ARM_M, ARM_D)
    fill(s, c+16, 46, 14, 2, g(ARM_R))
    fill(s, c+26, 38,  2, 20, g(ARM_R))

    # ── Shield arm ────────────────────────────────────────────────────────────
    grad_v(s, c-28, 38, 10, 20, ARM_H, ARM_M)
    grad_circle(s, c-23, 53, 6, ARM_M, ARM_D)
    fill(s, c-29, 46, 12, 2, g(ARM_R))

    # ── Faulds + tassets ──────────────────────────────────────────────────────
    grad_v(s, c-16, 63, 32, 10, ARM_H, ARM_M)
    fill(s, c-16, 63, 32, 2, g(ARM_R))
    fill(s, c-16, 72, 32, 2, g(ARM_D))
    for tx in (c-14, c+2):
        grad_v(s, tx, 73, 12, 10, ARM_M, ARM_D)
        fill(s, tx, 73, 12, 2, g(ARM_R))

    # ── Greaves ───────────────────────────────────────────────────────────────
    for lx in (c-12, c+2):
        grad_v(s, lx, 83, 10, 13, ARM_H, ARM_M)
        fill(s, lx,   83, 2, 13, g(ARM_R))
        fill(s, lx+8, 83, 2, 13, g(ARM_R))

    # ── Helmet ────────────────────────────────────────────────────────────────
    grad_circle(s, c, 16, 15, ARM_H, ARM_M)
    grad_v(s, c-14, 16, 28, 14, ARM_H, ARM_M)
    for vy in (15, 17, 19):
        fill(s, c-8, vy, 15, 2, g(ARM_D - 5))
    for deg in range(185, 355, 2):
        rx = int(c + 14*math.cos(math.radians(deg)))
        ry = int(16 + 14*math.sin(math.radians(deg)))
        circle(s, rx, ry, 1, g(ARM_R))
    fill(s, c-15, 29, 30, 2, g(ARM_M))
    fill(s, c-14, 30, 28, 2, g(ARM_R))

    return _down(s)

# ══════════════════════════════════════════════════════════════════════════════
#  MONSTER SPRITES — dark silhouettes on transparent (floor shows through)
# ══════════════════════════════════════════════════════════════════════════════

# Tier map: base brightness — kept dark so figures read on light floors
_TIER = {'r':55,'b':60,'k':65,'o':70,'s':75,'z':80,
         'E':85,'D':80,'d':75,'V':90,'X':95,'P':88,'W':78}

def sprite_monster(glyph: str, color: tuple) -> pygame.Surface:
    s  = _canvas(alpha=True)
    m  = 48
    bv = _TIER.get(glyph, 72)
    hi = min(200, bv + 70)
    lo = max(10,  bv - 30)
    ey = g(15)
    eh = g(240)

    if glyph == 'b':
        poly(s, [(5,34),(m,m-12),(91,34),(m,m+14)], g(lo))
        poly(s, [(m-2,m-10),(5,34),(m,m+8)],  g(bv))
        poly(s, [(m+2,m-10),(91,34),(m,m+8)], g(bv))
        grad_circle(s, m, m, 12, hi, bv)
        circle(s, m-5, m-4, 3, ey); circle(s, m+5, m-4, 3, ey)
        circle(s, m-5, m-4, 1, eh); circle(s, m+5, m-4, 1, eh)

    elif glyph in ('k','o'):
        r_head = 13 if glyph=='o' else 10
        grad_circle(s, m, 18, r_head, hi, bv)
        grad_v(s, m-12, 30, 24, 24, bv, lo)
        fill(s, m-22, 34, 8, 22, g(bv))
        fill(s, m+14, 34, 8, 22, g(bv))
        fill(s, m-10, 54, 8, 24, g(bv))
        fill(s, m+2,  54, 8, 24, g(bv))
        ey2 = 14 if glyph=='o' else 16
        for ex2 in (m-5, m+5):
            circle(s, ex2, ey2, 3, ey); circle(s, ex2, ey2, 1, eh)
        if glyph == 'o':
            line(s, m+24, 20, m+22, 52, g(hi), 3)
            grad_circle(s, m+22, 18, 7, hi, bv)

    elif glyph == 'r':
        grad_circle(s, m-16, m+4, 12, hi, bv)
        poly(s, [(m-25,m-5),(m+22,m-8),(m+26,m+12),(m-22,m+14)], g(bv))
        fill(s, m-16, m-4, 38, 20, g(bv))
        for i in range(22):
            circle(s, m+23+i, m+10-i//4, max(1, 3-i//8), g(max(lo, bv-i)))
        circle(s, m-20, m, 3, ey); circle(s, m-20, m, 1, eh)

    elif glyph in ('s','z'):
        grad_circle(s, m, 20, 15, hi, bv)
        circle(s, m-5, 18, 5, ey); circle(s, m+5, 18, 5, ey)
        circle(s, m-5, 18, 2, g(bv-10)); circle(s, m+5, 18, 2, g(bv-10))
        for tx in range(m-6, m+8, 4):
            fill(s, tx, 30, 3, 5, g(hi))
        grad_v(s, m-10, 36, 20, 26, bv, lo)
        for ry2 in (38,44,50,56):
            fill(s, m-13, ry2, 26, 2, g(lo))
        fill(s, m-22, 36, 8, 24, g(bv if glyph=='z' else lo))
        fill(s, m+14, 36, 8, 24, g(bv if glyph=='z' else lo))
        fill(s, m-9,  62, 7, 26, g(bv)); fill(s, m+2, 62, 7, 26, g(bv))

    elif glyph == 'E':
        for hx in (m-12, m+12):
            grad_circle(s, hx, 14, 11, hi, bv)
            circle(s, hx-3, 12, 3, ey); circle(s, hx-3, 12, 1, eh)
        fill(s, m-10, 24, 8, 6, g(bv)); fill(s, m+2, 24, 8, 6, g(bv))
        grad_v(s, m-22, 30, 44, 30, hi, bv)
        fill(s, m-36, 28, 14, 28, g(bv)); fill(s, m+22, 28, 14, 28, g(bv))
        grad_circle(s, m-29, 58, 8, hi, bv)
        grad_circle(s, m+29, 58, 8, hi, bv)
        fill(s, m-18, 60, 14, 28, g(bv)); fill(s, m+4, 60, 14, 28, g(bv))

    elif glyph in ('D','d'):
        poly(s, [(m-10,6),(m-20,30),(m-4,22)], g(hi))
        poly(s, [(m+10,6),(m+20,30),(m+4,22)], g(hi))
        grad_circle(s, m, 26, 16, hi, bv)
        circle(s, m-6, 22, 5, g(220)); circle(s, m+6, 22, 5, g(220))
        circle(s, m-6, 22, 3, ey);     circle(s, m+6, 22, 3, ey)
        grad_v(s, m-20, 42, 40, 32, bv, lo)
        poly(s, [(m-20,44),(4,22),(2,72),(m-6,62)], g(lo))
        poly(s, [(m+20,44),(92,22),(94,72),(m+6,62)], g(lo))
        fill(s, m-14, 74, 12, 22, g(bv)); fill(s, m+2, 74, 12, 22, g(bv))

    elif glyph == 'V':
        poly(s, [(m,8),(m-38,90),(m+38,90)], g(lo))
        poly(s, [(m-2,8),(m-28,70),(m+28,70),(m+2,8)], g(bv))
        grad_circle(s, m, 20, 14, hi, bv)
        circle(s, m-5, 17, 4, g(210)); circle(s, m+5, 17, 4, g(210))
        circle(s, m-5, 17, 2, ey);     circle(s, m+5, 17, 2, ey)
        fill(s, m-5, 30, 3, 6, g(hi)); fill(s, m+2, 30, 3, 6, g(hi))
        grad_circle(s, m-28, 58, 7, bv, lo)
        grad_circle(s, m+28, 58, 7, bv, lo)

    elif glyph == 'X':
        for i in range(50):
            w2 = 8 + i*22//50
            fill(s, m-w2, 34+i, w2*2, 2, g(max(lo, bv - i//3)))
        grad_circle(s, m, 22, 16, hi, bv)
        circle(s, m-6, 18, 6, ey); circle(s, m+6, 18, 6, ey)
        circle(s, m-6, 18, 3, g(bv-10)); circle(s, m+6, 18, 3, g(bv-10))
        fill(s, m+20, 35, 8, 30, g(bv))
        grad_circle(s, m+24, 34, 9, 220, 150)
        circle(s, m+24, 34, 9, g(hi), 2)

    elif glyph == 'P':
        for i in range(56):
            a  = math.radians(i*6.4)
            rx = int(m + (14+i//5)*math.cos(a))
            ry = int(m + (18+i//6)*math.sin(a)*0.72)
            r  = max(1, 9-i//10)
            av = max(0, 200-i*3)
            if 0<=rx<96 and 0<=ry<96:
                pygame.draw.circle(s, ga(bv+i//3, av), (px(rx),px(ry)), pw(r))
        grad_circle(s, m, m-8, 16, hi, bv)
        circle(s, m-5, m-12, 4, ey); circle(s, m+5, m-12, 4, ey)
        circle(s, m-5, m-12, 2, eh); circle(s, m+5, m-12, 2, eh)

    elif glyph == 'W':
        for i in range(180):
            a  = math.radians(i*2)
            r  = 10+i//10
            rx = int(m+r*math.cos(a))
            ry = int(m+r*math.sin(a)*0.55)
            rad = max(1, 10-i//22)
            cv = max(lo, bv-i//4)
            if 0<=rx<96 and 0<=ry<96:
                pygame.draw.circle(s, g(cv), (px(rx),px(ry)), pw(rad))
        grad_circle(s, m+20, m-18, 10, hi, bv)
        circle(s, m+24, m-20, 4, ey); circle(s, m+24, m-20, 2, eh)

    else:
        outline(s, 12, 12, 72, 72, g(bv), 3)
        outline(s, 18, 18, 60, 60, g(lo), 2)
        circle(s, m-8, m, 8, g(bv)); circle(s, m+8, m, 8, g(bv))

    return _down(s)


# ══════════════════════════════════════════════════════════════════════════════
#  ITEM SPRITES — unique per item_id, Mac greyscale aesthetic
#  All drawn at 3× (288 px) then smoothscaled to 96 px for clean AA edges.
# ══════════════════════════════════════════════════════════════════════════════

# ── Weapon helpers ─────────────────────────────────────────────────────────────

def _blade(s, x1,y1, x2,y2, thick=5, edge_v=195, body_v=55, tip_glint=True):
    """Draw a sword blade from tip (x1,y1) to hilt end (x2,y2)."""
    pygame.draw.line(s, g(body_v),  (px(x1),px(y1)), (px(x2),px(y2)), pw(thick))
    pygame.draw.line(s, g(edge_v),  (px(x1),px(y1)), (px(x2),px(y2)), pw(max(1,thick-3)))
    if tip_glint:
        pygame.draw.line(s, g(240), (px(x1),px(y1)), (px(x1),px(y1+2)), pw(2))

def _guard(s, x1,y1, x2,y2, thick=4, v=90, hi=165):
    """Draw a crossguard from (x1,y1) to (x2,y2)."""
    pygame.draw.line(s, g(v),  (px(x1),px(y1)), (px(x2),px(y2)), pw(thick))
    pygame.draw.line(s, g(hi), (px(x1),px(y1)), (px(x2),px(y2)), pw(max(1,thick-2)))

def _grip(s, x1,y1, x2,y2, thick=4):
    """Draw a grip (handle)."""
    pygame.draw.line(s, g(40), (px(x1),px(y1)), (px(x2),px(y2)), pw(thick))
    pygame.draw.line(s, g(90), (px(x1),px(y1)), (px(x2),px(y2)), pw(max(1,thick-2)))

def _pommel(s, cx,cy, r=5):
    """Draw a round pommel."""
    pygame.draw.circle(s, g(80),  (px(cx),px(cy)), pw(r))
    pygame.draw.circle(s, g(160), (px(cx),px(cy)), pw(r-1))

# ── Weapon sprites ─────────────────────────────────────────────────────────────

def _itm_long_sword(s):
    m = 48
    # Long diagonal blade: tip upper-right → base lower-left
    _blade(s,  74, 12,  32, 62,  thick=5)
    # Crossguard perpendicular at ~(40,54)
    _guard(s,  26, 54,  46, 72,  thick=4)
    # Grip
    _grip( s,  34, 64,  24, 76,  thick=4)
    # Pommel
    _pommel(s, 20, 81,  r=5)

def _itm_two_handed_sword(s):
    # Fills most of the tile — very long blade
    _blade(s,  80,  8,  22, 76,  thick=6, edge_v=210, body_v=50)
    # Wide crossguard
    _guard(s,  20, 62,  46, 82,  thick=5, v=80, hi=155)
    # Long grip
    _grip( s,  28, 72,  14, 86,  thick=5)
    # Large pommel
    _pommel(s, 10, 90,  r=6)

def _itm_dagger(s):
    # Short stubby blade
    _blade(s,  66, 24,  42, 56,  thick=4, edge_v=200, body_v=60)
    # Minimal guard
    _guard(s,  36, 52,  50, 64,  thick=3, v=100, hi=170)
    # Very short grip, no pommel
    _grip( s,  40, 60,  34, 68,  thick=3)
    _pommel(s, 31, 71,  r=3)

def _itm_leather_whip(s):
    m = 48
    # Handle at top-right, coiled S-curve sweeping to lower-left
    # Grip: thick short diagonal
    pygame.draw.line(s, g(60), (px(72),px(16)), (px(60),px(30)), pw(5))
    pygame.draw.line(s, g(130),(px(72),px(16)), (px(60),px(30)), pw(2))
    # Whip body: series of connected arcs forming an S-curve
    pts = [(60,30),(52,38),(44,46),(36,50),(28,56),(20,62),(14,70),(10,78)]
    for i in range(len(pts)-1):
        x1,y1 = pts[i]; x2,y2 = pts[i+1]
        thick = max(1, 4 - i//2)
        v = 45 + i * 8
        pygame.draw.line(s, g(v), (px(x1),px(y1)), (px(x2),px(y2)), pw(thick))
    # Tip: fine line
    pygame.draw.line(s, g(100),(px(10),px(78)),(px(6),px(86)), pw(1))

def _itm_mace(s):
    m = 48
    # Head: heavy flanged ball at upper-right
    cx, cy = 68, 22
    grad_circle(s, cx, cy, 16, 200, 110)
    circle(s, cx, cy, 16, g(40), 1)
    # Flanges: 6 radial spikes around the head
    for ang in range(0, 360, 60):
        ex = int(cx + 20*math.cos(math.radians(ang)))
        ey = int(cy + 20*math.sin(math.radians(ang)))
        pygame.draw.line(s, g(70), (px(cx),px(cy)), (px(ex),px(ey)), pw(4))
        pygame.draw.line(s, g(160),(px(cx),px(cy)), (px(ex),px(ey)), pw(2))
    # Re-draw ball over flanges
    grad_circle(s, cx, cy, 12, 210, 130)
    circle(s, cx, cy, 12, g(50), 1)
    # Specular highlight
    fill(s, cx-6, cy-8, 8, 5, g(240))
    # Handle diagonal
    pygame.draw.line(s, g(50), (px(56),px(36)),(px(22),px(78)), pw(5))
    pygame.draw.line(s, g(120),(px(56),px(36)),(px(22),px(78)), pw(2))
    # Pommel
    _pommel(s, 18, 82, r=5)

def _itm_death_blade(s):
    # Dark menacing serrated sword
    _blade(s, 78, 10, 28, 72, thick=6, edge_v=230, body_v=35)
    # Serrations along the back edge
    for i in range(5):
        bx = 70 - i*10; by = 18 + i*10
        pygame.draw.line(s, g(35), (px(bx),px(by)),(px(bx-6),px(by+4)), pw(3))
    # Dark skull-style crossguard — wide and heavy
    _guard(s, 22, 64, 48, 80, thick=6, v=50, hi=110)
    _grip( s, 30, 74, 20, 84, thick=4)
    # Dark pommel with glint
    pygame.draw.circle(s, g(40), (px(16),px(88)), pw(6))
    pygame.draw.circle(s, g(100),(px(16),px(88)), pw(3))
    fill(s, 13, 84, 4, 3, g(200))

def _itm_sling(s):
    m = 48
    # Y-shape: two diverging thongs from center cup, with a tail grip
    # Leather cup in center
    cx, cy = m, 50
    grad_circle(s, cx, cy, 10, 170, 100)
    circle(s, cx, cy, 10, g(50), 1)
    # Left thong going upper-left
    pygame.draw.line(s, g(70), (px(cx),px(cy-8)),(px(cx-24),px(cy-32)), pw(3))
    pygame.draw.line(s, g(140),(px(cx),px(cy-8)),(px(cx-24),px(cy-32)), pw(1))
    # Right thong going upper-right
    pygame.draw.line(s, g(70), (px(cx),px(cy-8)),(px(cx+24),px(cy-32)), pw(3))
    pygame.draw.line(s, g(140),(px(cx),px(cy-8)),(px(cx+24),px(cy-32)), pw(1))
    # Grip tail going down
    pygame.draw.line(s, g(55), (px(cx),px(cy+10)),(px(cx),px(cy+34)), pw(4))
    pygame.draw.line(s, g(110),(px(cx),px(cy+10)),(px(cx),px(cy+34)), pw(2))

def _itm_small_rock(s):
    m = 48
    cx, cy = m, m
    # Rough stone — layered slightly irregular circles
    grad_circle(s, cx, cy, 20, 190, 120)
    circle(s, cx, cy, 20, g(55), 1)
    # Surface chips and texture
    fill(s, cx-8, cy-12, 7, 4, g(160))
    fill(s, cx+4, cy-8,  5, 3, g(200))
    line(s, cx+6, cy+4, cx+12, cy+10, g(80), 1)
    line(s, cx-4, cy+8, cx+2, cy+12,  g(80), 1)

def _itm_large_rock(s):
    m = 48
    cx, cy = m, m
    grad_circle(s, cx, cy, 30, 185, 110)
    circle(s, cx, cy, 30, g(50), 1)
    fill(s, cx-14, cy-18, 10, 6, g(160))
    fill(s, cx+6, cy-12,  8, 4, g(200))
    line(s, cx+10, cy+6,  cx+18, cy+14, g(75), 2)
    line(s, cx-6,  cy+10, cx+4,  cy+16, g(75), 1)
    line(s, cx-14, cy-2,  cx-8,  cy+6,  g(75), 1)

def _itm_dart(s):
    # Thin needle — very sleek
    _blade(s, 80, 10, 30, 70, thick=3, edge_v=230, body_v=80)
    # Tiny flight fins at base
    pygame.draw.line(s, g(90), (px(36),px(64)),(px(28),px(76)), pw(3))
    pygame.draw.line(s, g(90), (px(36),px(64)),(px(44),px(72)), pw(3))

def _itm_spear(s):
    # Long shaft with triangular point at upper-right
    # Shaft: very thin, runs most of tile
    pygame.draw.line(s, g(60), (px(76),px(14)),(px(20),px(78)), pw(4))
    pygame.draw.line(s, g(140),(px(76),px(14)),(px(20),px(78)), pw(2))
    # Triangular spearhead
    poly(s, [(76,14),(68,8),(62,22)], g(200))
    poly(s, [(76,14),(68,8),(62,22)], g(200))
    pygame.draw.polygon(s, g(50), [(px(76),px(14)),(px(68),px(8)),(px(62),px(22))], pw(1))

def _itm_mac_plus(s):
    m = 48
    # Classic Macintosh Plus silhouette — iconic computer shape
    # Main body — cream/light grey box
    grad_v(s, m-26, 10, 52, 60, 220, 185)
    outline(s, m-26, 10, 52, 60, g(35), 2)
    # Screen bezel (dark rectangle inside top of body)
    fill(s, m-18, 16, 36, 28, g(30))
    # Screen interior (lighter)
    fill(s, m-16, 18, 32, 24, g(200))
    # Pixel face drawn on screen
    for ex,ey in [(m-8,22),(m+6,22)]:   # eyes
        fill(s, ex, ey, 4, 3, g(30))
    fill(s, m-6, 30, 12, 3, g(30))   # mouth
    # Drive slot
    fill(s, m-12, 50, 24, 4, g(40))
    fill(s, m-10, 51, 20, 2, g(100))
    # Neck / base
    grad_v(s, m-12, 70, 24, 12, 200, 170)
    outline(s, m-12, 70, 24, 12, g(50), 1)
    # Feet
    fill(s, m-22, 82, 16, 6, g(160))
    fill(s, m+6,  82, 16, 6, g(160))

# ── Armor sprites ──────────────────────────────────────────────────────────────

def _itm_leather_armor(s):
    m = 48
    # Simple body silhouette — soft, plain outlines
    grad_v(s, m-20, 14, 40, 42, 185, 130)
    outline(s, m-20, 14, 40, 42, g(50), 2)
    # Shoulder caps
    grad_v(s, m-26, 18, 12, 16, 175, 140); outline(s, m-26, 18, 12, 16, g(60), 1)
    grad_v(s, m+14, 18, 12, 16, 175, 140); outline(s, m+14, 18, 12, 16, g(60), 1)
    # Skirt
    for i in range(22):
        ww = 20 - i//2
        fill(s, m-ww, 56+i, ww*2, 2, g(max(50, 130-i*3)))
    # Chest stripe
    fill(s, m-2, 16, 4, 38, g(200))

def _itm_chain_armor(s):
    m = 48
    grad_v(s, m-22, 12, 44, 46, 195, 140)
    outline(s, m-22, 12, 44, 46, g(40), 2)
    # Chain pattern: small diamond grid
    for ry in range(16, 56, 5):
        for rx in range(m-20, m+20, 5):
            offset = 2 if (ry//5) % 2 else 0
            outline(s, rx+offset, ry, 4, 4, g(60), 1)
    # Shoulder plates
    grad_v(s, m-28, 16, 14, 18, 180, 140); outline(s, m-28, 16, 14, 18, g(50), 1)
    grad_v(s, m+14, 16, 14, 18, 180, 140); outline(s, m+14, 16, 14, 18, g(50), 1)
    # Skirt bands
    for i in range(20):
        ww = 22 - i//2
        v = max(40, 140-i*4)
        fill(s, m-ww, 58+i, ww*2, 2, g(v))

def _itm_banded_armor(s):
    m = 48
    grad_v(s, m-22, 10, 44, 50, 200, 145)
    outline(s, m-22, 10, 44, 50, g(35), 2)
    # Horizontal bands
    for by in range(14, 58, 7):
        fill(s, m-20, by, 40, 3, g(80))
        fill(s, m-20, by+1, 40, 1, g(160))
    # Pauldrons (shoulder guards)
    for bx in (m-30, m+16):
        grad_v(s, bx, 14, 14, 22, 185, 140); outline(s, bx, 14, 14, 22, g(45), 1)
        fill(s, bx, 14, 14, 3, g(210))
    # Skirt
    for i in range(22):
        ww = 22 - i//2
        fill(s, m-ww, 60+i, ww*2, 2, g(max(35, 145-i*4)))

def _itm_plate_armor(s):
    m = 48
    # Heavily stylised full plate — deep gradient, strong bevel
    grad_v(s, m-22, 8, 44, 54, 230, 150)
    outline(s, m-22, 8, 44, 54, g(30), 2)
    # Central ridge catch-light
    fill(s, m-2, 10, 4, 50, g(255))
    fill(s, m-6, 10, 12, 3, g(220))
    # Horizontal articulation lines
    for by in (22, 36, 48):
        fill(s, m-20, by, 40, 2, g(60))
    # Large pauldrons
    for bx in (m-32, m+18):
        grad_v(s, bx, 12, 14, 24, 210, 160); outline(s, bx, 12, 14, 24, g(40), 1)
        fill(s, bx, 12, 14, 3, g(240))
    # Faulds
    for i in range(24):
        ww = 22 - i//2
        v = max(40, 150-i*4)
        fill(s, m-ww, 62+i, ww*2, 2, g(v))

def _itm_elven_cloak(s):
    m = 48
    # Flowing asymmetric cape — thin and elegant
    poly(s, [(m,10),(m+22,14),(m+26,70),(m+8,84),(m-8,84),(m-26,70),(m-22,14)],
         g(175))
    poly(s, [(m-22,14),(m,10),(m+22,14),(m+26,70),(m+8,84),(m-8,84),(m-26,70)],
         g(175))
    # Dark outer edge
    pygame.draw.polygon(s, g(50),
        [(px(m),px(10)),(px(m+22),px(14)),(px(m+26),px(70)),
         (px(m+8),px(84)),(px(m-8),px(84)),(px(m-26),px(70)),(px(m-22),px(14))], pw(2))
    # Elegant vertical fold lines
    line(s, m,   12, m,   82, g(120), 1)
    line(s, m+10, 16, m+12, 78, g(140), 1)
    line(s, m-10, 16, m-12, 78, g(140), 1)
    # Clasp at top
    grad_circle(s, m, 14, 6, 230, 160)
    circle(s, m, 14, 6, g(40), 1)
    fill(s, m-2, 12, 4, 4, g(255))

def _itm_shield(s):
    m = 48
    # Classic kite shield — wide rounded top, pointed base
    poly(s, [(m,82),(m-24,20),(m-22,10),(m+22,10),(m+24,20)], g(160))
    poly(s, [(m,82),(m-24,20),(m-22,10),(m+22,10),(m+24,20)], g(160))
    # Gradient fill
    pygame.draw.polygon(s, g(180),
        [(px(m),px(82)),(px(m-24),px(20)),(px(m-22),px(10)),
         (px(m+22),px(10)),(px(m+24),px(20))])
    # Boss (central boss)
    grad_circle(s, m, m, 10, 230, 160)
    circle(s, m, m, 10, g(50), 1)
    # Cross decoration
    line(s, m, 14, m, 80, g(60), 2)
    line(s, m-22, m, m+22, m, g(60), 2)
    # Border
    pygame.draw.polygon(s, g(40),
        [(px(m),px(82)),(px(m-24),px(20)),(px(m-22),px(10)),
         (px(m+22),px(10)),(px(m+24),px(20))], pw(2))

def _itm_helmet(s):
    m = 48
    # Dome helmet viewed from the front
    # Main dome — big round top
    grad_circle(s, m, 38, 28, 230, 155)
    # Dome outline
    pygame.draw.arc(s, g(40), (px(m-28),px(10),pw(56),pw(56)), 0, math.pi, pw(2))
    # Brim
    fill(s, m-32, 54, 64, 8, g(170))
    outline(s, m-32, 54, 64, 8, g(40), 1)
    fill(s, m-30, 54, 60, 2, g(220))
    # Visor slit
    fill(s, m-18, 40, 36, 6, g(40))
    fill(s, m-16, 41, 32, 2, g(90))
    # Nose guard
    fill(s, m-2, 40, 4, 18, g(60))
    fill(s, m-1, 40, 2, 16, g(120))
    # Top ridge catch-light
    fill(s, m-2, 12, 4, 28, g(255))

def _itm_gloves(s):
    m = 48
    # Two gauntlets side by side — left and right
    for ox, flip in ((-14, 0), (14, 1)):
        cx = m + ox
        # Cuff
        fill(s, cx-8, 54, 16, 16, g(175))
        outline(s, cx-8, 54, 16, 16, g(50), 1)
        fill(s, cx-8, 54, 16, 3, g(220))
        # Palm
        grad_v(s, cx-7, 36, 14, 18, 200, 160)
        outline(s, cx-7, 36, 14, 18, g(50), 1)
        # Four fingers: packed squares
        for fi in range(4):
            fx = cx - 7 + fi*4 - (1 if flip else 0)
            grad_v(s, fx, 16, 3, 20, 210, 170)
            outline(s, fx, 16, 3, 20, g(60), 1)
        # Thumb (side)
        tx = cx + (9 if not flip else -9)
        grad_v(s, tx, 40, 6, 12, 200, 160)
        outline(s, tx, 40, 6, 12, g(60), 1)
        # Knuckle lines
        for ky in (32, 36, 40):
            fill(s, cx-6, ky, 12, 1, g(90))

# ── Potion sprites (subtle shape variation per type) ──────────────────────────

def _itm_potion_base(s, neck_h=16, body_r=22, fill_v=155, glass_v=75):
    """Round-bottomed flask — neck top-centre, spherical body below."""
    m = 48
    neck_x = m - 5
    neck_y = 12
    # Neck
    fill(s, neck_x, neck_y, 10, neck_h, g(100))
    fill(s, neck_x, neck_y, 10, 2, g(170))   # cork/stopper tint
    # Liquid body
    body_cy = neck_y + neck_h + body_r - 4
    grad_circle(s, m, body_cy, body_r, fill_v, glass_v)
    outline(s, m-body_r, body_cy-body_r, body_r*2, body_r*2, g(30), 2)
    # Collar between neck and body
    fill(s, neck_x-3, neck_y+neck_h-2, 16, 5, g(70))
    fill(s, neck_x-2, neck_y+neck_h, 14, 2, g(130))
    # Glint
    fill(s, m-body_r+4, body_cy-body_r+4, 8, 6, g(220))
    fill(s, m-body_r+4, body_cy-body_r+4, 4, 3, g(255))

def _itm_potion_tall(s, fill_v=155, glass_v=75):
    """Tall thin flask — for special potions."""
    m = 48
    fill(s, m-5, 10, 10, 22, g(100))   # neck
    fill(s, m-5, 10,  10, 2, g(170))
    fill(s, m-8, 32,  16, 42, g(fill_v))
    outline(s, m-8, 32, 16, 42, g(30), 2)
    fill(s, m-8, 32, 16, 3, g(glass_v+40))
    fill(s, m-8, 70, 16, 4, g(glass_v-20))
    fill(s, m-5, 74,  10, 3, g(glass_v))   # rounded bottom
    fill(s, m-10,35, 6, 8, g(220))   # glint

# ── Scroll sprite ──────────────────────────────────────────────────────────────

def _itm_scroll_base(s):
    """Rolled parchment cylinder — end-caps visible."""
    m = 48
    # Main body rect
    grad_v(s, m-22, 22, 44, 50, 210, 170)
    outline(s, m-22, 22, 44, 50, g(40), 2)
    # End-cap ellipses (top and bottom)
    for cy in (22, 72):
        pygame.draw.ellipse(s, g(190), (px(m-22), px(cy-6), pw(44), pw(10)))
        pygame.draw.ellipse(s, g(40),  (px(m-22), px(cy-6), pw(44), pw(10)), pw(1))
    # Text lines
    for ly in range(32, 66, 7):
        fill(s, m-16, ly, 32, 2, g(55))
    # Red wax seal (small circle on front)
    grad_circle(s, m+8, m+2, 5, 80, 40)
    circle(s, m+8, m+2, 5, g(30), 1)

# ── Wand sprite ────────────────────────────────────────────────────────────────

def _itm_wand_base(s, tip_bright=True):
    """Thin diagonal rod with sparkle at tip (lower-left handle, upper-right tip)."""
    # Rod body
    for i in range(8, 82):
        v = 60 + (i-8)*60//74
        line(s, i, 90-i, i+2, 90-i, g(v), 3)
    # Handle knob
    grad_circle(s, 14, 82, 8, 190, 110)
    circle(s, 14, 82, 8, g(40), 1)
    if tip_bright:
        # Sparkle at tip
        for ang in range(0, 360, 45):
            rx = int(82+10*math.cos(math.radians(ang)))
            ry = int(14+10*math.sin(math.radians(ang)))
            if 0<=rx<96 and 0<=ry<96:
                circle(s, rx, ry, 2, g(230))
        grad_circle(s, 82, 14, 5, 255, 180)
    else:
        circle(s, 82, 14, 4, g(80))

# ── Ring sprite ────────────────────────────────────────────────────────────────

def _itm_ring_base(s, gem_v=220):
    """Bold band ring with gem at top."""
    m = 48
    # Band: thick circle with gradient
    pygame.draw.circle(s, g(60),  (px(m),px(m)), pw(28), pw(6))
    pygame.draw.circle(s, g(160), (px(m),px(m)), pw(28), pw(4))
    pygame.draw.circle(s, g(220), (px(m),px(m)), pw(28), pw(2))
    # Gem setting (top of ring)
    grad_circle(s, m, m-26, 7, gem_v, max(50, gem_v-120))
    circle(s, m, m-26, 7, g(30), 1)
    fill(s, m-3, m-30, 6, 5, g(min(255, gem_v+20)))

# ── Food sprites ───────────────────────────────────────────────────────────────

def _itm_food_ration(s, crack=False):
    """Drumstick / meat bone."""
    m = 48
    # Knuckle at top
    grad_circle(s, m, 24, 16, 200, 130)
    circle(s, m, 24, 16, g(50), 1)
    fill(s, m-8, 18, 12, 8, g(230))
    # Shank tapering down
    for i in range(32):
        ww = max(2, 9 - i//4)
        v  = max(80, 160-i*2)
        fill(s, m-ww, 40+i, ww*2, 2, g(v))
    # Bone tip
    grad_circle(s, m, 76, 5, 210, 160)
    if crack:
        # Rotten: cracks and darker
        line(s, m-4, 22, m+2, 30, g(40), 2)
        line(s, m+2, 30, m-2, 36, g(40), 1)
        fill(s, m-10, 26, 6, 4, g(90))

def _itm_fruit(s):
    m = 48
    # Round apple/fruit shape
    grad_circle(s, m, m+4, 26, 200, 130)
    circle(s, m, m+4, 26, g(50), 1)
    # Stem
    fill(s, m-1, 16, 3, 10, g(60))
    # Leaf
    poly(s, [(m+1,18),(m+14,14),(m+10,22)], g(100))
    # Specular
    fill(s, m-12, m-6, 10, 8, g(240))

def _itm_spider(s):
    m = 48
    # Small spider — oval body with 8 legs
    # Body segments
    grad_circle(s, m+4, m+4, 9, 80, 40)
    grad_circle(s, m-4, m-4, 12, 90, 50)
    circle(s, m-4, m-4, 12, g(25), 1)
    # Eyes
    circle(s, m-8, m-8, 2, g(220))
    circle(s, m-4, m-9, 2, g(220))
    # Legs (4 per side, bent)
    for i, (lx, ly, tx, ty) in enumerate([
        (m-14, m-2,  m-24, m-14),  # L1
        (m-14, m+2,  m-26, m+4),   # L2
        (m-12, m+8,  m-22, m+18),  # L3
        (m-8,  m+12, m-14, m+24),  # L4
        (m+4,  m-2,  m+16, m-14),  # R1
        (m+4,  m+4,  m+18, m+4),   # R2
        (m+4,  m+10, m+16, m+20),  # R3
        (m+2,  m+14, m+10, m+24),  # R4
    ]):
        pygame.draw.line(s, g(55), (px(m-4),px(m-4)),(px(lx),px(ly)), pw(2))
        pygame.draw.line(s, g(55), (px(lx),px(ly)),  (px(tx),px(ty)), pw(2))

def _itm_lizard(s):
    m = 48
    # Side-view lizard
    # Body
    poly(s, [(m-24,m+6),(m-4,m-10),(m+18,m-6),(m+26,m+6),(m+16,m+16),(m-14,m+16)], g(120))
    pygame.draw.polygon(s, g(50), [(px(m-24),px(m+6)),(px(m-4),px(m-10)),
        (px(m+18),px(m-6)),(px(m+26),px(m+6)),(px(m+16),px(m+16)),(px(m-14),px(m+16))], pw(1))
    # Head
    poly(s, [(m-28,m+4),(m-20,m-8),(m-8,m-6),(m-4,m+4)], g(140))
    # Eye
    circle(s, m-18, m-2, 3, g(30))
    circle(s, m-18, m-2, 1, g(200))
    # Tail
    pts = [(m+26,m+6),(m+34,m+2),(m+40,m+8),(m+44,m+4)]
    for i in range(len(pts)-1):
        pygame.draw.line(s, g(100), (px(pts[i][0]),px(pts[i][1])),
                         (px(pts[i+1][0]),px(pts[i+1][1])), pw(3))
    # Legs
    for lx,ly in ((m-8,m+16),(m+10,m+16)):
        pygame.draw.line(s, g(90),(px(lx),px(ly)),(px(lx-4),px(ly+10)), pw(2))
        pygame.draw.line(s, g(90),(px(lx),px(ly)),(px(lx+4),px(ly+10)), pw(2))

# ── Gem sprites ────────────────────────────────────────────────────────────────

def _itm_diamond(s):
    m = 48
    # Classic 4-point diamond ◇ with internal facets
    pts = [(m, 10), (m+30, m), (m, m+30), (m-30, m)]
    poly(s, pts, g(220))
    # Facet shading — four triangles
    for (x1,y1),(x2,y2),v in [
        (pts[0],pts[1], 240), (pts[1],pts[2], 160),
        (pts[2],pts[3], 180), (pts[3],pts[0], 250),
    ]:
        pygame.draw.polygon(s, g(v), [(px(m),px(m)),(px(x1),px(y1)),(px(x2),px(y2))])
    # Internal facet cross lines
    line(s, m, 10, m+30, m, g(80), 1)
    line(s, m+30, m, m, m+30, g(80), 1)
    line(s, m, m+30, m-30, m, g(80), 1)
    line(s, m-30, m, m, 10, g(80), 1)
    line(s, m, 10, m, m+30, g(130), 1)
    line(s, m-30, m, m+30, m, g(130), 1)
    # Outline
    pygame.draw.polygon(s, g(40), [(px(m),px(10)),(px(m+30),px(m)),
        (px(m),px(m+30)),(px(m-30),px(m))], pw(2))
    # Top glint
    fill(s, m-3, 12, 6, 5, g(255))

def _itm_ruby(s):
    m = 48
    # Rounded brilliant-cut gem
    pts = [(m,8),(m+24,18),(m+28,m),(m+20,m+28),(m,m+34),(m-20,m+28),(m-28,m),(m-24,18)]
    poly(s, pts, g(160))
    for i,((x1,y1),(x2,y2)) in enumerate(zip(pts, pts[1:]+pts[:1])):
        v = min(240, 90 + i*22)
        pygame.draw.polygon(s, g(v), [(px(m),px(m)),(px(x1),px(y1)),(px(x2),px(y2))])
    pygame.draw.polygon(s, g(40), [(px(x),px(y)) for x,y in pts], pw(2))
    # Table facet (centre top)
    pygame.draw.ellipse(s, g(220), (px(m-10),px(m-10),pw(20),pw(14)))
    fill(s, m-6, m-9, 12, 6, g(240))

def _itm_emerald(s):
    m = 48
    # Square-cut (emerald cut) gem
    pts = [(m-14,8),(m+14,8),(m+26,20),(m+26,m+16),(m+14,m+30),
           (m-14,m+30),(m-26,m+16),(m-26,20)]
    poly(s, pts, g(150))
    for i,((x1,y1),(x2,y2)) in enumerate(zip(pts, pts[1:]+pts[:1])):
        v = min(230, 80 + i*20)
        pygame.draw.polygon(s, g(v), [(px(m),px(m)),(px(x1),px(y1)),(px(x2),px(y2))])
    pygame.draw.polygon(s, g(40), [(px(x),px(y)) for x,y in pts], pw(2))
    # Step facets
    for off in (6, 12):
        pygame.draw.rect(s, g(80), (px(m-14+off),px(8+off),pw(28-off*2),pw(22+off*2+2)), pw(1))
    fill(s, m-8, 12, 16, 10, g(240))

# ── Orb sprites ────────────────────────────────────────────────────────────────

def _itm_orb_of_carnos(s):
    m = 48
    # Dark mystic orb with inner glow
    grad_circle(s, m, m, 32, 80, 20)
    circle(s, m, m, 32, g(30), 2)
    # Inner swirling glow
    for r in (22, 16, 10, 6):
        grad_circle(s, m, m, r, 200-r*3, 60-r)
    # Orbiting sparks
    for ang in range(0, 360, 45):
        rx = int(m + 24*math.cos(math.radians(ang)))
        ry = int(m + 24*math.sin(math.radians(ang)))
        if 0<=rx<96 and 0<=ry<96:
            circle(s, rx, ry, 2, g(220))
    fill(s, m-4, m-10, 8, 6, g(250))

def _itm_plastic_orb(s):
    m = 48
    # Plain bright plastic sphere
    grad_circle(s, m, m, 30, 240, 160)
    circle(s, m, m, 30, g(60), 2)
    # Simple specular highlight
    fill(s, m-12, m-18, 14, 10, g(255))
    fill(s, m-10, m-16, 10,  7, g(255))
    # Equator ring
    pygame.draw.ellipse(s, g(100), (px(m-30),px(m-6),pw(60),pw(12)), pw(1))


# ── Master dispatcher ──────────────────────────────────────────────────────────

def sprite_item_by_id(item_id: str, glyph: str, color: tuple) -> pygame.Surface:
    """Return a unique sprite for the given item_id.
    Falls back to glyph-based sprite_item() for uncatalogued IDs."""
    s = _canvas(alpha=True)
    m = 48

    # Single unbroken if/elif/else chain — ordered by category
    # ── WEAPONS ───────────────────────────────────────────────────────────────
    if   item_id == "long_sword":        _itm_long_sword(s)
    elif item_id == "two_handed_sword":  _itm_two_handed_sword(s)
    elif item_id == "dagger":            _itm_dagger(s)
    elif item_id == "leather_whip":      _itm_leather_whip(s)
    elif item_id == "mace":              _itm_mace(s)
    elif item_id == "death_blade":       _itm_death_blade(s)
    elif item_id == "sling":             _itm_sling(s)
    elif item_id == "small_rock":        _itm_small_rock(s)
    elif item_id == "large_rock":        _itm_large_rock(s)
    elif item_id == "dart":              _itm_dart(s)
    elif item_id == "spear":             _itm_spear(s)
    elif item_id == "mac_plus":          _itm_mac_plus(s)
    # ── ARMOR ─────────────────────────────────────────────────────────────────
    elif item_id == "leather_armor":     _itm_leather_armor(s)
    elif item_id == "chain_armor":       _itm_chain_armor(s)
    elif item_id == "banded_armor":      _itm_banded_armor(s)
    elif item_id == "plate_armor":       _itm_plate_armor(s)
    elif item_id == "elven_cloak":       _itm_elven_cloak(s)
    elif item_id == "shield":            _itm_shield(s)
    elif item_id == "helmet":            _itm_helmet(s)
    elif item_id == "gloves":            _itm_gloves(s)
    # ── POTIONS ───────────────────────────────────────────────────────────────
    elif item_id in ("potion_healing", "potion_extra_healing", "potion_life"):
        _itm_potion_base(s, fill_v=180, glass_v=90)
    elif item_id in ("potion_poison", "potion_blindness", "potion_confusion"):
        _itm_potion_base(s, fill_v=80, glass_v=40)
    elif item_id in ("potion_speed", "potion_haste",
                     "potion_levitation", "potion_invisibility"):
        _itm_potion_tall(s, fill_v=170, glass_v=90)
    elif item_id in ("potion_strength", "potion_muscle"):
        _itm_potion_base(s, neck_h=12, body_r=26, fill_v=140, glass_v=70)
    elif glyph == '!':                   # all remaining potions
        _itm_potion_base(s)
    # ── SCROLLS ───────────────────────────────────────────────────────────────
    elif glyph == '?':
        _itm_scroll_base(s)
    # ── WANDS ─────────────────────────────────────────────────────────────────
    elif glyph == '\\':
        _itm_wand_base(s)
    # ── RINGS ─────────────────────────────────────────────────────────────────
    elif item_id == "ring_resist_fire":  _itm_ring_base(s, gem_v=200)
    elif item_id == "ring_resist_cold":  _itm_ring_base(s, gem_v=180)
    elif item_id == "ring_regeneration": _itm_ring_base(s, gem_v=240)
    elif item_id in ("ring_slowness", "ring_hunger"):
        _itm_ring_base(s, gem_v=90)
    elif glyph == '=':                   # all remaining rings
        _itm_ring_base(s)
    # ── FOOD ──────────────────────────────────────────────────────────────────
    elif item_id == "food_rotten":       _itm_food_ration(s, crack=True)
    elif item_id in ("food_bland", "food_good"): _itm_food_ration(s)
    elif item_id == "fruit":             _itm_fruit(s)
    elif item_id == "spider":            _itm_spider(s)
    elif item_id == "lizard":            _itm_lizard(s)
    # ── JEWELS ────────────────────────────────────────────────────────────────
    elif item_id == "diamond":           _itm_diamond(s)
    elif item_id == "ruby":              _itm_ruby(s)
    elif item_id == "emerald":           _itm_emerald(s)
    # ── MISC ──────────────────────────────────────────────────────────────────
    elif item_id == "orb_of_carnos":     _itm_orb_of_carnos(s)
    elif item_id == "plastic_orb":       _itm_plastic_orb(s)
    else:
        return sprite_item(glyph, color)   # unknown — glyph fallback

    return _down(s)


def sprite_item(glyph: str, color: tuple) -> pygame.Surface:
    """Glyph-based fallback sprite (kept for compatibility)."""
    s = _canvas(alpha=True)
    m = 48

    if glyph == '/':   # Weapon fallback — generic sword
        _blade(s, 74, 12, 32, 62, thick=5)
        _guard(s, 26, 54, 46, 72, thick=4)
        _grip( s, 34, 64, 24, 76, thick=4)
        _pommel(s, 20, 81, r=5)
    elif glyph == ']':
        _itm_leather_armor(s)
    elif glyph == '!':
        _itm_potion_base(s)
    elif glyph == '?':
        _itm_scroll_base(s)
    elif glyph == '=':
        _itm_ring_base(s)
    elif glyph == '\\':
        _itm_wand_base(s)
    elif glyph == '%':
        _itm_food_ration(s)
    elif glyph == '*':
        _itm_diamond(s)
    else:
        outline(s, 16, 16, 64, 64, g(80), 3)
        outline(s, 22, 22, 52, 52, g(50), 2)
        circle(s, m, m, 12, g(90))

    return _down(s)


# ══════════════════════════════════════════════════════════════════════════════
#  CACHE
# ══════════════════════════════════════════════════════════════════════════════

_CACHE: dict = {}

def _load_player_sprite(class_key: str) -> pygame.Surface:
    """
    Load the PNG sprite for the given class key (96×96 RGBA).
    Sprite IDs: knight=300, fighter=301, sage=302, wizard=303,
                alchemist=304, jeweler=305, jones=306.
    Falls back to the procedural sprite_player() if the file is missing or corrupt.
    """
    import os
    CLASS_SPRITE_ID = {
        "knight":    300,
        "fighter":   301,
        "sage":      302,
        "wizard":    303,
        "alchemist": 304,
        "jeweler":   305,
        "jones":     306,
    }
    sprite_id = CLASS_SPRITE_ID.get(class_key, 300)
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites",
                        f"{sprite_id}.png")
    path = os.path.normpath(path)
    if os.path.isfile(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_size() != (T, T):
                img = pygame.transform.smoothscale(img, (T, T))
            return img
        except Exception:
            pass   # corrupt file — fall through to procedural
    return sprite_player()

#Monsters
import os, sys
# Fix: Ensure the data/ directory is visible to the UI subfolder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.monsters import get_monster, MONSTERS

# ... (Keep your existing g, ga, _canvas, _down, px, pw functions) ...

def sprite_monster(glyph: str, color: tuple) -> pygame.Surface:
    """Procedural fallback for monsters (Mac-style silhouette)."""
    s = _canvas(alpha=True)
    # Draw a stylized circular base using the monster's color_hint
    pygame.draw.circle(s, color, (TS//2, TS//2 + px(4)), px(14))
    # Draw a dark outline
    pygame.draw.circle(s, g(0), (TS//2, TS//2 + px(4)), px(14), pw(2))
    return _down(s)

def get_monster_sprite(monster_id: str) -> pygame.Surface:
    """
    Loads monster sprite from assets/sprites/[icon_id].png.
    Same mechanism as get_player_sprite.
    """
    try:
        m_data = get_monster(monster_id)
        sprite_id = m_data["icon_id"] # e.g. 400, 401...
        glyph = m_data["glyph"]
        color = m_data["color_hint"]
    except KeyError:
        return sprite_monster("?", (127, 127, 127))

    # Assets are in ../assets/sprites/ named by the icon_id
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", f"{sprite_id}.png")
    path = os.path.normpath(path)

    if os.path.isfile(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_size() != (T, T):
                # 1. Calculate the new size while keeping aspect ratio
                w, h = img.get_size()
                aspect = w / h
            
                if w > h:
                    new_w = T
                    new_h = int(T / aspect)
                else:
                    new_h = T
                    new_w = int(T * aspect)
            
                # 2. Scale the original image to fit (without stretching)
                scaled_img = pygame.transform.smoothscale(img, (new_w, new_h))
              
                # 3. Create a transparent 96x96 canvas and center the monster on it
                centered_surf = pygame.Surface((T, T), pygame.SRCALPHA)
                offset_x = (T - new_w) // 2
                offset_y = (T - new_h) // 2
                centered_surf.blit(scaled_img, (offset_x, offset_y))
            
                img = centered_surf
            return img
        except Exception:
            pass 
            
    return sprite_monster(glyph, color)

# ── Item sprite ID table ──────────────────────────────────────────────────────
# Maps every item_id to a PNG icon number in assets/sprites/.
# IDs 500–511 : weapons (one unique sprite each, including throwables)
# IDs 512–519 : armor pieces (one unique sprite each)
# ID  520     : all potions   (shared)
# ID  521     : all scrolls   (shared)
# ID  522     : all rings     (shared)
# ID  523     : all wands     (shared)
# ID  524     : all gems/jewels (shared)
# ID  525     : all food      (shared)
# IDs 526–527 : misc unique items

ITEM_SPRITE_ID: dict = {
    # ── Weapons — unique per item (500–511) ───────────────────────────────────
    "dagger":            500,
    "leather_whip":      501,
    "long_sword":        502,
    "mace":              503,
    "two_handed_sword":  504,
    "death_blade":       505,
    "sling":             506,
    "small_rock":        507,
    "large_rock":        508,
    "dart":              509,
    "spear":             510,
    "mac_plus":          511,
    # ── Armor — unique per item (512–519) ─────────────────────────────────────
    "leather_armor":     512,
    "chain_armor":       513,
    "banded_armor":      514,
    "plate_armor":       515,
    "elven_cloak":       516,
    "shield":            517,
    "helmet":            518,
    "gloves":            519,
    # ── Potions — all share icon 520 ──────────────────────────────────────────
    "potion_confusion":      520,
    "potion_extra_healing":  520,
    "potion_resist_fire":    520,
    "potion_healing":        520,
    "potion_invisibility":   520,
    "potion_levitation":     520,
    "potion_poison":         520,
    "potion_speed":          520,
    "potion_muscle":         520,
    "potion_resist_cold":    520,
    "potion_dexterity":      520,
    "potion_constitution":   520,
    "potion_charisma":       520,
    "potion_blindness":      520,
    "potion_worthless":      520,
    "potion_strength":       520,
    "potion_life":           520,
    # ── Scrolls — all share icon 521 ──────────────────────────────────────────
    "scroll_gain_level":     521,
    "scroll_identify":       521,
    "scroll_enchant_armor":  521,
    "scroll_magic_mapping":  521,
    "scroll_teleport":       521,
    "scroll_enchant_weapon": 521,
    "scroll_protection":     521,
    "scroll_wishing":        521,
    "scroll_intelligence":   521,
    "scroll_wisdom":         521,
    "scroll_remove_curse":   521,
    "scroll_amnesia":        521,
    "scroll_joke":           521,
    "scroll_words":          521,
    "scroll_scare":          521,
    "scroll_charm":          521,
    # ── Rings — all share icon 522 ────────────────────────────────────────────
    "ring_resist_fire":      522,
    "ring_resist_cold":      522,
    "ring_regeneration":     522,
    "ring_slowness":         522,
    "ring_hunger":           522,
    "ring_xray":             522,
    "ring_monster":          522,
    # ── Wands — all share icon 523 ────────────────────────────────────────────
    "wand_lightning":        523,
    "wand_fire":             523,
    "wand_ice":              523,
    "wand_death":            523,
    "wand_striking":         523,
    "wand_fear":             523,
    "wand_digging":          523,
    "wand_sleep":            523,
    "wand_polymorph":        523,
    "wand_teleport":         523,
    "wand_invisibility":     523,
    # ── Gems / jewels — all share icon 524 ───────────────────────────────────
    "diamond":               524,
    "ruby":                  524,
    "emerald":               524,
    # ── Food — all share icon 525 ─────────────────────────────────────────────
    "food_rotten":           525,
    "food_bland":            525,
    "food_good":             525,
    "fruit":                 525,
    "spider":                525,
    "lizard":                525,
    # ── Misc unique items ─────────────────────────────────────────────────────
    "orb_of_carnos":         526,
    "plastic_orb":           527,
}


def _load_item_sprite(item_id: str) -> pygame.Surface:
    """
    Load item sprite from assets/sprites/[icon_id].png.
    Priority:
      1. PNG file at assets/sprites/{icon_id}.png — proportional scale +
         centred on transparent 96×96 canvas if not already 96×96.
      2. Procedural fallback via sprite_item_by_id() using the item's
         glyph and color from items.py.
    Returns a 96×96 RGBA Surface in all cases.
    """
    from data.items import ITEMS, get_item

    icon_id = ITEM_SPRITE_ID.get(item_id)

    if icon_id is not None:
        path = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites",
                            f"{icon_id}.png")
        path = os.path.normpath(path)
        if os.path.isfile(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                if img.get_size() != (T, T):
                    w, h = img.get_size()
                    if w >= h:
                        new_w, new_h = T, max(1, int(T * h / w))
                    else:
                        new_h, new_w = T, max(1, int(T * w / h))
                    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                    canvas = pygame.Surface((T, T), pygame.SRCALPHA)
                    canvas.blit(scaled, ((T - new_w) // 2, (T - new_h) // 2))
                    img = canvas
                return img
            except Exception:
                pass   # corrupt PNG — fall through to procedural

    # Procedural fallback — use existing per-item drawing code
    try:
        idata = get_item(item_id)
        glyph = idata.get("glyph", "?")
        color = idata.get("color_hint", (180, 180, 180))
        return sprite_item_by_id(item_id, glyph, color)
    except KeyError:
        return sprite_item("?", (180, 180, 180))


# ── Tile sprite icon IDs ──────────────────────────────────────────────────────
# Drop a 96×96 px PNG into assets/sprites/ to replace any procedural tile.
# All tiles must be exactly 96×96 px (the game's TILE constant).
# If an image is a different size it will be scaled to fit; transparency is
# preserved for RGBA images.
#
#  ID  | Cache key(s)                  | Tile shown when
# -----|-------------------------------|----------------------------------
#  550 | stair_up                      | Staircase going up (T_STAIR_UP)
#  551 | stair_down                    | Staircase going down (T_STAIR_DOWN)
#  560 | wall_lit, wall_dim*           | Stone wall tile (T_WALL)
#  561 | floor_light_lit, _dim*        | Floor tile — checkerboard light square
#  562 | floor_grey_lit,  _dim*        | Floor tile — checkerboard grey square
#  563 | boulder                       | Pushable boulder (T_BOULDER)
#
# * _dim variants (explored but not currently visible) are derived automatically
#   by darkening the lit PNG at 55% brightness — no separate file needed.
#
STAIR_UP_SPRITE_ID     = 550
STAIR_DOWN_SPRITE_ID   = 551
WALL_SPRITE_ID         = 560
FLOOR_LIGHT_SPRITE_ID  = 561
FLOOR_GREY_SPRITE_ID   = 562
BOULDER_SPRITE_ID      = 563


def _load_tile_sprite(icon_id: int, fallback_fn,
                      dim: bool = False, dim_factor: float = 0.55) -> pygame.Surface:
    """
    Load a dungeon tile from assets/sprites/{icon_id}.png.

    If `dim` is True, return a darkened copy for the explored-but-not-visible
    (dim) variant: multiply every pixel's RGB by `dim_factor`, preserving alpha.

    Falls back to `fallback_fn()` if the PNG is absent or corrupt.
    All images are scaled to exactly 96×96 px.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "assets", "sprites",
                        f"{icon_id}.png")
    path = os.path.normpath(path)
    if os.path.isfile(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_size() != (T, T):
                img = pygame.transform.smoothscale(img, (T, T))
            if dim:
                # Darken via pygame.transform.threshold-free approach:
                # blit a semi-transparent black overlay onto a copy
                dim_surf = img.copy()
                veil = pygame.Surface((T, T), pygame.SRCALPHA)
                alpha = int(255 * (1.0 - dim_factor))
                veil.fill((0, 0, 0, alpha))
                dim_surf.blit(veil, (0, 0))
                return dim_surf
            return img
        except Exception:
            pass
    return fallback_fn()


def build_cache():
    global _CACHE
    void = pygame.Surface((T, T))
    void.fill(g(0))
    _CACHE = {
        # ── Walls ─────────────────────────────────────────────────────────────
        "wall_lit":  _load_tile_sprite(WALL_SPRITE_ID, lambda: tile_wall(lit=True)),
        "wall_dim":  _load_tile_sprite(WALL_SPRITE_ID, lambda: tile_wall(lit=False),
                                       dim=True),
        # ── Floor — checkerboard light squares ────────────────────────────────
        "floor_light_lit": _load_tile_sprite(FLOOR_LIGHT_SPRITE_ID,
                                             lambda: tile_floor_light(lit=True)),
        "floor_light_dim": _load_tile_sprite(FLOOR_LIGHT_SPRITE_ID,
                                             lambda: tile_floor_light(lit=False),
                                             dim=True),
        # ── Floor — checkerboard grey squares ─────────────────────────────────
        "floor_grey_lit":  _load_tile_sprite(FLOOR_GREY_SPRITE_ID,
                                             lambda: tile_floor_grey(lit=True)),
        "floor_grey_dim":  _load_tile_sprite(FLOOR_GREY_SPRITE_ID,
                                             lambda: tile_floor_grey(lit=False),
                                             dim=True),
        # ── Stairs ────────────────────────────────────────────────────────────
        "stair_up":   _load_tile_sprite(STAIR_UP_SPRITE_ID,   tile_stair_up),
        "stair_down": _load_tile_sprite(STAIR_DOWN_SPRITE_ID, tile_stair_down),
        # ── Boulder ───────────────────────────────────────────────────────────
        "boulder":    _load_tile_sprite(BOULDER_SPRITE_ID, tile_boulder),
        # ── Void ──────────────────────────────────────────────────────────────
        "void":       void,
    }
    # Player sprites — one per class
    for class_key in ("knight", "fighter", "sage", "wizard", "alchemist", "jeweler", "jones"):
        _CACHE[f"player_{class_key}"] = _load_player_sprite(class_key)

    # Monster sprites — one per monster id (42 total)
    for m in MONSTERS:
        _CACHE[f"monster_{m['id']}"] = get_monster_sprite(m['id'])

    # Item sprites — one per item id (82 total); shared-category items resolve
    # to the same underlying PNG but each gets its own cache entry so the
    # renderer can always do a simple sprites.get("itm_{item.id}") lookup.
    from data.items import ITEMS
    for item in ITEMS:
        _CACHE[f"itm_{item['id']}"] = _load_item_sprite(item['id'])

    print(f"Sprite cache built: {len(_CACHE)} entries "
          f"({len(MONSTERS)} monsters, {len(ITEMS)} items, 7 classes, tiles).")

def get(key: str) -> pygame.Surface:
    return _CACHE.get(key, _CACHE["void"])
