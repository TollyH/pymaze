"""
Contains functions related to the raycast rendering used to generate pseudo-3D
graphics.
"""
import math
from typing import List, Optional, Tuple


def get_first_collision(wall_map: List[List[bool]],
                        origin: Tuple[float, float],
                        direction: Tuple[float, float],
                        edge_is_wall: bool):
    """
    Find the distance of the first intersection of a wall tile by a ray
    travelling at the specified direction from a particular origin. Returns
    None if no collision occurs before the edge of the wall map, or a tuple
    (distance, side) if a collision did occur. Side is False if a North/South
    wall was hit, or True if an East/West wall was.
    """
    # Prevent divide by 0
    if direction[0] == 0:
        direction = (1e-30, direction[1])
    if direction[1] == 0:
        direction = (direction[0], 1e-30)
    # When traversing one unit in a direction, what will the coordinate of the
    # other direction increase by?
    step_size = (abs(1 / direction[0]), abs(1 / direction[1]))
    current_tile = [math.floor(origin[0]), math.floor(origin[1])]
    # The current length of the X and Y rays respectively
    dimension_ray_length = [0.0, 0.0]
    step = [0, 0]

    # Establish ray directions and starting lengths
    # Going negative X (left)
    if direction[0] < 0:
        step[0] = -1
        # X distance from the corner of the origin
        dimension_ray_length[0] = (origin[0] - current_tile[0]) * step_size[0]
    # Going positive X (right)
    else:
        step[0] = 1
        # X distance until origin tile is exited
        dimension_ray_length[0] = (
            current_tile[0] + 1 - origin[0]
        ) * step_size[0]
    # Going negative Y (up)
    if direction[1] < 0:
        step[1] = -1
        # Y distance from the corner of the origin
        dimension_ray_length[1] = (origin[1] - current_tile[1]) * step_size[1]
    # Going positive Y (down)
    else:
        step[1] = 1
        # Y distance until origin tile is exited
        dimension_ray_length[1] = (
            current_tile[1] + 1 - origin[1]
        ) * step_size[1]

    # Stores whether a North/South or East/West wall was hit
    side_was_ns = False
    tile_found = False
    while not tile_found:
        # Move along ray
        if dimension_ray_length[0] < dimension_ray_length[1]:
            current_tile[0] += step[0]
            dimension_ray_length[0] += step_size[0]
            side_was_ns = False
        else:
            current_tile[1] += step[1]
            dimension_ray_length[1] += step_size[1]
            side_was_ns = True

        if (current_tile[1] < 0 or current_tile[0] < 0
                or current_tile[1] >= len(wall_map)
                or current_tile[0] >= len(wall_map[current_tile[1]])):
            # Edge of wall map has been reached, yet no wall in sight
            if edge_is_wall:
                tile_found = True
            else:
                return None
        else:
            # Collision check
            if wall_map[current_tile[1]][current_tile[0]]:
                tile_found = True
    # If this point is reached, a wall tile has been found
    if not side_was_ns:
        return (dimension_ray_length[0] - step_size[0], side_was_ns)
    return (dimension_ray_length[1] - step_size[1], side_was_ns)


def get_column_distances(display_columns: int, wall_map: List[List[bool]],
                         edge_is_wall: bool, origin: Tuple[float, float],
                         direction: Tuple[float, float],
                         camera_plane: Tuple[float, float]):
    """
    Get a list of the distances of each column's ray for a particular wall map
    by utilising raycasting.
    """
    columns: List[Tuple[Optional[float], bool]] = []
    for index in range(display_columns):
        camera_x = 2 * index / display_columns - 1
        cast_direction = (
            direction[0] + camera_plane[0] * camera_x,
            direction[1] + camera_plane[1] * camera_x,
        )
        result = get_first_collision(
            wall_map, origin, cast_direction, edge_is_wall
        )
        if result is None:
            columns.append((None, False))
        else:
            columns.append(result)
    return columns
