#!/usr/bin/env python
from __future__ import annotations

import heapq
import random
import math
from math import hypot
from abc import ABC, abstractmethod

from collections import defaultdict
from typing import Optional, Tuple, Sequence, List, Dict, Set
from arcade import Sprite, Texture, load_texture, load_spritesheet

from data_types import Number, UnitId, BuildingId, NodeId
from utils.functions import timer, log, get_path_to_file, distance_2d
from game import Game, PROFILING_LEVEL
from enums import TerrainCost


PATH = 'PATH'
TILE_WIDTH = 60
TILE_HEIGHT = 60

# typing aliases:
GridPosition = SectorId = NormalizedPoint = Tuple[int, int]
MapPath = List[NormalizedPoint]


MAP_TEXTURES = {
    'mud': load_spritesheet(
        get_path_to_file('mud_tileset_6x6.png'), 60, 60, 4, 16, 0)
}


class GridHandler:
    adjacent_offsets = [
        (-1, -1), (-1, 0), (-1, +1), (0, +1), (0, -1), (+1, -1), (+1, 0),
        (+1, +1)
    ]

    @abstractmethod
    def position_to_node(self, x: Number, y: Number) -> MapNode:
        raise NotImplementedError

    @classmethod
    def position_to_grid(cls, x: Number, y: Number) -> GridPosition:
        """Return map-grid-normalised position."""
        return x // TILE_WIDTH, y // TILE_HEIGHT

    @classmethod
    def normalize_position(cls, x: Number, y: Number) -> NormalizedPoint:
        grid = cls.position_to_grid(int(x), int(y))
        return cls.grid_to_position(grid)

    @classmethod
    def grid_to_position(cls, grid: GridPosition) -> NormalizedPoint:
        """Return (x, y) position of the map-grid-normalised Node."""
        return (
            grid[0] * TILE_WIDTH + TILE_WIDTH // 2,
            grid[1] * TILE_HEIGHT + TILE_HEIGHT // 2
        )

    @classmethod
    def adjacent_grids(cls, x: Number, y: Number) -> List[GridPosition]:
        """Return list of map-normalised grid-positions adjacent to (x, y)."""
        grid = cls.position_to_grid(x, y)
        return [(grid[0] + p[0], grid[1] + p[1]) for p in cls.adjacent_offsets]

    @abstractmethod
    def in_bounds(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def adjacent_nodes(self, *args, **kwargs) -> List[MapNode]:
        raise NotImplementedError

    @abstractmethod
    def walkable_adjacent(self, *args, **kwargs) -> List[MapNode]:
        """Useful for pathfinding."""
        raise NotImplementedError

    @classmethod
    def diagonal(cls, first_id: GridPosition, second_id: GridPosition) -> bool:
        return first_id[0] != second_id[0] and first_id[1] != second_id[1]


class Map(GridHandler):
    """

    """
    game: Optional[Game] = None

    def __init__(self, width=0, height=0, grid_width=0, grid_height=0):
        MapNode.map = Pathfinder.map = self
        self.width = width
        self.height = height
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rows = self.height // self.grid_height
        self.columns = self.width // self.grid_width

        self.nodes: Dict[GridPosition, MapNode] = {}
        self.units: Dict[GridPosition, UnitId] = {}
        self.buildings: Dict[GridPosition, BuildingId] = {}

        self.generate_nodes()
        self.calculate_distances_between_nodes()

    def __len__(self) -> int:
        return len(self.nodes)

    def in_bounds(self, grids) -> List[GridPosition]:
        return [
            p for p in grids if 0 <= p[0] < self.columns and 0 <= p[1] < self.rows
        ]

    def on_map_area(self, x: Number, y: Number) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable_adjacent(self, x, y) -> List[MapNode]:
        return [n for n in self.adjacent_nodes(x, y) if n.walkable]

    def adjacent_nodes(self, x: Number, y: Number) -> List[MapNode]:
        return [
            self.nodes[adj] for adj in self.in_bounds(self.adjacent_grids(x, y))
        ]

    def position_to_node(self, x: Number, y: Number) -> MapNode:
        return self.grid_to_node(self.position_to_grid(x, y))

    def grid_to_node(self, grid: GridPosition) -> MapNode:
        return self.nodes[grid]

    @timer(1, global_profiling_level=PROFILING_LEVEL)
    def generate_nodes(self):
        print(f'map rows: {self.rows}, columns: {self.columns}')
        for x in range(self.columns):
            for y in range(self.rows):
                self.nodes[(x, y)] = node = MapNode(x, y)
                self.create_map_sprite(*node.position)
        log(f'Generated {len(self)} map nodes.', True)

    def create_map_sprite(self, x, y):
        sprite = Sprite(center_x=x, center_y=y)
        sprite.texture = self.random_terrain_texture()
        self.game.terrain_objects.append(
            sprite
        )

    @staticmethod
    def random_terrain_texture() -> Texture:
        texture = random.choice(MAP_TEXTURES['mud'])
        texture.image.transpose(random.randint(0, 5))
        return texture

    def calculate_distances_between_nodes(self):
        for node in self.nodes.values():
            for grid in self.in_bounds(self.adjacent_grids(*node.position)):
                adjacent_node = self.nodes[grid]
                distance = 1.4 if self.diagonal(node.grid, grid) else 1
                distance *= (node.terrain_cost + adjacent_node.terrain_cost)
                node.costs[grid] = distance

    def get_nodes_row(self, row: int) -> List[MapNode]:
        return [n for n in self.nodes.values() if n.grid[1] == row]

    def get_nodes_column(self, column: int) -> List[MapNode]:
        return [n for n in self.nodes.values() if n.grid[0] == column]

    def get_all_nodes(self) -> List[MapNode]:
        return list(self.nodes.values())

    def group_of_waypoints(self,
                           x: Number,
                           y: Number,
                           required_waypoints: int) -> List[GridPosition]:
        first_waypoint = self.position_to_grid(x, y)
        waypoints: Set[GridPosition] = {first_waypoint}
        # all_adjacent = []
        node = self.grid_to_node(first_waypoint)

        while len(waypoints) < required_waypoints:
            adjacent = [n.grid for n in node.walkable_adjacent if n not in waypoints]
            waypoints.update(adjacent)
            # all_adjacent.extend(a for a in adjacent if a not in all_adjacent)
            node = self.grid_to_node(adjacent[-1])
        return [w for w in waypoints]

    def node(self, grid: GridPosition) -> MapNode:
        return self.nodes[grid]


class MapNode(GridHandler, ABC):
    """
    Class representing a single point on Map which can be Units pathfinding
    destination and is associated with graphic-map-tiles displayed on the
    screen.
    """
    map: Optional[Map] = None

    def __init__(self, x, y):
        self.grid = x, y
        self.position = self.x, self.y = self.grid_to_position(self.grid)
        self.costs: Dict[GridPosition, float] = {}
        self._unit_id: Optional[UnitId] = None
        self._building_id: Optional[BuildingId] = None
        self._walkable = True
        self.terrain_cost = 1

    def __repr__(self) -> str:
        return f'MapNode(grid position: {self.grid}, position: {self.position})'

    def in_bounds(self, *args, **kwargs):
        return self.map.in_bounds(*args, **kwargs)

    def diagonal_to_other(self, other: GridPosition):
        return self.grid[0] != other[0] and self.grid[1] != other[1]

    @property
    def unit_id(self) -> UnitId:
        return self._unit_id

    @unit_id.setter
    def unit_id(self, value: Optional[UnitId]):
        self.map.units[self.grid] = value
        self._unit_id = value

    @property
    def building_id(self) -> Optional[BuildingId]:
        return self._unit_id

    @building_id.setter
    def building_id(self, value: Optional[BuildingId]):
        self.map.buildings[self.grid] = value
        self._building_id = value

    @property
    def walkable(self):
        return self._unit_id is None and self._building_id is None

    @property
    def walkable_adjacent(self) -> List[MapNode]:
        return self.map.walkable_adjacent(*self.position)

    @property
    def adjacent_nodes(self) -> List[MapNode]:
        return self.map.adjacent_nodes(*self.position)


class PriorityQueue:
    # much faster than sorting list each frame
    def __init__(self, first_element=None, priority=None):
        self.elements = []
        self._contains = set()  # my improvement, faster lookups
        if first_element is not None:
            self.put(first_element, priority)

    def __bool__(self) -> bool:
        return len(self.elements) > 0

    def __len__(self) -> int:
        return len(self.elements)

    def __contains__(self, item) -> bool:
        return item in self._contains

    def not_empty(self) -> bool:
        return len(self.elements) > 0

    def put(self, item, priority):
        self._contains.add(item)
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]  # (priority, item)


class Pathfinder:
    """
    A* algorithm implementation using PriorityQueue based on improved heapq.
    """
    instance: Optional[Pathfinder] = None
    map: Optional[Map] = None

    @timer(level=2, global_profiling_level=PROFILING_LEVEL)
    def find_path(self, start: GridPosition, end: GridPosition):
        """
        Find shortest path from <start> to <end> position using A* algorithm.
        """
        log(f'Searching for path from {start} to {end}...')
        heuristic = self.heuristic

        map_nodes = self.map.nodes
        unexplored = PriorityQueue(start, heuristic(start, end) * 1.001)
        previous: Dict[GridPosition, GridPosition] = {}

        get_best_unexploed = unexplored.get
        put_to_unexplored = unexplored.put

        cost_so_far = defaultdict(lambda: math.inf)
        cost_so_far[start] = 0

        while unexplored:
            if (current := get_best_unexploed()) == end:
                return self.reconstruct_path(map_nodes, previous, current)
            node = map_nodes[current]
            for adj in (a for a in node.walkable_adjacent if a.grid not in unexplored):
                total = cost_so_far[current] + node.costs[adj.grid]
                if total < cost_so_far[adj.grid]:
                    previous[adj.grid] = current
                    cost_so_far[adj.grid] = total
                    priority = total + heuristic(adj.grid, end) * 1.001
                    put_to_unexplored(adj.grid, priority)
        return []

    @staticmethod
    def heuristic(start, end):
        return hypot(start[0] - end[0], start[1] - end[1])

    def reconstruct_path(self,
                         map_nodes: Dict[GridPosition, MapNode],
                         previous_nodes: Dict[GridPosition, GridPosition],
                         current_node: GridPosition) -> MapPath:
        path = [map_nodes[current_node]]
        while current_node in previous_nodes.keys():
            current_node = previous_nodes[current_node]
            path.append(map_nodes[current_node])
        return self.nodes_list_to_path(path[::-1])

    @staticmethod
    def nodes_list_to_path(nodes_list: List[MapNode]) -> MapPath:
        return [node.position for node in nodes_list]
