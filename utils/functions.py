#!/usr/bin/env python

import os
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import PIL
from arcade import Texture
from arcade.arcade_types import Color, RGB, RGBA
from shapely import speedups

from .colors import colors_names
from .geometry import clamp

SEPARATOR = '-' * 20

speedups.enable()


def get_screen_size() -> Tuple:
    from PIL import ImageGrab
    screen = ImageGrab.grab()
    return int(screen.width), int(screen.height)


def filter_sequence(sequence: Sequence,
                    filtered_class: Any) -> List[Any]:
    return [s for s in sequence if isinstance(s, filtered_class)]


def first_object_of_type(iterable: Iterable, class_name: type(object)):
    """
    Search the <iterable> for first instance of object which class is named
    <class_name>.
    """
    for obj in iterable:
        if isinstance(obj, class_name):
            return obj


def get_attributes_with_attribute(instance: object, name: str,
                                  ignore: Tuple = ()) -> List[Any]:
    """
    Search all attributes of <instance> to find all objects which have their
    own attribute of <name> and return these objects as List. You can also add
    a Tuple od class names to be ignored during query.
    """
    attributes = instance.__dict__.values()
    return [
        attr for attr in attributes if hasattr(attr, name) and not isinstance(attr, ignore)
    ]


@lru_cache
def get_path_to_file(filename: str) -> str:
    """
    Build full absolute path to the filename and return it + /filename.
    """
    for directory in os.walk(os.getcwd()):
        if filename in directory[2]:
            return f'{directory[0]}/{filename}'


def get_object_name(filename: str) -> str:
    """
    Retrieve raw name of a GameObject from the absolute path to it's texture.
    """
    name_with_extension = remove_path_from_name(filename)
    return name_with_extension.split('.', 1)[0]


def remove_path_from_name(filename):
    return filename.rsplit('/', 1)[1]


def object_name_to_filename(object_name: str) -> str:
    return '.'.join((object_name, '.png'))


def find_paths_to_all_files_of_type(extension: str,
                                    base_directory: str) -> Dict[str, str]:
    """
    Find and return a Dict containing all dirs where files with 'extension' are
    found.
    """
    names_to_paths = {}
    for directory in os.walk(os.path.abspath(base_directory)):
        for file_name in (f for f in directory[2] if f.endswith(extension)):
            names_to_paths[file_name] = directory[0]
    return names_to_paths


def add_player_color_to_name(name: str, color: Color) -> str:
    splitted = name.split('.')
    color = colors_names[color]
    return f'{splitted[0]}_{color}.{splitted[1]}'


def decolorized_name(name: str) -> str:
    for color in ('red', 'green', 'blue', 'yellow'):
        if color in name:
            return name.rsplit('_', 1)[0]
    return name


def to_texture_name(name: str) -> str:
    if '.png' not in name:
        return name + '.png'
    return name


def get_enemies(war: int) -> Tuple[int, int]:
    """
    Since each Player id attribute is a power of 2, id's can
    be combined to sum, being an unique identifier, for eg.
    Player with id 8 and Player with id 128 make unique sum
    136. To save pairs of hostile Players you can sum their
    id's and this functions allows to retrieve pair from the
    saved value. Limit of Players in game is 16, since 2^32
    gives 8589934592, which is highest id checked by functions.
    """
    index = 8589934592  # 2 to power of 32
    while index > 2:
        if war < index:
            index = index >> 1
        else:
            break
    return index, war - index


def to_rgba(color: RGB, alpha: int) -> RGBA:
    return color[0], color[1], color[2], clamp(alpha, 255, 0)


def make_texture(width: int, height: int, color: Color) -> Texture:
    """
    Return a :class:`Texture` of a square with the given diameter and color,
    fading out at its edges.

    :param int size: Diameter of the square and dimensions of the square
    Texture returned.
    :param Color color: Color of the square.
    :param int center_alpha: Alpha value of the square at its center.
    :param int outer_alpha: Alpha value of the square at its edges.

    :returns: New :class:`Texture` object.
    """
    img = PIL.Image.new("RGBA", (width, height), color)
    name = "{}:{}:{}:{}".format("texture_rect", width, height, color)
    return Texture(name, img)


def ignore_in_editor_mode(func):
    def wrapper(self, *args, **kwargs):
        if self.game.settings.editor_mode:
            return
        return func(self, *args, **kwargs)
    return wrapper


def ignore_in_menu(func):
    def wrapper(self, *args, **kwargs):
        if not self.window.is_game_running:
            return
        return func(self, *args, **kwargs)
    return wrapper
