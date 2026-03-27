# ui/renderer.py — v0.107 revised
# Ornate Mac-style viewport border. Right panel same height as left.
# No dead black strip: SCREEN_H = MENU_H + VP_PX.

import pygame
from constants import *
from engine.game import (GameState, PHASE_TITLE, PHASE_CHAR_CREATE,
                          PHASE_PLAYING, PHASE_DEAD, PHASE_WIN,
                          PHASE_INVENTORY, PHASE_WISH, PHASE_QUICK_USE,
                          PHASE_WAND_AIM, PHASE_THROW_AIM)
import ui.sprites as sprites
from ui.panels  import StatsPanel, MessagePanel
from ui.menubar import MenuBar
from ui.screens    import TitleScreen, CharCreateScreen, OverlayScreen
from ui.inventory  import InventoryScreen, WishPopup, QuickUseScreen

# ── Ornate border parameters ──────────────────────────────────────────────────
BORD          = 20
CORNER_SZ     = BORD
DIAMOND_SPACE = 46
DIAMOND_R     = 5
BAND_COL      = (232, 224, 210)
BAND_DARK     = (0, 0, 0)


class Renderer:

    def __init__(self, screen: pygame.Surface):
        self.screen     = screen
        self.surf_menu  = screen.subsurface(pygame.Rect(*RECT_MENU))
        self.surf_map   = screen.subsurface(pygame.Rect(*RECT_MAP))
        # surf_msg is a 1×1 stub — MessagePanel no longer draws to screen
        self.surf_msg   = screen.subsurface(pygame.Rect(*RECT_MSG))
        self.surf_stats = screen.subsurface(pygame.Rect(*RECT_STATS))

        self.menubar     = MenuBar(self.surf_menu)
        self.stats_panel = StatsPanel(self.surf_stats)
        self.msg_panel   = MessagePanel(self.surf_msg)   # stub
        self.title_scr   = TitleScreen(screen)
        self.char_scr    = CharCreateScreen(screen)
        self.overlay     = OverlayScreen(screen)
        self.inv_scr     = InventoryScreen(screen)
        self.wish_pop    = WishPopup(screen)
        self.quick_use   = QuickUseScreen(screen)

        self._border_surf = self._build_border_surf()

        self.tick = 0
        sprites.build_cache()

    def advance(self): self.tick += 1

    def render(self, game: GameState, char_state: dict = None):
        self.screen.fill(C_BLACK)
        if game.phase == PHASE_TITLE:
            self.title_scr.draw(self.tick,
                                has_active_game=getattr(game, '_had_game', False))
        elif game.phase == PHASE_CHAR_CREATE:
            self.char_scr.draw(char_state or {}, self.tick)
        elif game.phase in (PHASE_PLAYING, PHASE_DEAD, PHASE_WIN,
                            PHASE_INVENTORY, PHASE_WISH, PHASE_QUICK_USE,
                            PHASE_WAND_AIM, PHASE_THROW_AIM):
            if game.phase in (PHASE_DEAD, PHASE_WIN):
                # White-theme full-screen result — no game background needed
                if game.phase == PHASE_DEAD: self.overlay.draw_death(game)
                else:                        self.overlay.draw_win(game)
            else:
                self._draw_game(game)
                if   game.phase == PHASE_INVENTORY: self.inv_scr.draw(game)
                elif game.phase == PHASE_WISH:      self.wish_pop.draw(game)
                elif game.phase == PHASE_QUICK_USE: self.quick_use.draw(game)
                elif game.phase == PHASE_WAND_AIM:   self._draw_wand_aim(game)
                elif game.phase == PHASE_THROW_AIM:  self._draw_throw_aim(game)
                # ── Paused overlay ────────────────────────────────────────────────
                if game.paused and game.phase == PHASE_PLAYING:
                    self._draw_paused_overlay()
        if game.phase in (PHASE_PLAYING, PHASE_DEAD, PHASE_WIN,
                          PHASE_INVENTORY, PHASE_WISH, PHASE_QUICK_USE,
                          PHASE_WAND_AIM, PHASE_THROW_AIM):
            cs = {
                "pickup_mode": getattr(game, "pickup_mode", True),
                "sound_on":    False,
            }
            self.menubar.draw_dropdown(self.screen, check_states=cs)
        pygame.display.flip()

    # ── Game frame ────────────────────────────────────────────────────────────

    def _draw_game(self, game: GameState):
        self.menubar.draw(game)
        self._draw_9x9(game)
        self.screen.blit(self._border_surf, (0, MENU_H))
        self.stats_panel.draw(game)
        # Vertical divider — runs exactly the height of both panels
        pygame.draw.line(self.screen, C_BLACK,
                         (VP_PX, MENU_H), (VP_PX, MENU_H + VP_PX), 2)

    # ── Ornate border (built once, SRCALPHA) ──────────────────────────────────

    def _build_border_surf(self) -> pygame.Surface:
        s = pygame.Surface((VP_PX, VP_PX), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        W = H = VP_PX
        B = BORD

        pygame.draw.rect(s, (*BAND_DARK, 255), (0, 0, W, H), 3)

        pygame.draw.rect(s, (*BAND_COL, 255), (3, 3, W - 6, B - 3))
        pygame.draw.rect(s, (*BAND_COL, 255), (3, H - B, W - 6, B - 3))
        pygame.draw.rect(s, (*BAND_COL, 255), (3, B, B - 3, H - B * 2))
        pygame.draw.rect(s, (*BAND_COL, 255), (W - B, B, B - 3, H - B * 2))

        mid = B // 2
        pygame.draw.line(s, (*BAND_DARK, 200),
                         (CORNER_SZ, mid), (W - CORNER_SZ, mid), 1)
        pygame.draw.line(s, (*BAND_DARK, 200),
                         (CORNER_SZ, H - mid - 1),
                         (W - CORNER_SZ, H - mid - 1), 1)
        pygame.draw.line(s, (*BAND_DARK, 200),
                         (mid, CORNER_SZ), (mid, H - CORNER_SZ), 1)
        pygame.draw.line(s, (*BAND_DARK, 200),
                         (W - mid - 1, CORNER_SZ),
                         (W - mid - 1, H - CORNER_SZ), 1)

        pygame.draw.rect(s, (*BAND_DARK, 255),
                         (B - 2, B - 2, W - (B - 2) * 2, H - (B - 2) * 2), 2)

        for cx, cy in [(0, 0), (W - CORNER_SZ, 0),
                       (0, H - CORNER_SZ), (W - CORNER_SZ, H - CORNER_SZ)]:
            pygame.draw.rect(s, (*BAND_DARK, 255),
                             (cx, cy, CORNER_SZ, CORNER_SZ))

        DR = DIAMOND_R
        SP = DIAMOND_SPACE

        def diamond(sx, sy):
            pygame.draw.polygon(s, (*BAND_DARK, 255), [
                (sx,      sy - DR),
                (sx + DR, sy),
                (sx,      sy + DR),
                (sx - DR, sy),
            ])

        for x in range(CORNER_SZ + SP, W - CORNER_SZ, SP):
            diamond(x, mid)
            diamond(x, H - mid - 1)
        for y in range(CORNER_SZ + SP, H - CORNER_SZ, SP):
            diamond(mid, y)
            diamond(W - mid - 1, y)

        return s

    # ── 9×9 viewport ─────────────────────────────────────────────────────────

    def _draw_9x9(self, game: GameState):
        surf = self.surf_map
        surf.fill(C_BLACK)
        if not game.level or not game.player:
            return

        lv = game.level
        p  = game.player

        if game.player_on_stairs:
            tile = lv.get(p.x, p.y)
            cx, cy = VIEW_HALF * TILE, VIEW_HALF * TILE
            surf.blit(self._floor_spr(tile, p.x, p.y), (cx, cy))
            surf.blit(sprites.get(f"player_{p.class_key}"), (cx, cy))
            return

        for vy in range(VIEW_TILES):
            for vx in range(VIEW_TILES):
                wx = p.x + (vx - VIEW_HALF)
                wy = p.y + (vy - VIEW_HALF)
                sx = vx * TILE
                sy = vy * TILE

                if not game.fov.is_visible(wx, wy):
                    continue

                tile = lv.get(wx, wy)
                surf.blit(self._floor_spr(tile, wx, wy), (sx, sy))

                item = game._item_at(wx, wy)
                if item:
                    key = f"itm_{item.id}"
                    if key not in sprites._CACHE:
                        # Fallback for any item not pre-cached (e.g. modded saves)
                        sprites._CACHE[key] = sprites._load_item_sprite(item.id)
                    surf.blit(sprites._CACHE[key], (sx, sy))

                mon = game._monster_at(wx, wy)
                if mon and mon.alive:
                    if not getattr(mon, "invisible", False):
                        key = f"monster_{mon.id}"
                        monster_sprite = sprites._CACHE.get(key)
                        if monster_sprite:
                            surf.blit(monster_sprite, (sx, sy))
                        if mon.hp < mon.max_hp:
                            self._hp_bar(surf, sx, sy, mon.hp_pct)

        # Blink player sprite when HP critical: 1 Hz (60-tick cycle, hidden 8 frames)
        # At full health always visible; blink only when hp < 25%
        blink = p.hp_pct > 0.25 or (self.tick % 60) < 52
        if blink:
            surf.blit(sprites.get(f"player_{p.class_key}"),
                      (VIEW_HALF * TILE, VIEW_HALF * TILE))

        # Ray animation overlay (drawn on top of everything)
        if game.ray_anim is not None:
            self._draw_ray_anim(surf, game)

    def _floor_spr(self, tile: int, wx: int, wy: int) -> pygame.Surface:
        if   tile == T_WALL:       return sprites.get("wall_lit")
        elif tile == T_STAIR_DOWN: return sprites.get("stair_down")
        elif tile == T_STAIR_UP:   return sprites.get("stair_up")
        elif tile == T_BOULDER:    return sprites.get("boulder")
        else:
            light = (wx + wy) % 2 == 0
            return sprites.get("floor_light_lit" if light else "floor_grey_lit")

    def _hp_bar(self, surf, sx, sy, pct):
        bw  = TILE - 8
        col = C_HP_FULL if pct > 0.5 else C_HP_MID if pct > 0.25 else C_HP_LOW
        pygame.draw.rect(surf, C_WALL_LIT, (sx + 4, sy + 2, bw, 8))
        pygame.draw.rect(surf, col,        (sx + 4, sy + 2, max(2, int(bw * pct)), 8))

    def _hostility_dot(self, surf, sx, sy, mon):
        """Small coloured dot in the bottom-right corner of the tile indicating hostility."""
        from constants import (HOSTILITY_AFRAID, HOSTILITY_NEUTRAL,
                               HOSTILITY_CAUTIOUS, HOSTILITY_DOT_COLOR)
        h = getattr(mon, "current_hostility", 2)
        # Don't draw a dot for plain HOSTILE — that's the default expectation
        if h >= 2 and not getattr(mon, "charmed", False):
            return
        col = HOSTILITY_DOT_COLOR.get(h, (200, 200, 200))
        # Override: charmed always shows green neutral dot
        if getattr(mon, "charmed", False):
            col = HOSTILITY_DOT_COLOR[HOSTILITY_NEUTRAL]
        r   = 6
        cx  = sx + TILE - r - 4
        cy  = sy + TILE - r - 4
        pygame.draw.circle(surf, (20, 20, 20), (cx, cy), r + 1)   # dark border
        pygame.draw.circle(surf, col,          (cx, cy), r)

    # ── Wand aiming overlay ────────────────────────────────────────────────────

    def _draw_paused_overlay(self):
        """Semi-transparent dark veil + centred PAUSED banner over the map."""
        surf = self.surf_map
        W, H = surf.get_size()
        # Dark veil
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        surf.blit(veil, (0, 0))
        # Text banner
        font_big = pygame.font.SysFont("Courier New", 36, bold=True)
        font_sm  = pygame.font.SysFont("Courier New", 16)
        lbl  = font_big.render("PAUSED", True, (255, 255, 255))
        hint = font_sm.render("Press Space or Control \u25b8 Pause to resume", True, (200, 200, 200))
        cx, cy = W // 2, H // 2
        surf.blit(lbl,  (cx - lbl.get_width()  // 2, cy - lbl.get_height()  // 2 - 14))
        surf.blit(hint, (cx - hint.get_width() // 2, cy + hint.get_height() // 2 +  6))

    def _draw_wand_aim(self, game):
        """Draw the 8-directional aim overlay in PHASE_WAND_AIM."""
        surf = self.surf_map
        p    = game.player

        # Player screen centre within surf_map
        pcx = VIEW_HALF * TILE + TILE // 2
        pcy = VIEW_HALF * TILE + TILE // 2

        # Draw a translucent highlight on each of the 8 neighbouring tiles
        arrow_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        arrow_surf.fill((220, 180, 40, 55))   # warm amber, very transparent

        _8DIRS = [(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
        for dx, dy in _8DIRS:
            wx = p.x + dx;  wy = p.y + dy
            if not (0 <= wx < MAP_COLS and 0 <= wy < MAP_ROWS):
                continue
            sx = (VIEW_HALF + dx) * TILE
            sy = (VIEW_HALF + dy) * TILE
            surf.blit(arrow_surf, (sx, sy))
            # Arrow triangle pointing outward from player
            self._draw_dir_arrow(surf,
                sx + TILE // 2, sy + TILE // 2,
                dx, dy, (240, 200, 60, 220))

        # "AIM" label in the viewport (top-left, inside border)
        try:
            font = pygame.font.SysFont("Courier New", 17, bold=True)
            lbl  = font.render("ZAP — choose direction  [ESC cancel]",
                               True, (240, 200, 60))
            # Dark backing
            backing = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 4),
                                     pygame.SRCALPHA)
            backing.fill((0, 0, 0, 160))
            surf.blit(backing, (22, 22))
            surf.blit(lbl, (26, 24))
        except Exception:
            pass

    def _draw_throw_aim(self, game):
        """Draw the 8-directional aim overlay in PHASE_THROW_AIM."""
        surf = self.surf_map
        p    = game.player
        item = getattr(game, "pending_throw", None)

        # Item name for banner
        item_name = item.get("name", "item") if item else "item"

        # Highlight 8 adjacent tiles in green-grey (earthy tone for throwing)
        arrow_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        arrow_surf.fill((140, 180, 120, 55))

        _8DIRS = [(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
        for dx, dy in _8DIRS:
            wx = p.x + dx;  wy = p.y + dy
            if not (0 <= wx < MAP_COLS and 0 <= wy < MAP_ROWS):
                continue
            sx = (VIEW_HALF + dx) * TILE
            sy = (VIEW_HALF + dy) * TILE
            surf.blit(arrow_surf, (sx, sy))
            self._draw_dir_arrow(surf,
                sx + TILE // 2, sy + TILE // 2,
                dx, dy, (160, 220, 100, 220))

        # Banner
        try:
            font = pygame.font.SysFont("Courier New", 17, bold=True)
            lbl  = font.render(f"THROW {item_name.upper()} — choose direction  [ESC cancel]",
                               True, (160, 220, 100))
            backing = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 4),
                                     pygame.SRCALPHA)
            backing.fill((0, 0, 0, 160))
            surf.blit(backing, (22, 22))
            surf.blit(lbl, (26, 24))
        except Exception:
            pass

    def _draw_dir_arrow(self, surf, cx, cy, dx, dy, col):
        """Draw a small filled triangle pointing in direction (dx,dy)."""
        size = 12
        # Normalise to arrow direction
        nx, ny = dx, dy
        # Perpendicular
        px, py = -ny, nx
        tip   = (cx + nx * size,     cy + ny * size)
        left  = (cx + px * (size//2), cy + py * (size//2))
        right = (cx - px * (size//2), cy - py * (size//2))
        try:
            s = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            s.fill((0,0,0,0))
            pygame.draw.polygon(s, col, [tip, left, right])
            surf.blit(s, (0, 0))
        except Exception:
            pass

    # ── Ray animation draw (called from _draw_9x9) ─────────────────────────────

    def _draw_ray_anim(self, surf, game):
        """Overlay the wand ray animation onto the map surface."""
        ra = game.ray_anim
        if ra is None:
            return

        # Initialise start_tick on first draw
        if ra["start_tick"] is None:
            ra["start_tick"] = self.tick

        elapsed = self.tick - ra["start_tick"]
        total   = ra["total_ticks"]

        if elapsed >= total:
            game.ray_anim = None
            return

        tiles   = ra["tiles"]
        r, g, b = ra["color"]
        n       = len(tiles)
        if n == 0:
            game.ray_anim = None
            return

        p = game.player

        # Progress 0→1 across the full duration
        progress = elapsed / total

        # Phase 1 (0→0.5): ray extends tile-by-tile from player outward
        # Phase 2 (0.5→1): full ray fades out
        for i, (wx, wy) in enumerate(tiles):
            vx = wx - p.x + VIEW_HALF
            vy = wy - p.y + VIEW_HALF
            if not (0 <= vx < VIEW_TILES and 0 <= vy < VIEW_TILES):
                continue

            tile_progress = (i + 1) / n          # 0→1 along ray length

            # In phase 1, only tiles up to current progress are lit
            if progress < 0.5:
                lit_front = (progress * 2) * n   # how many tiles lit
                if i >= lit_front:
                    continue
                alpha_raw = 230
            else:
                # Phase 2: fade out all
                fade = 1.0 - (progress - 0.5) * 2
                alpha_raw = int(230 * fade)

            if alpha_raw <= 0:
                continue

            sx = vx * TILE
            sy = vy * TILE

            glow = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            # Thick centre stripe + bloom
            bloom = int(alpha_raw * 0.35)
            glow.fill((r, g, b, bloom))
            # Core stripe along ray direction
            if tiles:
                # direction from first tile to last
                t0x, t0y = tiles[0]
                tlx, tly = tiles[-1]
                dx = tlx - t0x; dy = tly - t0y
                dl = max(1, abs(dx) + abs(dy))
                ndx = dx / dl; ndy = dy / dl
            else:
                ndx = ndy = 0
            # Core rect
            stripe_w = max(6, TILE // 5)
            stripe_h = max(6, TILE // 5)
            cx_ = TILE // 2 - stripe_w // 2
            cy_ = TILE // 2 - stripe_h // 2
            core_surf = pygame.Surface((stripe_w, stripe_h), pygame.SRCALPHA)
            core_surf.fill((r, g, b, min(255, alpha_raw)))
            glow.blit(core_surf, (cx_, cy_))

            surf.blit(glow, (sx, sy))
