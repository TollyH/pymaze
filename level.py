"""
Contains the class definition for Level, which handles collision,
player movement, victory checking, and path finding.
"""
import math
from typing import Dict, List, Tuple


def floor_coordinates(coord: Tuple[float, float]):
    """
    Convert a precise coordinate to one representing whole tile position.
    """
    return (math.floor(coord[0]), math.floor(coord[1]))


class Level:
    """
    A class representing a single maze level. Contains a wall map
    as a 2D array, with True representing the maze walls, and False
    represting occupyable space. Also keeps track of the current player
    coordinates within the level and can calculate possible solutions.
    """
    def __init__(self, dimensions: Tuple[int, int],
                 wall_map: List[List[bool]], start_point: Tuple[int, int],
                 end_point: Tuple[int, int], exit_keys: List[Tuple[int, int]]):
        """
        Create a level with a wall map, start and end points, and
        collectable keys required to exit the level.
        """
        self.dimensions = dimensions

        if (len(wall_map) != dimensions[1]
                or sum(1 for x in wall_map if len(x) != dimensions[0]) != 0):
            raise ValueError(
                f"Wall map must be {dimensions[0]}x{dimensions[1]} points"
            )
        self.wall_map = wall_map

        if not self.is_coord_in_bounds(start_point):
            raise ValueError("Out of bounds start point coordinates")
        if self[start_point]:
            raise ValueError("Start point cannot be inside wall")
        self.start_point = start_point
        # Start in centre of tile
        self.player_coords = (start_point[0] + 0.5, start_point[1] + 0.5)

        if not self.is_coord_in_bounds(end_point):
            raise ValueError("Out of bounds end point coordinates")
        if self[end_point]:
            raise ValueError("End point cannot be inside wall")
        self.end_point = end_point

        for key in exit_keys:
            if not self.is_coord_in_bounds(key):
                raise ValueError("Out of bounds key coordinates")
            if self[key]:
                raise ValueError("Key cannot be inside wall")
        self.original_exit_keys = exit_keys
        # Create a shallow copy of exit keys to be manipulated on collection
        self.exit_keys = [*exit_keys]

        # Maps coordinates to a list of lists of coordinates represting
        # possible paths from a previous player position. Saves on unnecessary
        # repeated calculations.
        self._solution_cache: Dict[
            Tuple[int, int], List[List[Tuple[int, int]]]
        ] = {}

        self.won = False

    def __str__(self):
        """
        Returns a string representation of the maze. '██' is a wall,
        '  ' is empty space, 'PP' is the player, 'KK' are keys, 'SS' is the
        start point, and 'EE' is the end point.
        """
        string = ""
        for y, row in enumerate(self.wall_map):
            for x, point in enumerate(row):
                if floor_coordinates(self.player_coords) == (x, y):
                    string += "PP"
                elif (x, y) in self.exit_keys:
                    string += "KK"
                elif self.start_point == (x, y):
                    string += "SS"
                elif self.end_point == (x, y):
                    string += "EE"
                else:
                    string += "██" if point else "  "
            string += "\n"
        return string[:-1]

    def __getitem__(self, index: Tuple[float, float]):
        """
        Returns True if the specified tile is a wall.
        """
        if not self.is_coord_in_bounds(index):
            raise ValueError("Coordinates must be between 0 and 9")
        grid_index = floor_coordinates(index)
        return self.wall_map[grid_index[1]][grid_index[0]]

    def move_player(self, vector: Tuple[float, float], relative: bool = True):
        """
        Moves the player either relative to their current position, or to an
        absolute location. Key collection and victory checking will be
        performed automatically. Silently fails if the player cannot move by
        the specified vector or to the specified position.
        """
        if relative:
            target = (
                self.player_coords[0] + vector[0],
                self.player_coords[1] + vector[1]
            )
        else:
            target = vector
        if not self.is_coord_in_bounds(target) or self[target] or self.won:
            return
        self.player_coords = target
        if floor_coordinates(target) in self.exit_keys:
            self.exit_keys.remove(floor_coordinates(target))
        if (floor_coordinates(target) == self.end_point
                and len(self.exit_keys) == 0):
            self.won = True

    def find_possible_paths(self):
        """
        Finds all possible paths to the current target(s) from the player's
        current position. The returned result is sorted by path length in
        ascending order (i.e. the shortest path is first).
        """
        targets = (
            [self.end_point] if len(self.exit_keys) == 0 else self.exit_keys
        )
        grid_coords = floor_coordinates(self.player_coords)
        if grid_coords in self._solution_cache:
            return [
                x for x in self._solution_cache[grid_coords]
                if x[-1] in targets
            ]
        result = sorted(
            self._path_search([grid_coords], targets), key=len
        )
        self._solution_cache[grid_coords] = result
        return result

    def reset(self):
        """
        Reset this level to its original state
        """
        # Shallow copy to prevent original key list being modified
        self.exit_keys = [*self.original_exit_keys]
        self.player_coords = (
            self.start_point[0] + 0.5, self.start_point[1] + 0.5
        )
        self.won = False

    def is_coord_in_bounds(self, coord: Tuple[float, float]):
        """
        Checks if a coordinate in within the boundaries of the maze.
        """
        return (
            coord[0] >= 0 and coord[0] < self.dimensions[0]
            and coord[1] >= 0 and coord[1] < self.dimensions[1]
        )

    def _path_search(self, current_path: List[Tuple[int, int]],
                     targets: List[Tuple[int, int]]):
        """
        Recursively find all possible paths to a list of targets. Use the
        find_possible_paths method instead of this one for finding paths
        to the player's target(s).
        """
        found_paths: List[List[Tuple[int, int]]] = []
        for x_offset, y_offset in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            point = (
                current_path[-1][0] + x_offset,
                current_path[-1][1] + y_offset
            )
            if (not self.is_coord_in_bounds(point) or self[point]
                    or point in current_path):
                continue
            if point in targets:
                found_paths.append(current_path + [point])
            found_paths += self._path_search(
                current_path + [point], targets
            )
        return found_paths
