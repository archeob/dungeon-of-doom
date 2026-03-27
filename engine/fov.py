# engine/fov.py — DDA (Digital Differential Analysis) raycasting FOV
# v0.004.20260307
#
# Bug fixed: int() truncation in the previous raycaster skipped wall cells
# when the ray direction had a large x-component vs y (or vice versa), causing
# tiles behind walls to appear visible — specifically visible in the lower-left
# and upper-right quadrants due to rounding always going toward zero.
#
# Fix: proper DDA traversal — for each target tile, step along the ray by
# advancing whichever axis (x or y) has the nearer grid-line crossing.
# This guarantees every cell the ray passes through is checked in order.
# On exact corner crossings (ray hits a grid corner), both adjacent cells
# are checked before the diagonal step, preventing corner-grazing leaks.
#
# walked: separate set tracking tiles physically stepped on (mini-map).

from typing import Set
from constants import MAP_COLS, MAP_ROWS, T_WALL, T_BOULDER

_OPAQUE = {T_WALL, T_BOULDER}   # tile types that block line of sight

_EPSILON = 1e-9


def _ray_blocked(level, x0: int, y0: int, x1: int, y1: int) -> bool:
    """
    DDA traversal from (x0,y0) toward (x1,y1).
    Returns True if any cell along the path (before reaching the target) is a wall.
    The target cell itself is NOT checked here — wall faces are visible.
    """
    dx = x1 - x0
    dy = y1 - y0
    if dx == 0 and dy == 0:
        return False

    step_x = 1 if dx > 0 else -1
    step_y = 1 if dy > 0 else -1
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    # t_delta: parametric distance (0→1 = full ray) between consecutive x or y crossings
    t_delta_x = 1.0 / abs_dx if abs_dx else 1e30
    t_delta_y = 1.0 / abs_dy if abs_dy else 1e30

    # t_max: parametric t at the FIRST x / y grid-line crossing
    # Starting from cell centre (0.5 offset) so the first crossing is half a cell away.
    t_max_x = t_delta_x * 0.5
    t_max_y = t_delta_y * 0.5

    cx, cy = x0, y0

    while True:
        diff = t_max_x - t_max_y

        if diff < -_EPSILON:          # next crossing is in x
            t_max_x += t_delta_x
            cx += step_x
            nx, ny = cx, cy

        elif diff > _EPSILON:         # next crossing is in y
            t_max_y += t_delta_y
            cy += step_y
            nx, ny = cx, cy

        else:                         # exact corner — ray grazes the grid corner
            # Check both neighbouring cells before the diagonal step.
            # If either intermediate cell is a wall, the path is blocked.
            ax, ay = cx + step_x, cy       # x-neighbour
            bx, by = cx,          cy + step_y   # y-neighbour
            for chx, chy in ((ax, ay), (bx, by)):
                if chx == x1 and chy == y1:
                    continue   # the target itself — don't block
                if 0 <= chx < MAP_COLS and 0 <= chy < MAP_ROWS:
                    if level.get(chx, chy) in _OPAQUE:
                        return True
            t_max_x += t_delta_x
            t_max_y += t_delta_y
            cx += step_x
            cy += step_y
            nx, ny = cx, cy

        # Reached target without hitting a wall
        if nx == x1 and ny == y1:
            return False

        # Out of bounds = treat as blocked
        if not (0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS):
            return True

        # Wall hit — ray is blocked (but the wall face itself IS visible)
        if level.get(nx, ny) in _OPAQUE:
            return True


def compute_fov(level, cx: int, cy: int, radius: int) -> Set:
    """
    Return all tiles visible from (cx, cy) within radius.
    Uses DDA raycasting: each tile is checked by tracing the exact path
    of the ray through the grid, guaranteeing wall-blocking is symmetric
    and correct in all eight directions.
    """
    vis: Set = {(cx, cy)}
    r2 = radius * radius

    for ty in range(cy - radius, cy + radius + 1):
        for tx in range(cx - radius, cx + radius + 1):
            if tx == cx and ty == cy:
                continue
            dx = tx - cx
            dy = ty - cy
            if dx * dx + dy * dy > r2:
                continue
            if not (0 <= tx < MAP_COLS and 0 <= ty < MAP_ROWS):
                continue
            if not _ray_blocked(level, cx, cy, tx, ty):
                vis.add((tx, ty))

    return vis


def compute_fov_xray(level, cx: int, cy: int, radius: int) -> Set:
    """X-Ray FOV: all tiles within radius are visible regardless of walls."""
    vis: Set = set()
    r2 = radius * radius
    for ty in range(cy - radius, cy + radius + 1):
        for tx in range(cx - radius, cx + radius + 1):
            if not (0 <= tx < MAP_COLS and 0 <= ty < MAP_ROWS):
                continue
            dx, dy = tx - cx, ty - cy
            if dx * dx + dy * dy <= r2:
                vis.add((tx, ty))
    return vis


class FovMap:
    def __init__(self, cols, rows):
        self.cols     = cols
        self.rows     = rows
        self.visible:  Set = set()   # tiles visible this turn
        self.explored: Set = set()   # tiles ever seen
        self.walked:   Set = set()   # tiles physically stepped on (mini-map)

    def update(self, level, px: int, py: int, radius: int, intelligence: int,
               xray: bool = False):
        if xray:
            self.visible = compute_fov_xray(level, px, py, radius)
        else:
            self.visible = compute_fov(level, px, py, radius)
        # Always reveal immediately adjacent tiles
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = px + dx, py + dy
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                    self.visible.add((nx, ny))
        self.explored |= self.visible

    def mark_walked(self, x: int, y: int):
        self.walked.add((x, y))

    def is_visible(self, x, y):  return (x, y) in self.visible
    def is_explored(self, x, y): return (x, y) in self.explored
    def is_walked(self, x, y):   return (x, y) in self.walked

    def reset(self):
        self.visible.clear()
        self.explored.clear()
        self.walked.clear()
