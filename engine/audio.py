# engine/audio.py — Dungeon of Doom Audio Manager
# v0.500.20260405
#
# Manages all sound effects and background music for the game.
#
# ── Asset placement ──────────────────────────────────────────────────────────
#
#   Drop audio files into the corresponding subdirectory of assets/sounds/:
#
#   assets/sounds/sfx/            ← short sound effects (.wav or .ogg)
#   assets/sounds/music/          ← background music loops (.ogg recommended)
#
# ── SFX reference (filename → event) ────────────────────────────────────────
#
#   hit_player.wav        Player takes damage from any source
#   hit_monster.wav       Player lands a hit on a monster
#   kill_monster.wav      Monster is slain
#   player_death.wav      Player dies
#   level_up.wav          Player gains an XP level
#   pickup.wav            Item picked up from floor
#   equip.wav             Item equipped or unequipped
#   drink_potion.wav      Potion consumed
#   read_scroll.wav       Scroll read
#   zap_wand.wav          Wand fired
#   eat_food.wav          Food eaten
#   stairs_down.wav       Player descends a staircase
#   stairs_up.wav         Player ascends a staircase
#   victory.wav           Player escapes with the Orb of Carnos
#   gate_keeper.wav       Gate Keeper spawns on the current floor
#   boulder_push.wav      Boulder pushed
#   curse_blocked.wav     Cursed item prevents action
#   remove_curse.wav      Scroll of Remove Curse used
#   wand_empty.wav        Wand out of charges
#   potion_bad.wav        Cursed / harmful potion consumed
#
# ── Music reference (filename → when played) ─────────────────────────────────
#
#   title_theme.ogg       Title screen — loops until new game starts
#   dungeon_ambient.ogg   Floors 1–39 — loops continuously while playing
#   boss_floor.ogg        Floor 40 (Dark Wizard) — replaces ambient
#   victory_theme.ogg     Victory overlay
#   death_theme.ogg       Death overlay
#
# ── Volume / mute ────────────────────────────────────────────────────────────
#
#   All volumes are 0.0–1.0.  Default: SFX 0.8, music 0.45.
#   Muting silences both channels without stopping playback position.
#   Settings are NOT persisted between sessions in this version.
#
# ── Placeholder behaviour ────────────────────────────────────────────────────
#
#   Missing audio files are silently ignored — the game runs normally with no
#   sound until assets are added. No errors are raised for missing files.

import os
import pygame

# Path to the sounds directory relative to this file (engine/audio.py)
_SOUNDS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
)
_SFX_DIR   = os.path.join(_SOUNDS_DIR, "sfx")
_MUSIC_DIR = os.path.join(_SOUNDS_DIR, "music")

# Supported audio extensions tried in order when loading SFX
_SFX_EXTS = (".wav", ".ogg", ".mp3")


class AudioManager:
    """
    Central audio controller. One instance lives on GameState as `game.audio`.

    Usage:
        game.audio.play("hit_player")
        game.audio.play_music("dungeon_ambient")
        game.audio.pause_music()
        game.audio.resume_music()
    """

    # ── Class-level defaults ──────────────────────────────────────────────────
    DEFAULT_SFX_VOLUME   = 0.80
    DEFAULT_MUSIC_VOLUME = 0.45
    NUM_CHANNELS         = 8      # concurrent SFX channels

    def __init__(self):
        self._ready        = False   # True once mixer initialised successfully
        self._sfx:  dict   = {}      # name → pygame.mixer.Sound
        self._mute         = False
        self._sfx_vol      = self.DEFAULT_SFX_VOLUME
        self._music_vol    = self.DEFAULT_MUSIC_VOLUME
        self._current_music: str = ""   # track name currently loaded/playing

        self._init_mixer()
        if self._ready:
            self._load_all_sfx()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_mixer(self):
        """Initialise pygame.mixer with preferred settings."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(self.NUM_CHANNELS)
            self._ready = True
        except Exception as e:
            print(f"[Audio] Mixer init failed ({e}). Running silently.")

    def _load_all_sfx(self):
        """
        Pre-load every SFX file found in assets/sounds/sfx/.
        The sound name is the filename without extension.
        Missing files are silently skipped.
        """
        if not os.path.isdir(_SFX_DIR):
            return
        for fname in os.listdir(_SFX_DIR):
            name, ext = os.path.splitext(fname)
            if ext.lower() in _SFX_EXTS:
                self._load_sfx(name, os.path.join(_SFX_DIR, fname))

    def _load_sfx(self, name: str, path: str):
        """Load a single SFX file into the cache."""
        try:
            snd = pygame.mixer.Sound(path)
            snd.set_volume(self._sfx_vol)
            self._sfx[name] = snd
        except Exception as e:
            print(f"[Audio] Could not load SFX '{name}' from {path}: {e}")

    # ── SFX playback ──────────────────────────────────────────────────────────

    def play(self, name: str):
        """
        Play a sound effect by name (filename without extension).
        No-ops silently if the file is missing, mixer is not ready, or muted.
        """
        if not self._ready or self._mute:
            return
        snd = self._sfx.get(name)
        if snd:
            snd.play()

    def stop_all_sfx(self):
        """Stop all currently playing sound effects."""
        if self._ready:
            pygame.mixer.stop()

    # ── Music playback ────────────────────────────────────────────────────────

    def play_music(self, name: str, loops: int = -1, fade_ms: int = 1500):
        """
        Stream background music by name (filename without extension).
        Searches assets/sounds/music/ for .ogg, .mp3, .wav in that order.
        If the requested track is already playing, does nothing.
        Uses a fade-in for smooth transitions.
        """
        if not self._ready:
            return
        if name == self._current_music and pygame.mixer.music.get_busy():
            return

        path = self._find_music_file(name)
        if path is None:
            return   # file not present — silent placeholder

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.0 if self._mute else self._music_vol)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self._current_music = name
        except Exception as e:
            print(f"[Audio] Could not play music '{name}': {e}")

    def stop_music(self, fade_ms: int = 800):
        """Fade out and stop the current music track."""
        if self._ready and pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
        self._current_music = ""

    def pause_music(self):
        """Pause music (e.g. when game timer is paused)."""
        if self._ready:
            pygame.mixer.music.pause()

    def resume_music(self):
        """Resume paused music."""
        if self._ready:
            pygame.mixer.music.unpause()

    def _find_music_file(self, name: str) -> str | None:
        """Return the path to a music file, trying .ogg / .mp3 / .wav."""
        if not os.path.isdir(_MUSIC_DIR):
            return None
        for ext in (".ogg", ".mp3", ".wav"):
            path = os.path.join(_MUSIC_DIR, name + ext)
            if os.path.isfile(path):
                return path
        return None

    # ── Volume & mute ─────────────────────────────────────────────────────────

    @property
    def sfx_volume(self) -> float:
        return self._sfx_vol

    @sfx_volume.setter
    def sfx_volume(self, value: float):
        self._sfx_vol = max(0.0, min(1.0, value))
        for snd in self._sfx.values():
            snd.set_volume(0.0 if self._mute else self._sfx_vol)

    @property
    def music_volume(self) -> float:
        return self._music_vol

    @music_volume.setter
    def music_volume(self, value: float):
        self._music_vol = max(0.0, min(1.0, value))
        if self._ready and not self._mute:
            pygame.mixer.music.set_volume(self._music_vol)

    @property
    def muted(self) -> bool:
        return self._mute

    @muted.setter
    def muted(self, value: bool):
        self._mute = value
        if self._ready:
            # SFX: update cached volumes
            for snd in self._sfx.values():
                snd.set_volume(0.0 if value else self._sfx_vol)
            # Music: set volume immediately
            pygame.mixer.music.set_volume(0.0 if value else self._music_vol)

    def toggle_mute(self):
        """Flip mute state. Returns new muted state."""
        self.muted = not self._mute
        return self._mute

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def quit(self):
        """Release mixer resources. Called on game exit."""
        if self._ready:
            try:
                pygame.mixer.quit()
            except Exception:
                pass


# ── Module-level singleton ────────────────────────────────────────────────────
# Imported directly by any module that needs to fire a sound without holding
# a reference to GameState (e.g. entities/player.py for level-up).

_instance: AudioManager | None = None


def get_audio() -> AudioManager:
    """Return the global AudioManager instance (created lazily on first call)."""
    global _instance
    if _instance is None:
        _instance = AudioManager()
    return _instance


def init_audio() -> AudioManager:
    """
    Explicitly initialise (or reinitialise) the global AudioManager.
    Call once from main() after pygame.init().
    Returns the instance.
    """
    global _instance
    _instance = AudioManager()
    return _instance
