VERSION = "0.410.20260325"

# constants.py — 1392×896 window (864 dungeon + 528 stats panel)

# ── Display ───────────────────────────────────────────────────────────────────
TILE       = 96          # pixels per tile — large, icon-sized sprites
VIEW_TILES = 9           # viewport is always 9×9 tiles (player centred)
VIEW_HALF  = VIEW_TILES // 2   # 4  (tiles visible each side of player)
VP_PX      = VIEW_TILES * TILE # 864 (viewport pixel size, square)

STATS_W    = 528         # right panel width (half of previous 1056)
MENU_H     = 32          # Mac menu bar
SCREEN_W   = VP_PX + STATS_W  # 1392
SCREEN_H   = MENU_H + VP_PX   # 896 — no dead strip below panels
MSG_H      = 0           # message strip removed; info lives in right panel

# UI rects (x, y, w, h)
RECT_MENU  = (0,       0,      SCREEN_W, MENU_H)
RECT_MAP   = (0,       MENU_H, VP_PX,    VP_PX)
RECT_MSG   = (0,       MENU_H, 1,        1)      # stub — not used for display
RECT_STATS = (VP_PX,   MENU_H, STATS_W,  VP_PX)  # equal height to left panel

FPS        = 60

# ── Map ───────────────────────────────────────────────────────────────────────
MAP_COLS   = 60
MAP_ROWS   = 60
TOTAL_FLOORS = 40

# ── Tile types ────────────────────────────────────────────────────────────────
T_FLOOR      = 0
T_WALL       = 1
T_STAIR_UP   = 2
T_STAIR_DOWN = 3
T_BOULDER    = 4    # wall partially destroyed by wand of Digging

# Legacy aliases so old code doesn't break
T_VOID     = T_WALL
T_CORRIDOR = T_FLOOR
T_DOOR_C   = T_FLOOR
T_DOOR_O   = T_FLOOR

PASSABLE   = {T_FLOOR, T_STAIR_UP, T_STAIR_DOWN}
# T_BOULDER is NOT in PASSABLE — player must push (STR≥20) or destroy it

# ── Boulder mechanics ─────────────────────────────────────────────────────────
BOULDER_MIN_STR = 20   # minimum STR to push a boulder

# ── Dungeon generation ────────────────────────────────────────────────────────
WALL_DENSITY_SHALLOW = 0.05
WALL_DENSITY_DEEP    = 0.60
CA_PASSES_SHALLOW    = 2
CA_PASSES_DEEP       = 5
BORDER               = 1

# ── FOV ───────────────────────────────────────────────────────────────────────
# FOV is disabled for now — the 9×9 window IS the visibility
# Will be re-enabled in Step 7 as a polish feature
FOV_RADIUS_BASE = VIEW_HALF + 1   # just enough to cover the viewport

# ── Colours ───────────────────────────────────────────────────────────────────
C_BLACK     = (  0,   0,   0)
C_WHITE     = (255, 255, 255)

# Tile colours
C_WALL_LIT  = (  8,   8,   8)
C_WALL_DIM  = ( 28,  26,  24)
C_FLOOR_LIT  = (238, 232, 214)   # checkerboard light tile
C_FLOOR_DIM  = ( 55,  50,  44)   # explored-but-dark
C_FLOOR_GREY = (188, 183, 166)   # checkerboard grey tile (alternate)
C_FLOOR_GREY_DIM = ( 42,  38,  34)  # explored grey tile dim

# UI chrome
C_PANEL_BG  = ( 10,  10,  10)
C_PANEL_LINE= ( 55,  55,  55)

# Light-theme panel colours (stats panel, message log, char-create, playing UI)
C_LPANEL_BG    = (255, 255, 255)   # white panel background
C_LPANEL_LINE  = (180, 180, 180)   # subtle separator
C_LPANEL_BORD  = (  0,   0,   0)   # crisp black border
C_LTEXT        = ( 20,  20,  20)   # primary text
C_LTEXT_DIM    = ( 90,  90,  90)   # secondary / label text
C_LTEXT_BRIGHT = (  0,   0,   0)   # headings
C_LTEXT_ACCENT = ( 50,  50, 160)   # accent (links, highlights)
C_MENU_BG        = (255, 255, 255)   # Mac: white menu bar
C_MENU_TEXT      = (  0,   0,   0)   # black text
C_MENU_TEXT_DIM  = (160, 160, 160)   # greyed-out item text
C_MENU_SEP       = (180, 180, 180)   # separator line / bar bottom border
C_MENU_HIGHLIGHT = (  0,   0, 128)   # selected menu title (Mac blue highlight)
C_MENU_HI_TEXT   = (255, 255, 255)   # text on highlighted title
C_MENU_DROP_BG   = (255, 255, 255)   # dropdown background
C_MENU_DROP_BRD  = (  0,   0,   0)   # dropdown border

# Text
C_TEXT        = (228, 228, 228)
C_TEXT_DIM    = (120, 120, 120)
C_TEXT_BRIGHT = (255, 255, 255)

# Status bars
C_HP_FULL   = ( 50, 180,  50)
C_HP_MID    = (210, 160,  20)
C_HP_LOW    = (200,  40,  40)
C_FOOD_OK   = ( 50, 150, 200)
C_FOOD_LOW  = (200,  90,  30)
C_GOLD      = (210, 175,  45)
C_XP        = (110, 150, 220)

# Messages
C_MSG_NEW   = (248, 248, 248)
C_MSG_OLD   = (130, 130, 130)

# ── Player / stats ────────────────────────────────────────────────────────────
S_STR, S_INT, S_WIS, S_DEX, S_CON, S_CHA = 0, 1, 2, 3, 4, 5
STAT_NAMES = ["STR","INT","WIS","DEX","CON","CHA"]
STAT_FULL  = ["Strength","Intelligence","Wisdom","Dexterity","Constitution","Charisma"]
STAT_MAX   = 25
HP_PER_CON_POINT = 1
FOOD_MAX         = 1000
FOOD_STUFFED     = 950    # food >= this → player is stuffed (movement penalty)
FOOD_START       = 800
FOOD_PER_MOVE    = 1
FOOD_STARVE      = 0

# ── Real-time turn timer ──────────────────────────────────────────────────────
TURN_MS          = 5000   # milliseconds per turn (auto-Pass fires after this)

# ── Action costs (turns consumed) ─────────────────────────────────────────────
AP_MOVE     = 1   # move, attack, throw, wand, drink, equip, rest
AP_SCROLL   = 2   # read a scroll (takes concentration)
AP_EAT      = 4   # eat food (slow to chew)
AP_WISH     = 3   # make a wish
AP_PUSH_BOULDER = 4  # pushing a boulder — slow, effortful
XP_BASE          = 200  # was 10 — first level-up now requires real floor grinding
XP_GROWTH        = 2.0   # was 1.7 — slower level progression; ~1 XP level per dungeon level

# ── Items ─────────────────────────────────────────────────────────────────────
IC_WEAPON="weapon"; IC_ARMOR="armor"; IC_POTION="potion"; IC_SCROLL="scroll"
IC_RING="ring";     IC_WAND="wand";   IC_FOOD="food";    IC_JEWEL="jewel"
IC_MISC="misc"

# ── Monster Hostility ─────────────────────────────────────────────────────────
# Integer scale — lower = friendlier
HOSTILITY_AFRAID   = -1   # actively flees the player
HOSTILITY_NEUTRAL  =  0   # ignores player unless attacked
HOSTILITY_CAUTIOUS =  1   # only attacks if player is within 3 tiles or provoked
HOSTILITY_HOSTILE  =  2   # chases and attacks on sight (standard)

# CHA → hostility modifier (added to base hostility int; positive = more hostile)
def cha_hostility_mod(cha: int) -> int:
    if cha >= 22: return -1   # very charismatic — monsters are one step friendlier
    if cha >= 9:  return  0   # average — no effect
    return              1     # very low CHA — monsters are one step more hostile

# Colour hints for the hostility status dot drawn under monsters
HOSTILITY_DOT_COLOR = {
    HOSTILITY_AFRAID:   (255, 230,  50),   # yellow
    HOSTILITY_NEUTRAL:  ( 50, 200, 120),   # green
    HOSTILITY_CAUTIOUS: (220, 140,  30),   # orange
    HOSTILITY_HOSTILE:  (200,  40,  40),   # red (subtle — default)
}

# ── Difficulty ────────────────────────────────────────────────────────────────
DIFF_EXPLORER    = "explorer"    # HP regen ×2, hunger ×½, glory ×50%
DIFF_ADVENTURER  = "adventurer"  # Normal
DIFF_HERO        = "hero"        # No manual save; auto-save on quit; glory ×200%
DIFF_ARCHITECT   = "architect"   # Hidden/dev: name=="Architect"; no HoF; all items

DIFF_ORDER = [DIFF_EXPLORER, DIFF_ADVENTURER, DIFF_HERO]   # shown in UI (Architect hidden)

DIFF_LABEL = {
    DIFF_EXPLORER:   "Explorer",
    DIFF_ADVENTURER: "Adventurer",
    DIFF_HERO:       "Hero",
    DIFF_ARCHITECT:  "Architect",
}
DIFF_DESC = {
    DIFF_EXPLORER:   "HP regenerates faster. Hunger drains slower. Glory ×50%.",
    DIFF_ADVENTURER: "Standard difficulty. Normal rules apply.",
    DIFF_HERO:       "No manual save. Game auto-saves on quit. Glory ×200%.",
}
DIFF_GLORY_MULT = {
    DIFF_EXPLORER:   0.5,
    DIFF_ADVENTURER: 1.0,
    DIFF_HERO:       2.0,
    DIFF_ARCHITECT:  0.0,
}
# Glory bonus by class key (added after difficulty multiplier)
CLASS_GLORY_BONUS = {
    "sage":      0.20,
    "alchemist": 0.20,
    "wizard":    0.20,
    "jeweler":   0.20,
    "jones":     0.30,
}

# ── Combat ────────────────────────────────────────────────────────────────────
HIT_ROLL_SIDES = 20
CRIT_THRESHOLD = 20

# ── Gate Keeper barrier system ────────────────────────────────────────────────
# Every 5th floor (5,10,15,20,25,30,35) has a scripted Gate Keeper blocking
# descent. HP and stats scale by section; values from TDR v1.2.3 CODE_5
# jump table @ 0x3050. AC/ATK inferred from the 24-byte zone table.

GK_BARRIER_FLOORS = [5, 10, 15, 20, 25, 30, 35]

GK_HP_TABLE = {
     5: (  8,  20),
    10: ( 17,  30),
    15: ( 31,  41),
    20: ( 42,  49),
    25: ( 50,  57),   # confirmed via BSR args in CODE_4 @ 0x06e0
    30: ( 58,  64),
    35: ( 65,  79),
}

GK_AC_TABLE = {
     5:  4,
    10:  2,
    15:  1,
    20:  0,
    25: -1,
    30: -2,
    35: -3,
}

GK_ATK_TABLE = {
     5:  ( 6,  4, 10),   # (atk, dmg_min, dmg_max)
    10:  ( 9,  7, 14),
    15:  (12, 10, 18),
    20:  (15, 13, 22),
    25:  (18, 16, 26),
    30:  (21, 18, 28),
    35:  (24, 20, 32),
}

# ── Messages ──────────────────────────────────────────────────────────────────
MSG_MAX_STORED = 80
MSG_DISPLAY    = 10      # info panel shows last 10 actions
MSG_FONT_SIZE  = 18

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_MONO  = "Courier New"
FONT_SZ_SM = 15
FONT_SZ_MD = 18
FONT_SZ_LG = 22
FONT_SZ_XL = 32
FONT_SZ_TTL= 52
# KaTeX Fraktur Bold — used for all display headings (not buttons)
FONT_FRAKTUR = "assets/KaTeX_Fraktur-Bold.ttf"
