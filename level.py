"""
Contains the class definition for Level, which handles collision,
player movement, victory checking, and path finding.
"""
import random
from typing import Dict, List, Optional, Tuple


class Level:
    """
    A class representing a single maze level. Contains a wall map
    as a 2D array, with True representing the maze walls, and False
    represting occupyable space. Also keeps track of the current player
    coordinates within the level and can calculate possible solutions.
    Monster start and wait can be set to None if you do not wish the level
    to have a monster. This class will not automatically move or spawn
    the monster by itself, however does provide the method required to do so.
    """
    def __init__(self, dimensions: Tuple[int, int],
                 wall_map: List[List[bool]], start_point: Tuple[int, int],
                 end_point: Tuple[int, int], exit_keys: List[Tuple[int, int]],
                 monster_start: Optional[Tuple[int, int]],
                 monster_wait: Optional[float]):
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

        if not self._is_coord_in_bounds(start_point):
            raise ValueError("Out of bounds start point coordinates")
        if self[start_point]:
            raise ValueError("Start point cannot be inside wall")
        self.start_point = start_point
        self.player_coords = start_point

        if not self._is_coord_in_bounds(end_point):
            raise ValueError("Out of bounds end point coordinates")
        if self[end_point]:
            raise ValueError("End point cannot be inside wall")
        self.end_point = end_point

        for key in exit_keys:
            if not self._is_coord_in_bounds(key):
                raise ValueError("Out of bounds key coordinates")
            if self[key]:
                raise ValueError("Key cannot be inside wall")
        self.original_exit_keys = exit_keys
        # Create a shallow copy of exit keys to be manipulated on collection
        self.exit_keys = [*exit_keys]

        self.monster_coords: Optional[Tuple[int, int]] = None
        if monster_start is not None:
            if not self._is_coord_in_bounds(monster_start):
                raise ValueError("Out of bounds monster start coordinates")
            if self[monster_start]:
                raise ValueError("Monster start cannot be inside wall")
            self.monster_start = monster_start
            self.monster_wait = monster_wait
        else:
            self.monster_start = None
            self.monster_wait = None

        self._last_monster_position = (-1, -1)

        # Maps coordinates to a list of lists of coordinates represting
        # possible paths from a previous player position. Saves on unnecessary
        # repeated calculations.
        self._solution_cache: Dict[
            Tuple[int, int], List[List[Tuple[int, int]]]
        ] = {}

        self.won = False
        self.killed = False

    def __str__(self):
        """
        Returns a string representation of the maze. '██' is a wall,
        '  ' is empty space, 'PP' is the player, 'KK' are keys, 'SS' is the
        start point, 'EE' is the end point, and 'MM' is the monster.
        """
        string = ""
        for y, row in enumerate(self.wall_map):
            for x, point in enumerate(row):
                if self.player_coords == (x, y):
                    string += "PP"
                elif self.monster_coords == (x, y):
                    string += "MM"
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

    def __getitem__(self, index: Tuple[int, int]):
        """
        Returns True if the specified tile is a wall.
        """
        if not self._is_coord_in_bounds(index):
            raise ValueError("Target coordinates out of bounds")
        return self.wall_map[index[1]][index[0]]

    def move_player(self, vector: Tuple[int, int], relative: bool = True):
        """
        Moves the player either relative to their current position, or to an
        absolute location. Key collection and victory checking will be
        performed automatically. Silently fails if the player cannot move by
        the specified vector or to the specified position.
        """
        if self.won or self.killed:
            return
        if relative:
            target = (
                self.player_coords[0] + vector[0],
                self.player_coords[1] + vector[1]
            )
        else:
            target = vector
        if not self._is_coord_in_bounds(target) or self[target]:
            return
        self.player_coords = target
        if target in self.exit_keys:
            self.exit_keys.remove(target)
        if target == self.monster_coords:
            self.killed = True
        elif target == self.end_point and len(self.exit_keys) == 0:
            self.won = True

    def move_monster(self):
        """
        Moves the monster one space in a random available direction, unless
        the player is in the unobstructed view of one of the cardinal
        directions, in which case move toward the player instead. If the
        monster and the player occupy the same grid square, self.killed will
        be set to True.
        """
        last_monster_position = self.monster_coords
        if self.monster_start is None:
            return
        if self.monster_coords is None:
            self.monster_coords = self.monster_start
        else:
            # 0 - Not in line of sight
            # 1 - Line of sight on Y axis
            # 2 - Line of sight on X axis
            line_of_sight = 0
            if self.player_coords[0] == self.monster_coords[0]:
                min_y_coord = min(
                    self.player_coords[1], self.monster_coords[1]
                )
                max_y_coord = max(
                    self.player_coords[1], self.monster_coords[1]
                )
                collided = False
                for y_coord in range(min_y_coord, max_y_coord + 1):
                    if self[self.player_coords[0], y_coord]:
                        collided = True
                        break
                if not collided:
                    line_of_sight = 1
            elif self.player_coords[1] == self.monster_coords[1]:
                min_x_coord = min(
                    self.player_coords[0], self.monster_coords[0]
                )
                max_x_coord = max(
                    self.player_coords[0], self.monster_coords[0]
                )
                collided = False
                for x_coord in range(min_x_coord, max_x_coord + 1):
                    if self[x_coord, self.player_coords[1]]:
                        collided = True
                        break
                if not collided:
                    line_of_sight = 2
            if line_of_sight == 1:
                if self.player_coords[1] > self.monster_coords[1]:
                    self.monster_coords = (
                        self.monster_coords[0], self.monster_coords[1] + 1
                    )
                else:
                    self.monster_coords = (
                        self.monster_coords[0], self.monster_coords[1] - 1
                    )
            elif line_of_sight == 2:
                if self.player_coords[0] > self.monster_coords[0]:
                    self.monster_coords = (
                        self.monster_coords[0] + 1, self.monster_coords[1]
                    )
                else:
                    self.monster_coords = (
                        self.monster_coords[0] - 1, self.monster_coords[1]
                    )
            else:
                shuffled_vectors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(shuffled_vectors)
                for vector in shuffled_vectors:
                    target = (
                        self.monster_coords[0] + vector[0],
                        self.monster_coords[1] + vector[1]
                    )
                    if (self._is_coord_in_bounds(target) and not self[target]
                            and self._last_monster_position != target):
                        self.monster_coords = target
                        break
        self._last_monster_position = last_monster_position
        if self.monster_coords == self.player_coords:
            self.killed = True

    def find_possible_paths(self):
        """
        Finds all possible paths to the current target(s) from the player's
        current position. The returned result is sorted by path length in
        ascending order (i.e. the shortest path is first).
        """
        targets = (
            [self.end_point] if len(self.exit_keys) == 0 else self.exit_keys
        )
        if self.player_coords in self._solution_cache:
            return [
                x for x in self._solution_cache[self.player_coords]
                if x[-1] in targets
            ]
        result = sorted(
            self._path_search([self.player_coords], targets), key=len
        )
        self._solution_cache[self.player_coords] = result
        return result

    def reset(self):
        """
        Reset this level to its original state
        """
        # Shallow copy to prevent original key list being modified
        self.exit_keys = [*self.original_exit_keys]
        self.player_coords = self.start_point
        self.monster_coords = None
        self.won = False
        self.killed = False

    def _is_coord_in_bounds(self, coord: Tuple[int, int]):
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
            if (not self._is_coord_in_bounds(point) or self[point]
                    or point in current_path):
                continue
            if point in targets:
                found_paths.append(current_path + [point])
            found_paths += self._path_search(
                current_path + [point], targets
            )
        return found_paths
