"""
Contains functions related to the raycast rendering used to generate pseudo-3D
graphics.
"""
from typing import List, Tuple

import level

# Sprite types
END_POINT = 0
KEY = 1
MONSTER = 2
START_POINT = 3
FLAG = 4
END_POINT_ACTIVE = 5


def get_first_collision(current_level: level.Level,
                        direction: Tuple[float, float],
                        edge_is_wall: bool):
    """
    Find the first intersection of a wall tile by a ray travelling at the
    specified direction from a particular origin. The result will always be a
    tuple, of which the first item will be None if no collision occurs before
    the edge of the wall map, or a tuple
    (coordinate, distance, euclidean_squared, side_was_ns) if a collision did
    occur. Side is False if a North/South wall was hit, or True if an East/West
    wall was. The second tuple item is a list of tuples of sprite tile
    coordinates, their associated type, being either END_POINT, KEY, MONSTER,
    START_POINT, or FLAG - and the euclidean distance to the sprite.
    """
    # Prevent divide by 0
    if direction[0] == 0:
        direction = (1e-30, direction[1])
    if direction[1] == 0:
        direction = (direction[0], 1e-30)
    # When traversing one unit in a direction, what will the coordinate of the
    # other direction increase by?
    step_size = (abs(1 / direction[0]), abs(1 / direction[1]))
    current_tile = level.floor_coordinates(current_level.player_coords)
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
    sprites: List[Tuple[Tuple[float, float], int, float]] = []
    while not tile_found:
        # Move along ray
        if dimension_ray_length[0] < dimension_ray_length[1]:
            current_tile = (current_tile[0] + step[0], current_tile[1])
            distance = dimension_ray_length[0]
            dimension_ray_length[0] += step_size[0]
            side_was_ns = False
        else:
            current_tile = (current_tile[0], current_tile[1] + step[1])
            distance = dimension_ray_length[1]
            dimension_ray_length[1] += step_size[1]
            side_was_ns = True

        if not current_level.is_coord_in_bounds(current_tile):
            # Edge of wall map has been reached, yet no wall in sight
            if edge_is_wall:
                tile_found = True
            else:
                return None, sprites
        else:
            if current_tile in current_level.exit_keys:
                sprites.append((
                    (current_tile[0] + 0.5, current_tile[1] + 0.5),
                    KEY, no_sqrt_coord_distance(
                        current_level.player_coords,
                        (current_tile[0] + 0.5, current_tile[1] + 0.5)
                    )
                ))
            if current_level.end_point == current_tile:
                sprites.append((
                    (current_tile[0] + 0.5, current_tile[1] + 0.5),
                    END_POINT
                    if len(current_level.exit_keys) != 0 else
                    END_POINT_ACTIVE, no_sqrt_coord_distance(
                        current_level.player_coords,
                        (current_tile[0] + 0.5, current_tile[1] + 0.5)
                    )
                ))
            if current_level.monster_coords == current_tile:
                sprites.append((
                    (current_tile[0] + 0.5, current_tile[1] + 0.5),
                    MONSTER, no_sqrt_coord_distance(
                        current_level.player_coords,
                        (current_tile[0] + 0.5, current_tile[1] + 0.5)
                    )
                ))
            if current_level.start_point == current_tile:
                sprites.append((
                    (current_tile[0] + 0.5, current_tile[1] + 0.5),
                    START_POINT, no_sqrt_coord_distance(
                        current_level.player_coords,
                        (current_tile[0] + 0.5, current_tile[1] + 0.5)
                    )
                ))
            if current_tile in current_level.player_flags:
                sprites.append((
                    (current_tile[0] + 0.5, current_tile[1] + 0.5),
                    FLAG, no_sqrt_coord_distance(
                        current_level.player_coords,
                        (current_tile[0] + 0.5, current_tile[1] + 0.5)
                    )
                ))
            # Collision check
            if current_level[current_tile]:
                tile_found = True
    # If this point is reached, a wall tile has been found
    collision_point = (
        current_level.player_coords[0] + direction[0] * distance,
        current_level.player_coords[1] + direction[1] * distance
    )
    if not side_was_ns:
        return (
            collision_point, dimension_ray_length[0] - step_size[0],
            no_sqrt_coord_distance(
                current_level.player_coords, collision_point
            ), side_was_ns
        ), sprites
    return (
        collision_point, dimension_ray_length[1] - step_size[1],
        no_sqrt_coord_distance(
            current_level.player_coords, collision_point
        ), side_was_ns
    ), sprites


def get_columns_sprites(display_columns: int, current_level: level.Level,
                        edge_is_wall: bool, direction: Tuple[float, float],
                        camera_plane: Tuple[float, float]):
    """
    Get a list of the intersection positions and distances of each column's ray
    for a particular wall map by utilising raycasting. Tuples are in format
    (coordinate, distance, euclidean_squared, side_was_ns). Also gets a list of
    visible sprites as tuples (coordinate, type, distance) where type is either
    END_POINT, KEY, MONSTER, or START_POINT.
    """
    columns: List[Tuple[Tuple[float, float], float, float, bool]] = []
    sprites: List[Tuple[Tuple[float, float], int, float]] = []
    for index in range(display_columns):
        camera_x = 2 * index / display_columns - 1
        cast_direction = (
            direction[0] + camera_plane[0] * camera_x,
            direction[1] + camera_plane[1] * camera_x,
        )
        result, new_sprites = get_first_collision(
            current_level, cast_direction, edge_is_wall
        )
        if result is None:
            columns.append(((0.0, 0.0), float('inf'), float('inf'), False))
        else:
            columns.append(result)
        for new in new_sprites:
            if new[0:2] not in (x[0:2] for x in sprites):
                sprites.append(new)
    return columns, sprites


def no_sqrt_coord_distance(coord_a: Tuple[float, float],
                           coord_b: Tuple[float, float]):
    """
    Calculate the euclidean distance squared between two grid coordinates.
    """
    # Square root isn't performed because it's unnecessary for simply sorting
    # (euclidean distance is never used for actual render distance - that would
    # cause fisheye)
    return (coord_b[0] - coord_a[0]) ** 2 + (coord_b[1] - coord_a[1]) ** 2
