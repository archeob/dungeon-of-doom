#!/usr/bin/env python3
# main.py — Dungeon of Doom (1985) Recreation
# v0.103.20260307
# Run:  python main.py
# Requires: pip install pygame

import sys
import os
import pygame

from constants import (SCREEN_W, SCREEN_H, FPS,
                       RECT_MAP, RECT_MENU, MENU_H,
                       VP_PX, TILE, VIEW_HALF, TURN_MS,
                       DIFF_ADVENTURER, DIFF_HERO, DIFF_ARCHITECT)
from data.classes import CLASS_ORDER
from engine.game import (GameState, PHASE_TITLE, PHASE_CHAR_CREATE,
                         PHASE_PLAYING, PHASE_DEAD, PHASE_WIN,
                         PHASE_INVENTORY, PHASE_WISH, PHASE_QUICK_USE,
                         PHASE_THROW_AIM,
                         PHASE_WAND_AIM)
from engine.save import save_game, load_game, RESUME_PATH
from ui.renderer import Renderer


# ── File dialog helpers (tkinter) ─────────────────────────────────────────────

def _file_dialog_save(title="Save Game", initial="save.dod") -> str:
    """Open a native Save-As dialog. Returns chosen path or ''."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.asksaveasfilename(
            parent=root, title=title,
            defaultextension=".dod",
            initialfile=initial,
            filetypes=[("Dungeon of Doom save", "*.dod"), ("All files", "*.*")])
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _file_dialog_open(title="Open Game") -> str:
    """Open a native Open dialog. Returns chosen path or ''."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            parent=root, title=title,
            filetypes=[("Dungeon of Doom save", "*.dod"), ("All files", "*.*")])
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _confirm_dialog(title: str, message: str) -> bool:
    """Simple yes/no dialog. Returns True for yes."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        result = messagebox.askyesno(title, message, parent=root)
        root.destroy()
        return bool(result)
    except Exception:
        return True   # fail-safe: allow the action


def _error_dialog(title: str, message: str):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    except Exception:
        pass


# ── Save helpers ──────────────────────────────────────────────────────────────

def _do_save(game: GameState, path: str) -> bool:
    """Save to path. Returns True on success."""
    try:
        game._save_floor_state()
        save_game(game, path)
        game.save_path = path
        game.dirty     = False
        game.log.add(f"Game saved: {os.path.basename(path)}")
        return True
    except Exception as e:
        _error_dialog("Save failed", str(e))
        return False


def _do_save_as(game: GameState) -> bool:
    """Prompt for filename then save. Returns True on success."""
    initial = os.path.basename(game.save_path) if game.save_path else "save.dod"
    path = _file_dialog_save(initial=initial)
    if not path:
        return False
    return _do_save(game, path)


def _check_unsaved(game: GameState) -> bool:
    """
    If game has unsaved changes, ask the user whether to save.
    Returns True if it's safe to proceed (saved or discarded).
    Returns False if the user cancelled.
    Hero difficulty: silently auto-saves to RESUME_PATH instead of showing dialog.
    """
    if not game.dirty or game.phase not in (PHASE_PLAYING, PHASE_DEAD, PHASE_WIN,
                                          PHASE_INVENTORY):
        return True
    if game.phase in (PHASE_DEAD, PHASE_WIN):
        return True   # game over — nothing meaningful to save
    if getattr(game, "difficulty", DIFF_ADVENTURER) == DIFF_HERO:
        # Hero: silently auto-save to resume slot
        _do_save(game, RESUME_PATH)
        return True
    result = _confirm_dialog(
        "Unsaved changes",
        "You have unsaved progress. Save before closing?"
    )
    if result:
        if game.save_path:
            return _do_save(game, game.save_path)
        else:
            return _do_save_as(game)
    return True   # user chose not to save — ok to proceed


# ── File menu actions ─────────────────────────────────────────────────────────

def _action_new(game: GameState, char_state: dict, renderer: Renderer) -> tuple:
    """Start a new game. Returns (game, char_state)."""
    if not _check_unsaved(game):
        return game, char_state
    renderer.menubar.dismiss()
    char_state = fresh_char_state()
    game.phase = PHASE_CHAR_CREATE
    return game, char_state


def _action_open(game: GameState, renderer: Renderer) -> GameState:
    """Open a saved game. Returns (possibly new) game."""
    if not _check_unsaved(game):
        return game
    path = _file_dialog_open()
    if not path:
        return game
    try:
        new_game = load_game(path)
        new_game._had_game = True
        renderer.menubar.dismiss()
        return new_game
    except Exception as e:
        _error_dialog("Open failed", str(e))
        return game


def _action_close(game: GameState, renderer: Renderer) -> GameState:
    """Close current game → title screen. Returns game."""
    if not _check_unsaved(game):
        return game
    renderer.menubar.dismiss()
    game.phase = PHASE_TITLE
    return game


def _action_save(game: GameState) -> None:
    if getattr(game, "difficulty", DIFF_ADVENTURER) == DIFF_HERO:
        game.log.add("Hero mode: manual saving is disabled.", (180, 80, 80))
        return
    if game.save_path:
        _do_save(game, game.save_path)
    else:
        _do_save_as(game)


def _action_save_as(game: GameState) -> None:
    if getattr(game, "difficulty", DIFF_ADVENTURER) == DIFF_HERO:
        game.log.add("Hero mode: manual saving is disabled.", (180, 80, 80))
        return
    _do_save_as(game)


def _action_quit(game: GameState, renderer: Renderer) -> bool:
    """Returns True if app should exit."""
    if not _check_unsaved(game):
        return False
    return True


# ── Mouse movement helpers ────────────────────────────────────────────────────

_PLAYER_VX = VIEW_HALF * TILE + TILE // 2
_PLAYER_VY = VIEW_HALF * TILE + TILE // 2
_MOUSE_INITIAL_DELAY_MS = 220
_MOUSE_REPEAT_MS        =  70


def _viewport_direction(vx: int, vy: int) -> tuple[int, int]:
    dx_px = vx - _PLAYER_VX
    dy_px = vy - _PLAYER_VY
    if abs(dx_px) < TILE // 2 and abs(dy_px) < TILE // 2:
        return 0, 0
    adx, ady = abs(dx_px), abs(dy_px)
    _TAN22 = 0.4142
    dx = 0 if adx < ady * _TAN22 else (1 if dx_px > 0 else -1)
    dy = 0 if ady < adx * _TAN22 else (1 if dy_px > 0 else -1)
    return dx, dy


# ── Character creation state ──────────────────────────────────────────────────

def fresh_char_state():
    return {"name": "", "selected_class": 0, "cursor_on": "name",
            "difficulty": DIFF_ADVENTURER}


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("The Dungeon of Doom  —  1985 Recreation")
    screen    = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock     = pygame.time.Clock()

    game       = GameState()
    renderer   = Renderer(screen)
    char_state = fresh_char_state()

    pygame.key.set_repeat(220, 70)

    mouse_dir     = (0, 0)
    mouse_held    = False
    mouse_next_ms = 0
    turn_start_ms = 0    # when the current 5-second turn window began
    prev_phase    = None  # detect transitions back to PHASE_PLAYING
    running       = True

    while running:
        clock.tick(FPS)
        renderer.advance()
        now = pygame.time.get_ticks()

        # ── Turn timer management ─────────────────────────────────────────────
        # Reset the clock when:
        #  (a) a player action completed (game.turn_reset_pending), OR
        #  (b) we just returned to PHASE_PLAYING from any overlay/menu
        #      (inventory, quick-use, wand-aim, throw-aim, wish, pause)
        #      — so the player always gets a fresh 5 seconds after closing a screen
        returned_to_playing = (game.phase == PHASE_PLAYING and prev_phase != PHASE_PLAYING)
        if game.turn_reset_pending or returned_to_playing:
            game.turn_reset_pending = False
            turn_start_ms = now
        prev_phase = game.phase

        # ── Auto-pass: only fires in PHASE_PLAYING and when not paused ────────
        if (game.phase == PHASE_PLAYING and not game.paused
                and now - turn_start_ms >= TURN_MS):
            game.auto_pass()
            # auto_pass sets turn_reset_pending → timer restarts next frame

        # Auto-repeat mouse movement
        if mouse_held and game.phase == PHASE_PLAYING and not game.paused and not game.phase == PHASE_INVENTORY:
            if now >= mouse_next_ms and mouse_dir != (0, 0):
                game.try_move(*mouse_dir)
                mouse_next_ms = now + _MOUSE_REPEAT_MS

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if _check_unsaved(game):
                    running = False

            elif event.type == pygame.MOUSEMOTION:
                if game.phase == PHASE_INVENTORY:
                    renderer.inv_scr.handle_motion(*event.pos)
                elif game.phase == PHASE_QUICK_USE:
                    renderer.quick_use.handle_motion(*event.pos)
                elif game.phase == PHASE_TITLE:
                    renderer.title_scr.handle_motion(*event.pos)
                elif game.phase == PHASE_CHAR_CREATE:
                    renderer.char_scr.handle_motion(*event.pos)
                elif game.phase in (PHASE_DEAD, PHASE_WIN):
                    renderer.overlay.handle_motion(*event.pos)

            elif event.type == pygame.MOUSEWHEEL:
                dy = -event.y   # positive y = scroll down
                if game.phase == PHASE_INVENTORY:
                    renderer.inv_scr.scroll(dy, game)
                elif game.phase == PHASE_QUICK_USE:
                    renderer.quick_use.scroll(dy, game)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sx, sy = event.pos

                # ── Char create screen clicks ─────────────────────────────────
                if game.phase == PHASE_CHAR_CREATE:
                    action = renderer.char_scr.handle_click(sx, sy, char_state)
                    if action == renderer.char_scr.BTN_BEGIN:
                        name = char_state.get("name", "").strip() or "Adventurer"
                        cls  = CLASS_ORDER[char_state.get("selected_class", 0)]
                        diff = char_state.get("difficulty", DIFF_ADVENTURER)
                        game.start_new_game(name, cls, diff)
                    elif action == renderer.char_scr.BTN_BACK:
                        game.phase = PHASE_TITLE
                    continue

                # ── Wand aim clicks ──────────────────────────────────────────
                if game.phase == PHASE_WAND_AIM:
                    _handle_wand_aim_click(sx, sy, game)
                elif game.phase == PHASE_THROW_AIM:
                    _handle_throw_aim_click(sx, sy, game)
                    continue

                # ── Quick-use overlay clicks ─────────────────────────────────
                if game.phase == PHASE_QUICK_USE:
                    action = renderer.quick_use.handle_click(sx, sy, game)
                    if action == 'use':
                        item = renderer.quick_use.current_item(game)
                        if item:
                            if getattr(game, "quick_use_cat", "") == "throw":
                                game.phase = PHASE_PLAYING
                                game.begin_throw_aim(item)
                            else:
                                msg, col = game.use_item(item)
                                game.log.add(msg, col)
                                # use_item may have set PHASE_WAND_AIM/THROW_AIM
                                if game.phase == PHASE_QUICK_USE:
                                    game.phase = PHASE_PLAYING
                        else:
                            game.phase = PHASE_PLAYING
                    elif action == 'close':
                        game.phase = PHASE_PLAYING
                    continue

                # ── Inventory clicks ─────────────────────────────────────────
                if game.phase == PHASE_INVENTORY:
                    action = renderer.inv_scr.handle_click(sx, sy, game)
                    inv = renderer.inv_scr
                    item = inv.current_item(game)
                    if action == 'identify':
                        _inv_identify(item, game)
                        if game.pending_identify == 0:
                            game.phase = PHASE_PLAYING
                    elif action == 'use':
                        _inv_use(item, inv, game)
                    elif action == 'throw':
                        if item and item.get("slot") == "throw":
                            game.phase = PHASE_PLAYING
                            game.begin_throw_aim(item)
                    elif action == 'equip':
                        _inv_equip(item, game)
                    elif action == 'drop':
                        _inv_drop(item, inv, game)
                    elif action == 'close':
                        game.phase = PHASE_PLAYING
                    continue

                # ── Death / Win overlay clicks ────────────────────────────────
                if game.phase in (PHASE_DEAD, PHASE_WIN):
                    action = renderer.overlay.handle_click(sx, sy)
                    if action == renderer.overlay.BTN_CLOSE:
                        game.phase = PHASE_TITLE
                    continue

                # ── Title screen buttons ──────────────────────────────────────
                if game.phase == PHASE_TITLE:
                    action = renderer.title_scr.handle_click(sx, sy)
                    if action == renderer.title_scr.BTN_NEW:
                        game, char_state = _action_new(game, char_state, renderer)
                    elif action == renderer.title_scr.BTN_OPEN:
                        game = _action_open(game, renderer)
                    elif action == renderer.title_scr.BTN_RESUME:
                        if getattr(game, '_had_game', False):
                            game.phase = PHASE_PLAYING
                        elif os.path.exists(RESUME_PATH):
                            try:
                                import os as _os
                                loaded = load_game(RESUME_PATH)
                                loaded._had_game = True
                                game = loaded
                                game.phase = PHASE_PLAYING
                            except Exception as e:
                                _error_dialog("Resume failed", str(e))
                    elif action == renderer.title_scr.BTN_QUIT:
                        if _action_quit(game, renderer):
                            running = False
                    continue

                # ── Dropdown item click (must check before title-bar hit) ─────
                if renderer.menubar.active:
                    item = renderer.menubar.hit_test_item(sx, sy)
                    if item:
                        action = item.get("action", "")
                        renderer.menubar.dismiss()
                        mouse_held = False

                        if action == "file_new":
                            game, char_state = _action_new(game, char_state, renderer)
                        elif action == "file_open":
                            game = _action_open(game, renderer)
                        elif action == "file_close":
                            game = _action_close(game, renderer)
                        elif action == "file_save":
                            _action_save(game)
                        elif action == "file_save_as":
                            _action_save_as(game)
                        elif action == "file_quit":
                            if _action_quit(game, renderer):
                                running = False

                        # ── Control menu ─────────────────────────────────────
                        elif action == "ctrl_pickup_mode":
                            game.pickup_mode = not game.pickup_mode
                            state = "ON" if game.pickup_mode else "OFF"
                            game.log.add(f"Pickup Mode: {state}.", (200,200,200))

                        elif action == "ctrl_pause":
                            game.toggle_pause()

                        elif action == "ctrl_status":
                            pass   # stub — future

                        # ── Use menu: quick-use for consumables; inventory for gear ──
                        elif action in ("use_potion","use_scroll","use_wand",
                                        "use_food","use_wear_armor","use_wear_ring",
                                        "use_wield","use_remove_armor",
                                        "use_remove_rings","use_remove_weapon",
                                        "use_throw"):
                            from constants import (IC_POTION, IC_SCROLL, IC_WAND,
                                                   IC_FOOD, IC_ARMOR, IC_RING, IC_WEAPON)
                            # Consumables → compact quick-use overlay
                            _quick_cats = {
                                "use_potion": IC_POTION,
                                "use_scroll": IC_SCROLL,
                                "use_wand":   IC_WAND,
                                "use_food":   IC_FOOD,
                            }
                            # Gear → full inventory filtered
                            _gear_cats = {
                                "use_wear_armor":   IC_ARMOR,
                                "use_wear_ring":    IC_RING,
                                "use_wield":        IC_WEAPON,
                                "use_remove_armor": IC_ARMOR,
                                "use_remove_rings": IC_RING,
                                "use_remove_weapon":IC_WEAPON,
                                "use_throw":        IC_WEAPON,
                            }
                            if action in _quick_cats:
                                _open_quick_use(_quick_cats[action], game, renderer)
                            elif action == "use_throw":
                                # Throw: open missile quick-select overlay
                                throw_items = [it for it in game.player.inventory
                                               if it.get("slot") == "throw"]
                                if throw_items:
                                    _open_throw_select(game, renderer)
                                else:
                                    game.log.add("You have nothing to throw.", (180, 180, 180))
                            else:
                                fcat  = _gear_cats.get(action)
                                items = [it for it in game.player.inventory
                                         if it.get("cat") == fcat] if fcat else []
                                renderer.inv_scr.selected = (
                                    game.player.inventory.index(items[0])
                                    if items else 0)
                                game.phase = PHASE_INVENTORY

                        # ── Inventory menu ─────────────────────────────────────
                        elif action == "inv_get_item":
                            # Force-pick items at player tile (ignores pickup_mode)
                            if getattr(game, 'player', None):
                                game.pick_up_forced()

                        elif action == "inv_open":
                            renderer.inv_scr.selected = 0
                            game.phase = PHASE_INVENTORY

                        elif action == "inv_drop_item":
                            renderer.inv_scr.selected = 0
                            game.phase = PHASE_INVENTORY

                        elif action == "inv_drop_scrolls_potions":
                            from constants import IC_POTION, IC_SCROLL
                            game.drop_by_categories({IC_POTION, IC_SCROLL})

                        elif action == "inv_drop_rings_wands":
                            from constants import IC_RING, IC_WAND
                            game.drop_by_categories({IC_RING, IC_WAND})

                        elif action == "inv_drop_armor_weapons":
                            from constants import IC_ARMOR, IC_WEAPON
                            game.drop_by_categories({IC_ARMOR, IC_WEAPON})

                        elif action == "inv_drop_food_other":
                            from constants import IC_FOOD, IC_MISC
                            game.drop_by_categories({IC_FOOD, IC_MISC})

                        elif action == "inv_drop_all":
                            game.drop_all_items()

                        elif action == "inv_drop_last":
                            game.drop_last_pickup()

                        continue
                    elif sy > MENU_H:
                        # Click outside dropdown — dismiss
                        renderer.menubar.dismiss()

                # ── Menu bar title click ──────────────────────────────────────
                if sy < MENU_H:
                    renderer.menubar.click_title(sx, sy)
                    mouse_held = False

                # ── Viewport movement click ───────────────────────────────────
                elif (RECT_MAP[0] <= sx < RECT_MAP[0] + VP_PX and
                      RECT_MAP[1] <= sy < RECT_MAP[1] + VP_PX and
                      game.phase == PHASE_PLAYING and
                      not game.paused and
                      not renderer.menubar.active):
                    vx = sx - RECT_MAP[0]
                    vy = sy - RECT_MAP[1]
                    d  = _viewport_direction(vx, vy)
                    if d != (0, 0):
                        game.try_move(*d)
                        mouse_dir     = d
                        mouse_held    = True
                        mouse_next_ms = now + _MOUSE_INITIAL_DELAY_MS

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_held = False
                mouse_dir  = (0, 0)

            elif event.type == pygame.KEYDOWN:
                renderer.menubar.dismiss()
                key  = event.key
                mods = pygame.key.get_mods()

                if key == pygame.K_q and game.phase in (PHASE_TITLE, PHASE_DEAD, PHASE_WIN):
                    if _check_unsaved(game):
                        running = False

                elif game.phase == PHASE_TITLE:
                    if key == pygame.K_RETURN:
                        char_state = fresh_char_state()
                        game.phase = PHASE_CHAR_CREATE

                elif game.phase == PHASE_CHAR_CREATE:
                    _handle_char_create(key, event.unicode, char_state, game)

                elif game.phase == PHASE_PLAYING:
                    if key == pygame.K_i:
                        renderer.inv_scr.selected = 0
                        game.phase = PHASE_INVENTORY
                    elif key == pygame.K_g and not (mods & pygame.KMOD_CTRL):
                        # Get an Item (force-pickup ignoring pickup_mode)
                        if getattr(game, 'player', None):
                            game.pick_up_forced()
                    elif key == pygame.K_l and not (mods & pygame.KMOD_CTRL):
                        # Drop Last Items Picked Up
                        if getattr(game, 'player', None):
                            game.drop_last_pickup()
                    elif key == pygame.K_t and not (mods & pygame.KMOD_CTRL):
                        # Throw — always open missile quick-select overlay
                        if getattr(game, 'player', None):
                            throw_items = [it for it in game.player.inventory
                                           if it.get("slot") == "throw"]
                            if throw_items:
                                _open_throw_select(game, renderer)
                            else:
                                game.log.add("You have nothing to throw.", (180, 180, 180))
                    else:
                        _handle_playing(key, mods, game, renderer)

                elif game.phase == PHASE_INVENTORY:
                    _handle_inventory(key, mods, game, renderer)

                elif game.phase == PHASE_WISH:
                    _handle_wish(key, event.unicode, game)

                elif game.phase == PHASE_QUICK_USE:
                    should_close = renderer.quick_use.handle_key(key, game)
                    # handle_key for throw mode calls begin_throw_aim → phase=THROW_AIM
                    # so only revert to PLAYING if we're still in QUICK_USE
                    if should_close and game.phase == PHASE_QUICK_USE:
                        game.phase = PHASE_PLAYING

                elif game.phase == PHASE_WAND_AIM:
                    _handle_wand_aim_key(key, game)
                elif game.phase == PHASE_THROW_AIM:
                    _handle_throw_aim_key(key, game)

                elif game.phase in (PHASE_DEAD, PHASE_WIN):
                    if key == pygame.K_r or key == pygame.K_ESCAPE:
                        game.phase = PHASE_TITLE

        # Mark that a game is in progress (for Resume button on title screen)
        if game.phase in (PHASE_PLAYING, PHASE_INVENTORY, PHASE_WISH, PHASE_QUICK_USE,
                              PHASE_WAND_AIM, PHASE_THROW_AIM):
            game._had_game = True

        # ── Hall of Fame submission (fires exactly once per run end) ──────────
        if game.phase in (PHASE_DEAD, PHASE_WIN) and not game._hof_submitted:
            from engine.hof import submit_entry as _hof_submit
            game.hof_result     = _hof_submit(game)
            game._hof_submitted = True
            # Hero: delete resume slot — the run is over
            if getattr(game, "difficulty", DIFF_ADVENTURER) == DIFF_HERO:
                import os as _os
                try:    _os.remove(RESUME_PATH)
                except OSError: pass

        renderer.render(game, char_state)

    pygame.quit()
    sys.exit(0)


# ── Character creation input ───────────────────────────────────────────────────

def _handle_char_create(key, unicode_char, state: dict, game: GameState):
    cur = state["cursor_on"]
    if key == pygame.K_ESCAPE:
        game.phase = PHASE_TITLE; return
    if key == pygame.K_TAB:
        state["cursor_on"] = "class" if cur == "name" else "name"; return
    if cur == "name":
        if key == pygame.K_BACKSPACE:
            state["name"] = state["name"][:-1]
        elif key == pygame.K_RETURN:
            if state["name"].strip(): state["cursor_on"] = "class"
        elif unicode_char and unicode_char.isprintable() and len(state["name"]) < 16:
            state["name"] += unicode_char
    elif cur == "class":
        n = len(CLASS_ORDER)
        if key in (pygame.K_UP, pygame.K_k):
            state["selected_class"] = (state["selected_class"] - 1) % n
            state["cursor_on"] = "name"
        elif key in (pygame.K_DOWN, pygame.K_j):
            state["selected_class"] = (state["selected_class"] + 1) % n
            state["cursor_on"] = "name"
        elif key == pygame.K_RETURN:
            name = state["name"].strip() or "Adventurer"
            cls  = CLASS_ORDER[state["selected_class"]]
            diff = state.get("difficulty", DIFF_ADVENTURER)
            game.start_new_game(name, cls, diff)


# ── Playing keyboard input ────────────────────────────────────────────────────

_ORIG_KEYS = {
    pygame.K_o: ( 0,-1), pygame.K_p: (1,-1),
    pygame.K_k: (-1, 0), pygame.K_SEMICOLON: (1, 0),
    pygame.K_COMMA: (-1,1), pygame.K_PERIOD: (0,1), pygame.K_SLASH: (1,1),
}
_ARROW_KEYS = {
    pygame.K_UP: (0,-1), pygame.K_DOWN: (0,1),
    pygame.K_LEFT: (-1,0), pygame.K_RIGHT: (1,0),
}
_WASD_KEYS = {
    pygame.K_w: (0,-1), pygame.K_s: (0,1),
    pygame.K_a: (-1,0), pygame.K_d: (1,0),
}
_NUMPAD_KEYS = {
    pygame.K_KP7: (-1,-1), pygame.K_KP8: (0,-1), pygame.K_KP9: (1,-1),
    pygame.K_KP4: (-1, 0),                        pygame.K_KP6: (1, 0),
    pygame.K_KP1: (-1, 1), pygame.K_KP2: (0, 1),  pygame.K_KP3: (1, 1),
}
_VI_KEYS = {
    pygame.K_y: (-1,-1), pygame.K_u: (1,-1),
    pygame.K_h: (-1, 0), pygame.K_l: (1, 0),
    pygame.K_b: (-1, 1), pygame.K_n: (1, 1),
}


# ── 8-directional wand aim helpers ────────────────────────────────────────────

# Direction maps for every common key scheme
_WAND_KEY_DIRS = {
    # Numpad
    pygame.K_KP1: (-1,  1), pygame.K_KP2: ( 0,  1), pygame.K_KP3: ( 1,  1),
    pygame.K_KP4: (-1,  0),                          pygame.K_KP6: ( 1,  0),
    pygame.K_KP7: (-1, -1), pygame.K_KP8: ( 0, -1), pygame.K_KP9: ( 1, -1),
    # hjkl + diagonals
    pygame.K_h:   (-1,  0), pygame.K_l: (1,  0),
    pygame.K_k:   ( 0, -1), pygame.K_j: (0,  1),
    pygame.K_y:   (-1, -1), pygame.K_u: (1, -1),
    pygame.K_b:   (-1,  1), pygame.K_n: (1,  1),
    # Arrow keys (cardinals only)
    pygame.K_LEFT:  (-1, 0), pygame.K_RIGHT: (1, 0),
    pygame.K_UP:    ( 0,-1), pygame.K_DOWN:  (0, 1),
}

def _handle_wand_aim_key(key: int, game):
    """Handle a keypress while in PHASE_WAND_AIM."""
    from engine.game import PHASE_PLAYING
    if key == pygame.K_ESCAPE:
        game.pending_wand = None
        game.phase = PHASE_PLAYING
        game.log.add("You lower the wand.", (180, 180, 180))
        return
    direction = _WAND_KEY_DIRS.get(key)
    if direction:
        game.aim_wand(*direction)


def _handle_wand_aim_click(sx: int, sy: int, game):
    """Handle a mouse click in the viewport while in PHASE_WAND_AIM.
    Converts click position relative to player's screen tile to a direction."""
    from engine.game import PHASE_PLAYING
    from constants import MENU_H, TILE, VIEW_HALF

    # Click in viewport? (RECT_MAP = (0, MENU_H, VP_PX, VP_PX))
    vx = sx;  vy = sy - MENU_H
    if not (0 <= vx < VIEW_HALF * 2 * TILE + TILE and
            0 <= vy < VIEW_HALF * 2 * TILE + TILE):
        # Outside map — cancel
        game.pending_wand = None
        game.phase = PHASE_PLAYING
        game.log.add("You lower the wand.", (180, 180, 180))
        return

    # Player centre in viewport pixels
    pcx = VIEW_HALF * TILE + TILE // 2
    pcy = VIEW_HALF * TILE + TILE // 2
    dsx = vx - pcx
    dsy = vy - pcy

    if abs(dsx) < TILE // 4 and abs(dsy) < TILE // 4:
        return   # too close to player — wait for clearer input

    # Snap to nearest octant
    import math
    angle = math.atan2(dsy, dsx)   # radians, right=0, down=+π/2
    octant = round(angle / (math.pi / 4)) % 8
    # octant 0=right, 1=down-right, 2=down, 3=down-left,
    #        4=left,  5=up-left,    6=up,   7=up-right
    _OCT_DIRS = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
    dx, dy = _OCT_DIRS[octant]
    game.aim_wand(dx, dy)



# ── 8-directional throw aim helpers ──────────────────────────────────────────

def _open_throw_select(game, renderer):
    """Open the missile quick-select overlay (QuickUseScreen in throw mode)."""
    renderer.quick_use.selected = 0
    game.quick_use_cat = "throw"
    game.phase = PHASE_QUICK_USE


def _handle_throw_aim_key(key: int, game):
    """Handle a keypress while in PHASE_THROW_AIM."""
    from engine.game import PHASE_PLAYING
    if key == pygame.K_ESCAPE:
        game.pending_throw = None
        game.phase = PHASE_PLAYING
        game.log.add("You lower your arm.", (180, 180, 180))
        return
    direction = _WAND_KEY_DIRS.get(key)   # reuse same 8-dir map
    if direction:
        game.aim_throw(*direction)


def _handle_throw_aim_click(sx: int, sy: int, game):
    """Handle a mouse click in the viewport while in PHASE_THROW_AIM."""
    from engine.game import PHASE_PLAYING
    from constants import MENU_H, TILE, VIEW_HALF

    vx = sx;  vy = sy - MENU_H
    if not (0 <= vx < VIEW_HALF * 2 * TILE + TILE and
            0 <= vy < VIEW_HALF * 2 * TILE + TILE):
        game.pending_throw = None
        game.phase = PHASE_PLAYING
        game.log.add("You lower your arm.", (180, 180, 180))
        return

    pcx = VIEW_HALF * TILE + TILE // 2
    pcy = VIEW_HALF * TILE + TILE // 2
    dsx = vx - pcx
    dsy = vy - pcy

    if abs(dsx) < TILE // 4 and abs(dsy) < TILE // 4:
        return

    import math
    angle  = math.atan2(dsy, dsx)
    octant = round(angle / (math.pi / 4)) % 8
    _OCT_DIRS = [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
    dx, dy = _OCT_DIRS[octant]
    game.aim_throw(dx, dy)


def _open_quick_use(cat: str, game: GameState, renderer) -> bool:
    """Switch to PHASE_QUICK_USE for the given item category.
    Returns True if there are items of that type; False otherwise."""
    from constants import IC_POTION, IC_SCROLL, IC_WAND, IC_FOOD
    items = [it for it in game.player.inventory if it.get("cat") == cat]
    if not items:
        cat_names = {IC_POTION: "potions", IC_SCROLL: "scrolls",
                     IC_WAND: "wands", IC_FOOD: "food"}
        game.log.add(f"You have no {cat_names.get(cat, 'items')}.", (200, 160, 100))
        return False
    game.quick_use_cat = cat
    game.phase = PHASE_QUICK_USE
    return True


def _handle_playing(key: int, mods: int, game: GameState, renderer=None):
    ctrl = bool(mods & pygame.KMOD_CTRL)

    # ── Pause guard — only Space may pass when timer is frozen ────────────────
    if game.paused:
        if key == pygame.K_SPACE:
            game.toggle_pause()
        return

    # ── Quick-use hotkeys (no modifier needed) ────────────────────────────────
    if renderer:
        from constants import (IC_POTION, IC_SCROLL, IC_WAND, IC_FOOD,
                               IC_ARMOR, IC_RING, IC_WEAPON)
        if key == pygame.K_q and not ctrl:
            _open_quick_use(IC_POTION, game, renderer); return
        elif key == pygame.K_r and not ctrl:
            _open_quick_use(IC_SCROLL, game, renderer); return
        elif key == pygame.K_z and not ctrl:
            _open_quick_use(IC_WAND,   game, renderer); return
        elif key == pygame.K_e and not ctrl:
            _open_quick_use(IC_FOOD,   game, renderer); return
        # Gear items → full inventory (filtered)
        elif ctrl and key in (pygame.K_u, pygame.K_j, pygame.K_m,
                     pygame.K_y, pygame.K_h, pygame.K_n):
            _cat_map = {pygame.K_u: IC_ARMOR, pygame.K_j: IC_RING,
                        pygame.K_m: IC_WEAPON, pygame.K_y: IC_ARMOR,
                        pygame.K_h: IC_RING,   pygame.K_n: IC_WEAPON}
            fcat  = _cat_map[key]
            items = [it for it in game.player.inventory if it.get("cat") == fcat]
            renderer.inv_scr.selected = (
                game.player.inventory.index(items[0]) if items else 0)
            game.phase = PHASE_INVENTORY; return

    for mapping in (_ORIG_KEYS, _ARROW_KEYS, _WASD_KEYS, _NUMPAD_KEYS, _VI_KEYS):
        if key in mapping:
            game.try_move(*mapping[key])
            return
    if key in (pygame.K_SPACE,):
        game.toggle_pause()
    elif key == pygame.K_KP5:
        game.rest()
    elif key == pygame.K_s and ctrl:
        _action_save(game)


def _handle_inventory(key: int, mods: int, game: GameState, renderer):
    """Handle all keypresses while the inventory overlay is open."""
    inv = renderer.inv_scr
    from constants import IC_WEAPON, IC_ARMOR, IC_RING, IC_POTION, IC_SCROLL, IC_WAND, IC_FOOD

    # ── Fixed action keys — checked FIRST so they don't fall through to letter-select ──
    if key in (pygame.K_ESCAPE, pygame.K_i):
        game.phase = PHASE_PLAYING; return

    if key in (pygame.K_UP, pygame.K_k):
        inv.navigate(-1, game); return
    if key in (pygame.K_DOWN, pygame.K_j):
        inv.navigate(+1, game); return

    item = inv.current_item(game)

    if key in (pygame.K_u, pygame.K_RETURN):
        _inv_use(item, inv, game); return

    if key == pygame.K_e:
        _inv_equip(item, game); return

    if key == pygame.K_d:
        _inv_drop(item, inv, game); return

    # ── Letter-select (only keys not claimed above) ────────────────────────────
    # Excluded: i(close) k(up) j(down) u(use) e(equip) d(drop)
    _ACTION_KEYS = {pygame.K_i, pygame.K_k, pygame.K_j,
                    pygame.K_u, pygame.K_e, pygame.K_d,
                    pygame.K_ESCAPE, pygame.K_RETURN}
    if pygame.K_a <= key <= pygame.K_z and key not in _ACTION_KEYS:
        inv.select_by_letter(chr(key), game)
        # If in identify mode, identify on letter-select
        if game.pending_identify > 0:
            _inv_identify(inv.current_item(game), game)
        return



def _inv_use(item, inv, game):
    from constants import IC_POTION, IC_SCROLL, IC_FOOD, IC_WAND
    from engine.game import PHASE_PLAYING
    if item is None:
        return
    # Identify mode intercepts any action
    if game.pending_identify > 0:
        _inv_identify(item, game); return
    cat = item.get("cat","")
    if cat in (IC_POTION, IC_SCROLL, IC_FOOD, IC_WAND):
        msg, col = game.use_item(item)
        game.log.add(msg, col)
        items = inv._build_list(game)
        inv.selected = min(inv.selected, max(0, len(items)-1))
        # Close inventory — but if use_item opened PHASE_WAND_AIM, preserve it
        if game.phase not in (PHASE_WAND_AIM,):
            game.phase = PHASE_PLAYING
    else:
        game.log.add("You can't use that here.", (150,150,150))


def _inv_equip(item, game):
    from constants import IC_WEAPON, IC_ARMOR, IC_RING
    if item is None:
        return
    if game.pending_identify > 0:
        _inv_identify(item, game); return
    cat = item.get("cat","")
    if cat in (IC_WEAPON, IC_ARMOR, IC_RING):
        msg, col = game.equip_item(item)
        game.log.add(msg, col)
    else:
        game.log.add("You can't equip that.", (150,150,150))


def _inv_drop(item, inv, game):
    if item is None:
        return
    msg, col = game.drop_item(item)
    game.log.add(msg, col)
    items = inv._build_list(game)
    inv.selected = min(inv.selected, max(0, len(items)-1))


def _inv_identify(item, game):
    if item is None or game.pending_identify <= 0:
        return
    iid = item.get("item_id", item.get("id", ""))
    game.identified.add(iid)
    item["enchant_known"] = True   # exact enchant now known
    item.pop("fuzzy_enchant", None)   # discard the guess — no more ?
    game.pending_identify -= 1
    nm = game.item_display_name(item)
    game.log.add(f"Identified: {nm}.", (50, 50, 200))
    if game.pending_identify == 0:
        game.log.add("Identify scroll exhausted.", (150, 150, 150))


def _handle_wish(key: int, unicode_char: str, game: GameState):
    """Handle keypresses in the wish popup."""
    from engine.effects import resolve_wish

    if key == pygame.K_ESCAPE:
        game.log.add("You choose not to make a wish.", (150, 150, 150))
        game.phase = PHASE_PLAYING
        return

    if key == pygame.K_RETURN:
        text = getattr(game, "wish_input", "").strip()
        if text:
            msg, col = resolve_wish(game, text)
            game.log.add(msg, col)
        else:
            game.log.add("Your wish fades without form.", (150, 150, 150))
        game.wish_input = ""
        game.phase = PHASE_PLAYING
        return

    if key == pygame.K_BACKSPACE:
        wi = getattr(game, "wish_input", "")
        game.wish_input = wi[:-1]
        return

    if unicode_char and unicode_char.isprintable():
        game.wish_input = getattr(game, "wish_input", "") + unicode_char



if __name__ == "__main__":
    main()
