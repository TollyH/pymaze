"""
Contains functions related to the raycast rendering used to generate pseudo-3D
graphics.
"""
from typing import List, Literal, Tuple

import level

WALL = 0
END_POINT = 1
KEY = 2
MONSTER = 3


def get_first_collision(current_level: level.Level,
                        direction: Tuple[float, float],
                        edge_is_wall: bool):
    """
    Find the first intersection of a wall tile by a ray travelling at the
    specified direction from a particular origin. Returns None if no collision
    occurs before the edge of the wall map, or a tuple
    (coordinate, distance, side_was_ns, type) if a collision did occur.
    Side is False if a North/South wall was hit, or True if an East/West wall
    was. Type is either WALL, END_POINT, KEY, or MONSTER.
    """
    # Prevent divide by 0
    if direction[0] == 0:
        direction = (1e-30, direction[1])
    if direction[1] == 0:
        direction = (direction[0], 1e-30)
    # When traversing one unit in a direction, what will the coordinate of the
    # other direction increase by?
    step_size = (abs(1 / direction[0]), abs(1 / direction[1]))
    current_tile = list(level.floor_coordinates(current_level.player_coords))
    # The current length of the X and Y rays respectively
    dimension_ray_length = [0.0, 0.0]
    step = [0, 0]

    # Establish ray directions and starting lengths
    # Going negative X (left)
    if direction[0] < 0:
        step[0] = -1
        # X distance from the corner of the origin
        dimension_ray_length[0] = (
            current_level.player_coords[0] - current_tile[0]
        ) * step_size[0]
    # Going positive X (right)
    else:
        step[0] = 1
        # X distance until origin tile is exited
        dimension_ray_length[0] = (
            current_tile[0] + 1 - current_level.player_coords[0]
        ) * step_size[0]
    # Going negative Y (up)
    if direction[1] < 0:
        step[1] = -1
        # Y distance from the corner of the origin
        dimension_ray_length[1] = (
            current_level.player_coords[1] - current_tile[1]
        ) * step_size[1]
    # Going positive Y (down)
    else:
        step[1] = 1
        # Y distance until origin tile is exited
        dimension_ray_length[1] = (
            current_tile[1] + 1 - current_level.player_coords[1]
        ) * step_size[1]

    distance = 0.0
    # Stores whether a North/South or East/West wall was hit
    side_was_ns = False
    tile_found = False
    hit_type = 0
    while not tile_found:
        # Move along ray
        if dimension_ray_length[0] < dimension_ray_length[1]:
            current_tile[0] += step[0]
            distance = dimension_ray_length[0]
            dimension_ray_length[0] += step_size[0]
            side_was_ns = False
        else:
            current_tile[1] += step[1]
            distance = dimension_ray_length[1]
            dimension_ray_length[1] += step_size[1]
            side_was_ns = True

        if not current_level.is_coord_in_bounds(tuple(current_tile)):
            # Edge of wall map has been reached, yet no wall in sight
            if edge_is_wall:
                tile_found = True
            else:
                return None
        else:
            check_coords = tuple(current_tile)
            # Collision check
            if current_level[check_coords]:
                tile_found = True
                hit_type = WALL
            elif check_coords == current_level.monster_coords:
                tile_found = True
                hit_type = MONSTER
            elif (check_coords == current_level.end_point
                    and len(current_level.exit_keys) == 0):
                tile_found = True
                hit_type = END_POINT
            elif check_coords in current_level.exit_keys:
                tile_found = True
                hit_type = KEY
    # If this point is reached, a wall tile has been found
    if not side_was_ns:
        return (
            (
                current_level.player_coords[0] + direction[0] * distance,
                current_level.player_coords[1] + direction[1] * distance
            ),
            dimension_ray_length[0] - step_size[0], side_was_ns, hit_type
        )
    return (
        (
            current_level.player_coords[0] + direction[0] * distance,
            current_level.player_coords[1] + direction[1] * distance
        ),
        dimension_ray_length[1] - step_size[1], side_was_ns, hit_type
    )


def get_columns(display_columns: int, current_level: level.Level,
                edge_is_wall: bool, direction: Tuple[float, float],
                camera_plane: Tuple[float, float]):
    """
    Get a list of the intersection positions and distances of each column's ray
    for a particular wall map by utilising raycasting. Tuples are in format
    (coordinate, distance, side_was_ns, type).
    """
    columns: List[
        Tuple[Tuple[float, float], float, bool, Literal[0, 1, 2, 3]]
    ] = []
    for index in range(display_columns):
        camera_x = 2 * index / display_columns - 1
        cast_direction = (
            direction[0] + camera_plane[0] * camera_x,
            direction[1] + camera_plane[1] * camera_x,
        )
        result = get_first_collision(
            current_level, cast_direction, edge_is_wall
        )
        if result is None:
            columns.append(((0.0, 0.0), float('inf'), False, 0))
        else:
            columns.append(result)
    return columns
