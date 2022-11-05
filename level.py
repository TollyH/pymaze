"""
Contains the class definition for Level, which handles collision,
player movement, victory checking, and path finding.
"""
import random
from typing import Any, Dict, List, no_type_check, Optional, Set, Tuple, Union

# Movement events
MOVED = 0
MOVED_GRID_DIAGONALLY = 1
ALTERNATE_COORD_CHOSEN = 2
PICKUP = 3
PICKED_UP_KEY = 4
PICKED_UP_KEY_SENSOR = 5
PICKED_UP_GUN = 6
WON = 7
MONSTER_CAUGHT = 8

# Wall map index selection type
PRESENCE = 0
PLAYER_COLLIDE = 1
MONSTER_COLLIDE = 2


class Level:
    """
    A class representing a single maze level. Contains a wall map
    as a 2D array, with strings representing the north, east, south, and west
    texture names for maze walls, and None representing occupy-able space.
    The collision map is a 2D array of two bools representing whether the
    player/monster should collide with the square respectively.
    Also keeps track of the current player coordinates within the level and can
    calculate possible solutions.
    Decorations are a dictionary of coordinates to a decoration texture name.
    Monster can be set to None if you do not wish the level
    to have a monster, or if you do it should be a Tuple of (x, y, spawn_delay)
    This class will not automatically move or spawn the monster by itself,
    however does provide the method required to do so.
    Note that the wall map may also contain 'True' values. These represent
    player placed walls and are only temporary.
    """
    def __init__(self, dimensions: Tuple[int, int],
                 wall_map: List[List[
                     Optional[Union[Tuple[str, str, str, str], bool]]
                 ]], collision_map: List[List[Tuple[bool, bool]]],
                 start_point: Tuple[int, int], end_point: Tuple[int, int],
                 exit_keys: Set[Tuple[int, int]],
                 key_sensors: Set[Tuple[int, int]], guns: Set[Tuple[int, int]],
                 decorations: Dict[Tuple[int, int], str],
                 monster: Optional[Tuple[int, int, float]],
                 edge_wall_texture_name: str):
        self.dimensions = dimensions
        self.edge_wall_texture_name = edge_wall_texture_name

        if (len(wall_map) != dimensions[1]
                or sum(1 for x in wall_map if len(x) != dimensions[0]) != 0):
            raise ValueError(
                f"Wall map must be {dimensions[0]}x{dimensions[1]} points"
            )
        self.wall_map: List[
            List[Optional[Union[Tuple[str, str, str, str], bool]]]
        ] = wall_map

        if (len(collision_map) != dimensions[1]
                or sum(
                    1 for x in collision_map if len(x) != dimensions[0]) != 0):
            raise ValueError(
                f"Collision map must be {dimensions[0]}x{dimensions[1]} points"
            )
        self.collision_map: List[List[Tuple[bool, bool]]] = collision_map

        if not self.is_coord_in_bounds(start_point):
            raise ValueError("Out of bounds start point coordinates")
        if self[start_point, PRESENCE] or self[start_point, PLAYER_COLLIDE]:
            raise ValueError(
                "Start point cannot be inside wall or player collider"
            )
        self.start_point = start_point
        # Start in the centre of the tile
        self.player_coords = (start_point[0] + 0.5, start_point[1] + 0.5)
        self.player_grid_coords = start_point

        if not self.is_coord_in_bounds(end_point):
            raise ValueError("Out of bounds end point coordinates")
        if self[end_point, PRESENCE] or self[end_point, PLAYER_COLLIDE]:
            raise ValueError(
                "End point cannot be inside wall or player collider"
            )
        self.end_point = end_point

        for key in exit_keys:
            if not self.is_coord_in_bounds(key):
                raise ValueError("Out of bounds key coordinates")
            if self[key, PRESENCE] or self[key, PLAYER_COLLIDE]:
                raise ValueError(
                    "Key cannot be inside wall or player collider"
                )
        # Use a frozen set to prevent manipulation of original exit keys.
        self.original_exit_keys = frozenset(exit_keys)
        self.exit_keys = exit_keys

        for sensor in key_sensors:
            if not self.is_coord_in_bounds(sensor):
                raise ValueError("Out of bounds key sensor coordinates")
            if self[sensor, PRESENCE] or self[sensor, PLAYER_COLLIDE]:
                raise ValueError(
                    "Key sensor cannot be inside wall or player collider"
                )
        # Use a frozen set to prevent manipulation of original key sensors.
        self.original_key_sensors = frozenset(key_sensors)
        self.key_sensors = key_sensors

        for gun_pickup in guns:
            if not self.is_coord_in_bounds(gun_pickup):
                raise ValueError("Out of bounds gun coordinates")
            if self[gun_pickup, PRESENCE] or self[gun_pickup, PLAYER_COLLIDE]:
                raise ValueError(
                    "Gun cannot be inside wall or player collider"
                )
        # Use a frozen set to prevent manipulation of original guns
        self.original_guns = frozenset(guns)
        self.guns = guns

        for decor in decorations:
            if not self.is_coord_in_bounds(decor[:2]):
                raise ValueError("Out of bounds decoration coordinates")
            if self[decor[:2], PRESENCE] or self[decor[:2], PLAYER_COLLIDE]:
                raise ValueError(
                    "Decoration cannot be inside wall or player collider"
                )
        self.decorations = decorations

        self.monster_coords: Optional[Tuple[int, int]] = None
        if monster is not None:
            monster_start, monster_wait = monster[:2], monster[2]
            if not self.is_coord_in_bounds(monster_start):
                raise ValueError("Out of bounds monster start coordinates")
            if (self[monster_start, PRESENCE]
                    or self[monster_start, PLAYER_COLLIDE]):
                raise ValueError(
                    "Monster start cannot be inside wall or player collider"
                )
            self.monster_start: Optional[Tuple[int, int]] = monster_start
            self.monster_wait: Optional[float] = monster_wait
        else:
            self.monster_start = None
            self.monster_wait = None

        self.player_flags: Set[Tuple[int, int]] = set()

        # Used to prevent the monster from backtracking
        self._last_monster_position: Optional[Tuple[int, int]] = None

        # Maps coordinates to a list of lists of coordinates represented
        # possible paths from a previous player position. Saves on unnecessary
        # repeated calculations.
        self._solution_cache: Dict[
            Tuple[int, int], List[List[Tuple[int, int]]]
        ] = {}

        self.won = False
        self.killed = False

    @classmethod
    @no_type_check
    def from_json_dict(cls, json_dict: Dict[str, Any]) -> 'Level':
        """
        Create a Level instance from a valid deserialized JSON dictionary.
        Converts lists (JSON arrays) back to tuples and sets, and converts
        applicable string keys back to tuples.
        """
        return cls(
            tuple(json_dict['dimensions']),
            [
                [None if x is None else tuple(x) for x in y]
                for y in json_dict['wall_map']
            ],
            [[tuple(x) for x in y] for y in json_dict['collision_map']],
            tuple(json_dict['start_point']), tuple(json_dict['end_point']),
            {tuple(x) for x in json_dict['exit_keys']},
            {tuple(x) for x in json_dict['key_sensors']},
            {tuple(x) for x in json_dict['guns']},
            {
                tuple(int(x) for x in y.split(",")): z
                for y, z in json_dict['decorations'].items()
            },
            None
            if json_dict['monster_start'] is None else
            tuple(json_dict['monster_start'] + [json_dict['monster_wait']]),
            json_dict['edge_wall_texture_name']
        )

    @no_type_check
    def to_json_dict(self) -> Dict[str, Any]:
        """
        Convert this level into a JSON compatible dictionary. All tuples and
        sets are converted to lists (JSON arrays), and all tuple dictionary
        keys are converted to strings.
        """
        return {
            "dimensions": list(self.dimensions),
            "wall_map": [
                # 'x' is True when a player placed wall is in that position.
                # These are only temporary and as such should be serialized as
                # empty space.
                [None if x is True or x is None else list(x) for x in y]
                for y in self.wall_map
            ],
            "collision_map": [
                [list(x) for x in y] for y in self.collision_map
            ],
            "start_point": list(self.start_point),
            "end_point": list(self.end_point),
            "exit_keys": [list(x) for x in self.original_exit_keys],
            "key_sensors": [list(x) for x in self.original_key_sensors],
            "guns": [list(x) for x in self.original_guns],
            "decorations": {
                f"{x[0]},{x[1]}": y for x, y in self.decorations.items()
            },
            "monster_start": (
                None
                if self.monster_start is None else
                list(self.monster_start)
            ),
            "monster_wait": self.monster_wait,
            "edge_wall_texture_name": self.edge_wall_texture_name
        }

    def __str__(self) -> str:
        """
        Returns a string representation of the maze. '██' is a wall,
        '  ' is empty space, 'PP' is the player, 'KK' are keys, 'SS' is the
        start point, and 'EE' is the end point.
        """
        string = ""
        for y, row in enumerate(self.wall_map):
            for x, point in enumerate(row):
                if self.player_grid_coords == (x, y):
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
                    string += "██" if point is not None else "  "
            string += "\n"
        return string[:-1]

    def __getitem__(self, index: Tuple[Tuple[float, float], int]
                    ) -> Optional[Union[Tuple[str, str, str, str], bool]]:
        """
        Check for either the PRESENCE of a wall, or whether the player should
        collide (PLAYER_COLLIDE), or whether the monster should collide
        (MONSTER_COLLIDE).
        Gets the north, south, east, and west textures for the wall at the
        specified coordinates, or None if there is no wall if checking for
        PRESENCE, otherwise a bool. A True value may also be returned for
        PRESENCE if a player placed wall is at the specified coordinate.
        """
        grid_index = (index[0][0].__trunc__(), index[0][1].__trunc__())
        if index[1] == PRESENCE:
            return self.wall_map[grid_index[1]][grid_index[0]]
        if index[1] == PLAYER_COLLIDE:
            return self.collision_map[grid_index[1]][grid_index[0]][0]
        if index[1] == MONSTER_COLLIDE:
            return self.collision_map[grid_index[1]][grid_index[0]][1]
        return None

    def __setitem__(self, index: Tuple[Tuple[int, int], int],
                    value: Optional[Union[Tuple[str, str, str, str], bool]]
                    ) -> None:
        """
        Change the texture of a wall or remove the wall entirely if PRESENCE
        is specified, or change the PLAYER_COLLIDE or MONSTER_COLLIDE status.
        """
        if index[1] == PRESENCE:
            self.wall_map[index[0][1]][index[0][0]] = value
        elif index[1] == PLAYER_COLLIDE:
            if isinstance(value, bool):
                self.collision_map[index[0][1]][index[0][0]] = (
                    value, self.collision_map[index[0][1]][index[0][0]][1]
                )
            else:
                raise TypeError("Collision map entries must be bool")
        elif index[1] == MONSTER_COLLIDE:
            if isinstance(value, bool):
                self.collision_map[index[0][1]][index[0][0]] = (
                    self.collision_map[index[0][1]][index[0][0]][0], value
                )
            else:
                raise TypeError("Collision map entries must be bool")

    def move_player(self, vector: Tuple[float, float], has_gun: bool,
                    relative: bool = True, collision_check: bool = True,
                    multiplayer: bool = False
                    ) -> Set[int]:
        """
        Moves the player either relative to their current position, or to an
        absolute location. Pickups and victory checking will be performed
        automatically, and guns won't be picked up if has_gun is True.
        Fails without raising an error if the player cannot move by the
        specified vector or to the specified position.
        Returns a set of actions that took place as a result of the move,
        which may be empty if nothing changed. All events are included, so for
        example if MOVED_GRID_DIAGONALLY is returned, MOVED will also be.
        """
        events: Set[int] = set()
        if (self.won or self.killed) and not multiplayer:
            return events
        if relative:
            target = (
                self.player_coords[0] + vector[0],
                self.player_coords[1] + vector[1]
            )
            # Try moving just in X or Y if primary target cannot be moved to.
            alternate_targets = [
                (self.player_coords[0] + vector[0], self.player_coords[1]),
                (self.player_coords[0], self.player_coords[1] + vector[1])
            ]
        else:
            target = vector
            # There are no alternate movements if we aren't moving relatively.
            alternate_targets = []
        if not self.is_coord_in_bounds(target) or (
                self[target, PLAYER_COLLIDE] and collision_check):
            found_valid = False
            for alt_move in alternate_targets:
                if self.is_coord_in_bounds(alt_move) and (
                        not self[alt_move, PLAYER_COLLIDE]
                        or not collision_check):
                    target = alt_move
                    found_valid = True
                    events.add(ALTERNATE_COORD_CHOSEN)
            if not found_valid:
                return events
        grid_coords = (target[0].__trunc__(), target[1].__trunc__())
        relative_grid_pos = (
            grid_coords[0] - self.player_grid_coords[0],
            grid_coords[1] - self.player_grid_coords[1]
        )
        # Moved diagonally therefore skipping a square, make sure that's valid.
        if relative_grid_pos[0] and relative_grid_pos[1]:
            if collision_check:
                diagonal_path_free = False
                if not self[(self.player_grid_coords[0] + relative_grid_pos[0],
                            self.player_grid_coords[1]), PLAYER_COLLIDE]:
                    diagonal_path_free = True
                elif not self[(self.player_grid_coords[0],
                              self.player_grid_coords[1]
                              + relative_grid_pos[1]), PLAYER_COLLIDE]:
                    diagonal_path_free = True
                if not diagonal_path_free:
                    return events
            events.add(MOVED_GRID_DIAGONALLY)
        self.player_coords = target
        self.player_grid_coords = grid_coords
        events.add(MOVED)
        if grid_coords in self.exit_keys:
            self.exit_keys.remove(grid_coords)
            events.add(PICKED_UP_KEY)
            events.add(PICKUP)
        if grid_coords in self.key_sensors:
            self.key_sensors.remove(grid_coords)
            events.add(PICKED_UP_KEY_SENSOR)
            events.add(PICKUP)
        if grid_coords in self.guns and not has_gun:
            self.guns.remove(grid_coords)
            events.add(PICKED_UP_GUN)
            events.add(PICKUP)
        if grid_coords == self.monster_coords:
            events.add(MONSTER_CAUGHT)
        elif grid_coords == self.end_point and len(self.exit_keys) == 0:
            self.won = True
            events.add(WON)
        return events

    def move_monster(self) -> bool:
        """
        Moves the monster one space in a random available direction, unless
        the player is in the unobstructed view of one of the cardinal
        directions, in which case move toward the player instead.
        If the monster is not spawned in yet, it will be spawned when this
        function is called IF the player is 2 or more units away.
        If the monster and the player occupy the same grid square, True will be
        returned, else False will be.
        """
        import raycasting  # Import is here to prevent circular import
        last_monster_position = self.monster_coords
        if self.monster_start is None:
            return False
        if (self.monster_coords is None and
                raycasting.no_sqrt_coord_distance(
                    self.player_grid_coords, self.monster_start
                ) >= 4):
            self.monster_coords = self.monster_start
        elif self.monster_coords is not None:
            # 0 — Not in line of sight.
            # 1 — Line of sight on Y axis.
            # 2 — Line of sight on X axis.
            line_of_sight = 0
            if self.player_grid_coords[0] == self.monster_coords[0]:
                min_y_coord = min(
                    self.player_grid_coords[1], self.monster_coords[1]
                )
                max_y_coord = max(
                    self.player_grid_coords[1], self.monster_coords[1]
                )
                collided = False
                for y_coord in range(min_y_coord, max_y_coord + 1):
                    if self[(self.player_grid_coords[0], y_coord),
                            MONSTER_COLLIDE]:
                        collided = True
                        break
                if not collided:
                    line_of_sight = 1
            elif self.player_grid_coords[1] == self.monster_coords[1]:
                min_x_coord = min(
                    self.player_grid_coords[0], self.monster_coords[0]
                )
                max_x_coord = max(
                    self.player_grid_coords[0], self.monster_coords[0]
                )
                collided = False
                for x_coord in range(min_x_coord, max_x_coord + 1):
                    if self[(x_coord, self.player_grid_coords[1]),
                            MONSTER_COLLIDE]:
                        collided = True
                        break
                if not collided:
                    line_of_sight = 2
            if line_of_sight == 1:
                if self.player_grid_coords[1] > self.monster_coords[1]:
                    self.monster_coords = (
                        self.monster_coords[0], self.monster_coords[1] + 1
                    )
                else:
                    self.monster_coords = (
                        self.monster_coords[0], self.monster_coords[1] - 1
                    )
            elif line_of_sight == 2:
                if self.player_grid_coords[0] > self.monster_coords[0]:
                    self.monster_coords = (
                        self.monster_coords[0] + 1, self.monster_coords[1]
                    )
                else:
                    self.monster_coords = (
                        self.monster_coords[0] - 1, self.monster_coords[1]
                    )
            else:
                # Randomise order of each cardinal direction, then move to
                # the first one available.
                shuffled_vectors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(shuffled_vectors)
                for vector in shuffled_vectors:
                    target = (
                        self.monster_coords[0] + vector[0],
                        self.monster_coords[1] + vector[1]
                    )
                    if (self.is_coord_in_bounds(target)
                            and not self[target, MONSTER_COLLIDE]
                            and self._last_monster_position != target):
                        self.monster_coords = target
                        break
        self._last_monster_position = last_monster_position
        if self.monster_coords in self.player_flags and random.random() < 0.25:
            self.player_flags.remove(self.monster_coords)
        return self.monster_coords == self.player_grid_coords

    def find_possible_paths(self) -> List[List[Tuple[int, int]]]:
        """
        Finds all possible paths to the current target(s) from the player's
        current position. The returned result is sorted by path length in
        ascending order (i.e. the shortest path is first). Potentially very
        computationally expensive.
        """
        targets = (
            {self.end_point} if len(self.exit_keys) == 0 else self.exit_keys
        )
        if self.player_grid_coords in self._solution_cache:
            return [
                x for x in self._solution_cache[self.player_grid_coords]
                if x[-1] in targets
            ]
        result = sorted(
            self._path_search([self.player_grid_coords], targets), key=len
        )
        self._solution_cache[self.player_grid_coords] = result
        return result

    def reset(self) -> None:
        """
        Reset this level to its original state
        """
        self.exit_keys = set(self.original_exit_keys)
        self.key_sensors = set(self.original_key_sensors)
        self.guns = set(self.original_guns)
        self.player_flags = set()
        self.player_coords = (
            self.start_point[0] + 0.5, self.start_point[1] + 0.5
        )
        self.player_grid_coords = self.start_point
        self.monster_coords = None
        self.won = False
        self.killed = False

    def is_coord_in_bounds(self, coord: Tuple[float, float]) -> bool:
        """
        Checks if a coordinate in within the boundaries of the maze.
        """
        return (
            0 <= coord[0] < self.dimensions[0]
            and 0 <= coord[1] < self.dimensions[1]
        )

    def randomise_player_coords(self) -> None:
        """
        Move the player to a random valid position in the level. Used in
        multiplayer for (re)spawning.
        """
        new_coord = None
        while new_coord is None or self[new_coord, PLAYER_COLLIDE]:
            new_coord = (
                random.randint(0, self.dimensions[0] - 1) + 0.5,
                random.randint(0, self.dimensions[1] - 1) + 0.5
            )
        self.move_player(new_coord, False, False, False, True)

    def _path_search(self, current_path: List[Tuple[int, int]],
                     targets: Set[Tuple[int, int]]
                     ) -> List[List[Tuple[int, int]]]:
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
            if not self.is_coord_in_bounds(point) or self[
                    point, PLAYER_COLLIDE] or point in current_path:
                continue
            if point in targets:
                found_paths.append(current_path + [point])
            found_paths += self._path_search(
                current_path + [point], targets
            )
        return found_paths
