#!/usr/bin/env python
from __future__ import annotations

import pyglet

from typing import Dict, Optional
from pyglet.media import Player
from pyglet.media.codecs.base import Source, StaticSource

from utils.classes import Singleton
from utils.functions import find_paths_to_all_files_of_type, log

SOUNDS_DIRECTORY = 'resources/sounds'
SOUNDS_EXTENSION = 'wav'

load_source = pyglet.media.load


class SoundPlayer(Singleton):
    """
    SoundPlayer based on pyglet. Allows playing both long, background music
    themes and short sound effects.
    """

    def __init__(self,
                 sounds_directory: str = SOUNDS_DIRECTORY,
                 sound_on: bool = True,
                 music_on: bool = True,
                 sound_effects_on: bool = True):
        """
        SoundPlayer is a singleton.

        :param sounds_directory: str -- name of the directory without path
        :param sound_on: bool -- if sounds should be played or not
        """
        self.sounds: Dict[str, Source] = self._preload_sounds(sounds_directory)
        log(f'Loaded {len(self.sounds)} sounds.', True)

        self.currently_played: Dict[str, Player] = {}

        self.current_music: Optional[str] = None

        self._sound_on = sound_on
        self._music_on = music_on
        self._sound_effects_on = sound_effects_on

        self.volume: float = 1.0
        self.music_volume: float = self.volume
        self.effects_volume: float = self.volume

    @staticmethod
    def _preload_sounds(sounds_directory=None) -> Dict[str, Source]:
        names_to_paths = find_paths_to_all_files_of_type(SOUNDS_EXTENSION,
                                                         sounds_directory)
        return {
            name: load_source(f'{path}/{name}', streaming=False) for
            name, path in names_to_paths.items()
        }

    @staticmethod
    def _create_sound_source(full_sound_path: str) -> Source:
        source = load_source(full_sound_path, streaming=False)
        return StaticSource(source)

    @property
    def sound_on(self) -> bool:
        return self._sound_on

    @sound_on.setter
    def sound_on(self, value: bool):
        self.play() if value else self.pause()

    @property
    def music_on(self) -> bool:
        return self._music_on

    @music_on.setter
    def music_on(self, value: bool):
        self._music_on = value
        for name, player in self.currently_played.items():
            if name == self.current_music:
                player.pause() if not value else player.play()

    def play_sound(self, name: str,
                   loop: bool = False,
                   volume: Optional[float] = None):
        """
        Play sound. If 'loop' is set to True, sound would be repeated until
        stopped. To loop background music themes please use 'play_music'
        method.
        """
        if not self.sound_on:
            return
        if volume is not None:
            self.volume = volume
        if (source := self.sounds.get(name)) is not None:
            self._play_sound(name, source, loop)

    def play_music(self, name: str, volume: Optional[float] = None):
        """
        Stop playing current music theme (if any is active) and start playing
        new music in loop.
        """
        if self._music_on:
            self.stop_sound(self.current_music)
            self.current_music = name
            self.play_sound(name, loop=True, volume=volume)

    def stop_sound(self, name: str):
        """Stop playing single sound, useful to stop playing music themes."""
        try:
            self.currently_played[name].delete()
            del self.currently_played[name]
            if self.current_music == name:
                self.current_music = None
        except KeyError:
            pass

    def pause(self):
        """Pause playing all currently played sounds and music. Reversible."""
        self._sound_on = False
        for player in self.currently_played.values():
            player.pause()

    def play(self):
        """Unpause playing all currently active sounds and music."""
        self._sound_on = True
        for player in self.currently_played.values():
            player.play()

    def clear(self):
        """Stop and remove all sounds and music currently played."""
        for player in self.currently_played.values():
            player.delete()

    def _play_sound(self, name: str, source: Source, loop: bool):
        if loop:
            self._create_looped_player_and_play(name, source)
        else:
            source.play()

    def _create_looped_player_and_play(self, name: str, source: Source):
        player = Player()
        player.queue(source)
        player.play()
        player.loop = True
        self.currently_played[name] = player
