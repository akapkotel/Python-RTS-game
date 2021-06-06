#!/usr/bin/env python

from typing import Set

from arcade import Window
from arcade.key import *

from user_interface.user_interface import ToggledElement
from utils.logging import log, logger


class KeyboardHandler(ToggledElement):
    keys_pressed: Set[int] = set()

    def __init__(self, window: Window):
        super().__init__()
        self.window = window

    @logger(console=True)
    def on_key_press(self, symbol: int, modifiers: int):
        self.keys_pressed.add(symbol)
        log(f'Pressed key: {symbol}, all pressed keys: {self.keys_pressed}')
        self.evaluate_pressed_key(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol == LCTRL:
            self.window.game_view.pathfinder.finish_waypoints_queue()
        self.keys_pressed.discard(symbol)

    def evaluate_pressed_key(self, symbol: int, modifiers: int):
        if symbol == P and self.window.game_view is not None:
            self.window.game_view.toggle_pause()
        elif symbol == S and self.window.is_game_running:
            self.window.save_game()
        elif symbol == L:
            self.window.load_game()
        elif symbol == ESCAPE:
            self.on_escape_pressed()
        elif (digit := chr(symbol)).isdigit():
            self.on_numeric_key_press(int(digit))

    def on_escape_pressed(self):
        game = self.window.game_view
        if game is None or not game.is_running:
            self.window.close()
        elif game.current_mission.ended:
            game.current_mission.quit_mission()
        else:
            self.window.show_view(self.window.menu_view)

    def on_numeric_key_press(self, digit: int):
        manager = self.window.cursor.units_manager
        if LCTRL in self.keys_pressed:
            manager.create_new_permanent_units_group(digit)
        else:
            manager.select_permanent_units_group(digit)

    @staticmethod
    def key_to_letter(symbol: int) -> str:
        return chr(symbol)
