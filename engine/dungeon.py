# engine/dungeon.py — Corridor-grid maze dungeon generator
# v0.303.20260310
#
# === DESIGN FROM ORIGINAL GAME SCREENSHOTS (floors 2-19) ===
#
# The dungeon is NOT rooms connected by corridors.
# It is a GRID of equal-width corridors separated by 1-tile walls,
# connected as a perfect maze (spanning tree — no loops).
#
# Corridor width (W) shrinks with depth:
#   Floor  1 → W=9   Floor  2 → W=9   Floor  5 → W=8
#   Floor 10 → W=7   Floor 15 → W=6   Floor 20 → W=5
#   Floor 25 → W=4   Floor 30 → W=3   Floor 35 → W=2
#   Floor 40 → W=1
#   Formula: W = max(1, round(9 - floor / 5))
#
# Grid layout (60×60 map, 1-tile hard border on each side):
#   stride    = W + 1          (cell + right/bottom wall)
#   cells     = (inner+1)//stride  where inner = MAP_COLS-2 = 58
#   Grid is centred in the 58×58 usable interior.
#
# Algorithm: iterative recursive backtracker on the cell grid.
#   • Every cell (W×W block) becomes floor.
#   • Every passage removes the 1-tile wall between two cells (W tiles wide).
#   • Corner "pillar" tiles at wall-grid intersections stay as walls.
#
# Depth progression:
#   Floor  2: 5×5 cells, W=9 — very wide corridors
#   Floor 10: 7×7 cells, W=7 — medium corridors, denser maze
#   Floor 15: 8×8 cells, W=6 — narrower, more labyrinthine
#   Floor 40: 29×29 cells, W=1 — single-tile passages, densest maze

import random
from typing import List, Tuple, Optional, Dict
from constants import (
    MAP_COLS, MAP_ROWS, TOTAL_FLOORS,
    T_FLOOR, T_WALL, T_STAIR_UP, T_STAIR_DOWN, PASSABLE,
)

BORDER = 1   # hard wall border kept around the whole map


# ── Corridor-width schedule ───────────────────────────────────────────────────

def _corridor_width(floor: int) -> int:
    """
    Corridor width (W) for the given dungeon floor.
    Verified against original screenshots:
      floor 2=9, 5=8, 10=7, 15=6, 20=5, 25=4, 30=3, 35=2, 40=1
    """
    return max(1, round(9.0 - floor / 5.0))


# ── Enchant roller (unchanged) ────────────────────────────────────────────────

def _roll_enchant(rng, max_cap: int) -> int:
    """Weighted enchant roll centred on 0.  Negative = cursed quality.
    Weights: -2:2  -1:10  0:52  +1:22  +2:8  +3:5  +4:1  (total 100)
    The +4 result is rare but possible; clamped to max_cap and item max_enchant."""
    _WTS = [(-2, 2), (-1, 10), (0, 52), (1, 22), (2, 8), (3, 5), (4, 1)]
    r   = rng.randint(1, 100)
    cum = 0
    for val, w in _WTS:
        cum += w
        if r <= cum:
            return max(-2, min(val, max_cap))
    return 0


# ── DungeonLevel ─────────────────────────────────────────────────────────────

class DungeonLevel:
    def __init__(self, floor, seed):
        self.floor = floor
        self.seed  = seed
        self.rng   = random.Random(seed)
        # Start fully solid — carving creates floor
        self.tiles: List[List[int]] = [[T_WALL] * MAP_COLS for _ in range(MAP_ROWS)]
        self.stair_up:       Optional[Tuple[int, int]] = None
        self.stair_down:     Optional[Tuple[int, int]] = None
        self.spawn_player:   Optional[Tuple[int, int]] = None
        self.monster_spawns: List[Dict] = []
        self.item_spawns:    List[Dict] = []
        self.rooms:          list = []   # unused; kept for API compatibility
        # Tile modifications made after generation (wand of Digging, boulder push).
        # Maps (x, y) → new tile type.  Persisted in save files so changes survive
        # save/load cycles.
        self.tile_mods: dict = {}

    def get(self, x, y):
        if 0 <= x < MAP_COLS and 0 <= y < MAP_ROWS:
            return self.tiles[y][x]
        return T_WALL

    def set(self, x, y, t):
        if 0 <= x < MAP_COLS and 0 <= y < MAP_ROWS:
            self.tiles[y][x] = t

    def is_passable(self, x, y):
        return self.get(x, y) in PASSABLE

    def is_in_bounds(self, x, y):
        return 0 <= x < MAP_COLS and 0 <= y < MAP_ROWS

    def neighbours4(self, x, y):
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            nx, ny = x + dx, y + dy
            if self.is_in_bounds(nx, ny):
                yield nx, ny

    def floor_tiles(self):
        return [(x, y)
                for y in range(MAP_ROWS)
                for x in range(MAP_COLS)
                if self.tiles[y][x] == T_FLOOR]


# ── DungeonGenerator ─────────────────────────────────────────────────────────

class DungeonGenerator:

    def __init__(self, floor: int, seed: int):
        self.floor = floor
        self.lv    = DungeonLevel(floor, seed)
        self.rng   = self.lv.rng

    def generate(self) -> DungeonLevel:
        self._gen_corridor_maze()
        self._place_stairs()
        self._populate()
        return self.lv

    # ── Core maze generator ───────────────────────────────────────────────────

    def _gen_corridor_maze(self):
        lv     = self.lv
        W      = _corridor_width(self.floor)
        stride = W + 1   # one cell + the 1-tile wall after it

        # Usable interior: columns 1..MAP_COLS-2 (58 tiles each axis)
        inner = MAP_COLS - 2

        # Maximum cells that fit:
        #   cells * W  +  (cells-1) * 1  <=  inner
        #   cells * (W+1) - 1            <=  inner
        #   cells                        <=  (inner+1) / (W+1)
        cells_x = max(2, (inner + 1) // stride)
        cells_y = max(2, (inner + 1) // stride)

        # Centre the grid in the interior
        total_w = cells_x * stride - 1
        total_h = cells_y * stride - 1
        ox = BORDER + (inner - total_w) // 2
        oy = BORDER + (inner - total_h) // 2

        # Store for helper methods
        self._W       = W
        self._stride  = stride
        self._cells_x = cells_x
        self._cells_y = cells_y
        self._ox      = ox
        self._oy      = oy

        # ── Iterative recursive backtracker ───────────────────────────────────
        # Visits every cell, carving a spanning tree of passages.
        # Using an iterative stack avoids Python recursion-depth problems
        # (worst case: 29×29 = 841 cells at floor 40).
        visited = [[False] * cells_x for _ in range(cells_y)]

        sx = self.rng.randint(0, cells_x - 1)
        sy = self.rng.randint(0, cells_y - 1)

        self._carve_cell(sx, sy)
        visited[sy][sx] = True
        stack = [(sx, sy)]

        DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))

        while stack:
            cx, cy = stack[-1]
            nbrs = [
                (dx, dy)
                for dx, dy in DIRS
                if 0 <= cx + dx < cells_x
                and 0 <= cy + dy < cells_y
                and not visited[cy + dy][cx + dx]
            ]
            if nbrs:
                dx, dy = self.rng.choice(nbrs)
                nx, ny = cx + dx, cy + dy
                self._carve_passage(cx, cy, nx, ny)
                self._carve_cell(nx, ny)
                visited[ny][nx] = True
                stack.append((nx, ny))
            else:
                stack.pop()

        # Centres of every cell — used by _place_stairs
        self._cell_centres = [
            (ox + cx * stride + W // 2,
             oy + cy * stride + W // 2)
            for cy in range(cells_y)
            for cx in range(cells_x)
        ]

    # ── Carving helpers ───────────────────────────────────────────────────────

    def _carve_cell(self, cx: int, cy: int):
        """Carve the W×W floor block for grid cell (cx, cy)."""
        x0 = self._ox + cx * self._stride
        y0 = self._oy + cy * self._stride
        W  = self._W
        for dy in range(W):
            for dx in range(W):
                self.lv.set(x0 + dx, y0 + dy, T_FLOOR)

    def _carve_passage(self, cx: int, cy: int, nx: int, ny: int):
        """
        Remove the 1-tile wall between adjacent cells (cx,cy) and (nx,ny).
        The opening is W tiles wide (matching corridor width) and 1 tile deep.
        The 1×1 corner pillar tiles at grid intersections are never touched.
        """
        W      = self._W
        stride = self._stride
        ox, oy = self._ox, self._oy

        if nx > cx:          # rightward: wall column at x = ox + cx*stride + W
            wx = ox + cx * stride + W
            wy = oy + cy * stride
            for d in range(W):
                self.lv.set(wx, wy + d, T_FLOOR)
        elif nx < cx:        # leftward: wall column at x = ox + nx*stride + W
            wx = ox + nx * stride + W
            wy = oy + ny * stride
            for d in range(W):
                self.lv.set(wx, wy + d, T_FLOOR)
        elif ny > cy:        # downward: wall row at y = oy + cy*stride + W
            wy = oy + cy * stride + W
            wx = ox + cx * stride
            for d in range(W):
                self.lv.set(wx + d, wy, T_FLOOR)
        elif ny < cy:        # upward: wall row at y = oy + ny*stride + W
            wy = oy + ny * stride + W
            wx = ox + nx * stride
            for d in range(W):
                self.lv.set(wx + d, wy, T_FLOOR)

    # ── Stair placement ───────────────────────────────────────────────────────

    def _place_stairs(self):
        lv    = self.lv
        cells = self._cell_centres

        # Two most-distant cell centres for maximum separation
        best_d = -1
        pos_up = cells[0]
        pos_dn = cells[-1]
        n = len(cells)
        for i in range(n):
            for j in range(i + 1, n):
                d = (abs(cells[i][0] - cells[j][0]) +
                     abs(cells[i][1] - cells[j][1]))
                if d > best_d:
                    best_d = d
                    pos_up = cells[i]
                    pos_dn = cells[j]

        # Floor 1: stair_up marks surface entrance (ascending is blocked by game.py).
        lv.stair_up     = pos_up
        lv.spawn_player = pos_up
        lv.set(*pos_up, T_STAIR_UP)

        if self.floor < TOTAL_FLOORS:
            lv.stair_down = pos_dn
            lv.set(*pos_dn, T_STAIR_DOWN)

    # ── Population ────────────────────────────────────────────────────────────

    def _populate(self):
        lv    = self.lv
        floor = self.floor
        from data.monsters import monsters_for_floor
        from data.items    import items_by_category_for_floor, throwing_items_for_floor
        from constants import (IC_POTION, IC_SCROLL, IC_WEAPON, IC_FOOD,
                               IC_WAND, IC_ARMOR, IC_RING, IC_JEWEL)

        # ── Monster spawns ────────────────────────────────────────────────────
        specials = {lv.stair_up, lv.stair_down, lv.spawn_player}
        tiles = [p for p in lv.floor_tiles() if p not in specials]
        self.rng.shuffle(tiles)

        # ── Floor 40: scripted Dark Wizard spawn ──────────────────────────────
        # The Dark Wizard has spawn_freq=0 so monsters_for_floor() never returns
        # it.  On floor 40 we place exactly one instance at the tile most distant
        # from the stair_up (player start), matching original TDR behaviour.
        # hp_fixed=800 overrides dice rolling per the binary data table.
        if floor == 40 and tiles:
            from data.monsters import get_monster
            dw_data   = get_monster("dark_wizard")
            spawn_pt  = lv.spawn_player or lv.stair_up or (1, 1)
            boss_tile = max(
                tiles,
                key=lambda t: abs(t[0] - spawn_pt[0]) + abs(t[1] - spawn_pt[1])
            )
            hp = dw_data["hp_fixed"] if dw_data.get("hp_fixed") else (
                sum(self.rng.randint(1, dw_data["hp_dice"][1])
                    for _ in range(dw_data["hp_dice"][0]))
            )
            lv.monster_spawns.append({
                "monster_id": "dark_wizard",
                "x": boss_tile[0], "y": boss_tile[1],
                "hp": hp, "max_hp": hp,
                "boss_escapes": 0,
            })
            tiles = [t for t in tiles if t != boss_tile]

        eligible = monsters_for_floor(floor)
        if not eligible:
            # Skip normal random spawns (floor 40 only has the scripted boss)
            pass
        else:
            mpool = []
            for m in eligible:
                mpool.extend([m] * max(1, m["min_floor"]))

            n_mon = min(len(tiles) // 20, 8 + floor // 3)
            for i in range(min(n_mon, len(tiles))):
                x, y = tiles[i]
                m    = self.rng.choice(mpool)
                # hp_fixed: boss monsters always spawn at a set HP value
                if m.get("hp_fixed") is not None:
                    hp = m["hp_fixed"]
                else:
                    n, s = m["hp_dice"]
                    hp   = sum(self.rng.randint(1, s) for _ in range(n))
                lv.monster_spawns.append({
                    "monster_id": m["id"], "x": x, "y": y,
                    "hp": hp, "max_hp": hp,
                })

        # ── Item spawns — independent per category ────────────────────────────
        # tile offset starts after all placed monsters (boss + randoms)
        n_mon = len(lv.monster_spawns)
        tile_cur = [n_mon]

        def _spawn(cat, count, enchant_cap=0):
            ipool = items_by_category_for_floor(cat, floor)
            if not ipool:
                return
            for _ in range(count):
                if tile_cur[0] >= len(tiles):
                    return
                x, y = tiles[tile_cur[0]]
                tile_cur[0] += 1
                it  = self.rng.choice(ipool)
                if enchant_cap:
                    # Respect the item's own max_enchant — e.g. shield caps at +2
                    cap = min(enchant_cap, it.get("max_enchant", enchant_cap))
                    enc = _roll_enchant(self.rng, cap)
                else:
                    enc = 0
                lv.item_spawns.append({
                    "item_id": it["id"], "x": x, "y": y, "enchant": enc,
                })

        # ── Food: scaled by floor depth ───────────────────────────────────────
        if floor <= 5:
            food_count = self.rng.randint(4, 6)
        elif floor <= 15:
            food_count = self.rng.randint(3, 5)
        elif floor <= 30:
            food_count = self.rng.randint(2, 4)
        else:
            food_count = self.rng.randint(2, 3)
        _spawn(IC_FOOD, food_count)

        _spawn(IC_POTION, self.rng.randint(1 + int(floor >= 15),
                                           3 + int(floor >= 20)))
        if floor >= 2:
            _spawn(IC_SCROLL, self.rng.randint(int(floor >= 10),
                                               2 + int(floor >= 15)))

        # ── Weapons: corrected unlock formula ─────────────────────────────────
        # Old formula (floor//5+2) kept Dagger+Whip only until floor 5.
        # New: Long Sword available from floor 2, Mace from floor 5,
        # Two-Handed from floor 10, Death Blade from floor 20.
        # floor//3+1 maps: floors 1→2  Dagger/Whip; floor 3→2  same;
        # floor 4→2  +LongSword; floor 7→3  +Mace; floor 12→5  +2H; etc.
        # Adjusted to: max_dmg = floor//4 + 2  (friendlier early unlock)
        #   floor 1-3: max_dmg=2  Dagger, Whip
        #   floor 4-7: max_dmg=3  + Long Sword
        #   floor 8-11: max_dmg=4  + Mace
        #   floor 12-15: max_dmg=5  + Two-Handed Sword
        #   floor 16+: max_dmg=6  + Death Blade
        _spawn(IC_WEAPON, self.rng.randint(0, 1 + int(floor >= 20)),
               enchant_cap=4)

        # ── Armor: guaranteed one body piece + accessories separately ─────────
        # Old system picked randomly from all armor slots, so early floors
        # were more likely to yield Helmets/Gloves than body armor.
        # New: always spawn 1 body armor first, then 1-2 accessories.
        from constants import IC_ARMOR
        from data.items import ITEMS

        body_pool = [i for i in ITEMS
                     if i["cat"] == IC_ARMOR and i["slot"] == "armor"
                     and i.get("base_ac", 0) <= max(1, floor // 8 + 1)]
        acc_pool  = [i for i in ITEMS
                     if i["cat"] == IC_ARMOR and i["slot"] != "armor"
                     and i.get("base_ac", 0) <= 2]   # accessories cap at +2

        # Spawn 1 guaranteed body armor piece
        if body_pool and tile_cur[0] < len(tiles):
            x, y = tiles[tile_cur[0]]; tile_cur[0] += 1
            it   = self.rng.choice(body_pool)
            cap  = min(4, it.get("max_enchant", 4))
            lv.item_spawns.append({
                "item_id": it["id"], "x": x, "y": y,
                "enchant": _roll_enchant(self.rng, cap)
            })

        # Then 1-2 accessories (helmet, gloves, shield, cloak)
        if acc_pool:
            acc_count = self.rng.randint(1, 2 + int(floor >= 10))
            for _ in range(acc_count):
                if tile_cur[0] >= len(tiles):
                    break
                x, y = tiles[tile_cur[0]]; tile_cur[0] += 1
                it   = self.rng.choice(acc_pool)
                cap  = min(2, it.get("max_enchant", 2))
                lv.item_spawns.append({
                    "item_id": it["id"], "x": x, "y": y,
                    "enchant": _roll_enchant(self.rng, cap)
                })

        # Throwing items
        _throw_pool = throwing_items_for_floor(floor)
        if _throw_pool:
            for _ in range(self.rng.randint(1, 2 + int(floor >= 10))):
                it     = self.rng.choice(_throw_pool)
                tx, ty = self.rng.choice(list(lv.floor_tiles()))
                lv.item_spawns.append({
                    "item_id": it["id"], "x": tx, "y": ty, "enchant": 0,
                })

        if floor >= 5 and self.rng.random() < min(0.80, 0.30 + 0.015 * floor):
            _spawn(IC_WAND, 1)
        if floor >= 8 and self.rng.random() < min(0.70, 0.25 + 0.012 * floor):
            _spawn(IC_RING, 1, enchant_cap=2)
        if floor >= 15:
            _spawn(IC_JEWEL, self.rng.randint(0, 1 + int(floor >= 25)))


# ── Floor cache ───────────────────────────────────────────────────────────────

class FloorCache:
    def __init__(self, base_seed: int):
        self.base_seed = base_seed
        self._levels: Dict = {}

    def get(self, floor: int) -> DungeonLevel:
        if floor not in self._levels:
            seed = (self.base_seed ^ (floor * 0x9e3779b9)) & 0xFFFFFFFF
            self._levels[floor] = DungeonGenerator(floor, seed).generate()
        return self._levels[floor]

    def invalidate(self):
        self._levels.clear()
