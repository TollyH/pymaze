"""
Contains functions related to the raycast rendering used to generate pseudo-3D
graphics.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import level
import net_data

# Sprite types
END_POINT = 0
END_POINT_ACTIVE = 1
KEY = 2
MONSTER = 3
START_POINT = 4
FLAG = 5
KEY_SENSOR = 6
MONSTER_SPAWN = 7
GUN = 8
DECORATION = 9
OTHER_PLAYER = 10

# Wall directions
NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3


@dataclass
class Collision:
    """
    Represents a ray collision with either a sprite or a wall. Stores the
    coordinate of the collision and the squared euclidean distance from the
    player to that coordinate. This distance should be used for sorting only
    and not for drawing, as that would create a fisheye effect.
    """
    coordinate: Tuple[float, float]
    euclidean_squared: float
    tile: Tuple[int, int]


@dataclass
class WallCollision(Collision):
    """
    Subclass of Collision. Represents a ray collision with a wall. Tile is the
    absolute coordinates of the wall that was hit, side is either NORTH, SOUTH,
    EAST, or WEST depending on which side was hit by the ray, and draw_distance
    is the distance value that should be used for actual rendering. Index is
    used when raycasting the whole screen to identify the order that the
    columns need to go in — alone it is irrelevant and is -1 by default.
    """
    draw_distance: float
    side: int
    index: int = -1


@dataclass
class SpriteCollision(Collision):
    """
    Subclass of Collision. Represents a ray collision with a sprite of a
    particular type, being one of the constants defined in this file.
    If the type is OTHER_PLAYER, player_index will contain the index of the
    player that was hit in the provided players list.
    """
    type: int
    player_index: Optional[int] = None


def get_first_collision(current_level: level.Level,
                        direction: Tuple[float, float],
                        edge_is_wall: bool, players: Sequence[net_data.Player]
                        ) -> Tuple[
                                Optional[WallCollision], List[SpriteCollision]
                             ]:
    """
    Find the first intersection of a wall tile by a ray travelling at the
    specified direction from a particular origin. The result will always be a
    tuple, of which the first item will be None if no collision occurs before
    the edge of the wall map, or a WallCollision if a collision did occur.
    The second tuple item is always list of SpriteCollision.
    """
    # Prevent divide by 0
    if direction[0] == 0:
        direction = (1e-30, direction[1])
    if direction[1] == 0:
        direction = (direction[0], 1e-30)
    # When traversing one unit in a direction, what will the coordinate of the
    # other direction increase by?
    step_size = (abs(1 / direction[0]), abs(1 / direction[1]))
    current_tile = current_level.player_grid_coords
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
    # Stores whether a North/South or East/West wall was hit.
    side_was_ns = False
    tile_found = False
    sprites: List[SpriteCollision] = []
    first_check = True
    while not tile_found:
        # Move along ray, unless this is the first check in which case we want
        # to check our current square.
        if not first_check:
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
        first_check = False

        if current_level.is_coord_in_bounds(current_tile):
            # Collision check
            if current_level[current_tile, level.PRESENCE]:
                tile_found = True
            else:
                if current_tile in current_level.exit_keys:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, KEY
                    ))
                elif current_tile in current_level.key_sensors:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, KEY_SENSOR
                    ))
                elif current_tile in current_level.guns:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, GUN
                    ))
                elif current_tile in current_level.decorations:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, DECORATION
                    ))
                elif current_level.end_point == current_tile:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, END_POINT
                        if len(current_level.exit_keys) > 0 else
                        END_POINT_ACTIVE
                    ))
                elif current_level.monster_start == current_tile:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, MONSTER_SPAWN
                    ))
                elif current_level.start_point == current_tile:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, START_POINT
                    ))
                if current_level.monster_coords == current_tile:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, MONSTER
                    ))
                if current_tile in current_level.player_flags:
                    sprites.append(SpriteCollision(
                        (current_tile[0] + 0.5, current_tile[1] + 0.5),
                        no_sqrt_coord_distance(
                            current_level.player_coords,
                            (current_tile[0] + 0.5, current_tile[1] + 0.5)
                        ), current_tile, FLAG
                    ))
                for i, plr in enumerate(players):
                    if plr.grid_pos == current_tile:
                        plr_pos = plr.pos.to_tuple()
                        sprites.append(SpriteCollision(
                            plr_pos, no_sqrt_coord_distance(
                                current_level.player_coords, (
                                    current_level.player_coords[0]
                                    + direction[0] * distance,
                                    current_level.player_coords[1]
                                    + direction[1] * distance
                                )
                            ), current_tile, OTHER_PLAYER, i
                        ))
        else:
            # Edge of wall map has been reached, yet no wall in sight.
            if edge_is_wall:
                tile_found = True
            else:
                return None, sprites
    # If this point is reached, a wall tile has been found.
    collision_point = (
        current_level.player_coords[0] + direction[0] * distance,
        current_level.player_coords[1] + direction[1] * distance
    )
    if not side_was_ns:
        return WallCollision(
            collision_point, no_sqrt_coord_distance(
                current_level.player_coords, collision_point
            ), current_tile, dimension_ray_length[0] - step_size[0],
            EAST if step[0] < 0 else WEST
        ), sprites
    return WallCollision(
        collision_point, no_sqrt_coord_distance(
            current_level.player_coords, collision_point
        ), current_tile, dimension_ray_length[1] - step_size[1],
        SOUTH if step[1] < 0 else NORTH
    ), sprites


def get_columns_sprites(display_columns: int, current_level: level.Level,
                        edge_is_wall: bool, direction: Tuple[float, float],
                        camera_plane: Tuple[float, float],
                        players: List[net_data.Player]
                        ) -> Tuple[List[WallCollision], List[SpriteCollision]]:
    """
    Get a list of the intersection positions and distances of each column's ray
    for a particular wall map by utilising raycasting. Tuples are in format
    (coordinate, tile, distance, euclidean_squared, side). Also gets a
    list of visible sprites as tuples (coordinate, type, distance) where type
    is one of the constants defined in this file.
    """
    columns: List[WallCollision] = []
    sprites: List[SpriteCollision] = []
    for index in range(display_columns):
        camera_x = 2 * index / display_columns - 1
        cast_direction = (
            direction[0] + camera_plane[0] * camera_x,
            direction[1] + camera_plane[1] * camera_x,
        )
        result, new_sprites = get_first_collision(
            current_level, cast_direction, edge_is_wall, players
        )
        if result is None:
            columns.append(
                WallCollision(
                    (0.0, 0.0), float('inf'), (0, 0), float('inf'), NORTH,
                    index
                )
            )
        else:
            result.index = index
            columns.append(result)
        for new in new_sprites:
            if (new.coordinate, new.type) not in (
                    (x.coordinate, x.type) for x in sprites):
                sprites.append(new)
    return columns, sprites


def no_sqrt_coord_distance(coord_a: Tuple[float, float],
                           coord_b: Tuple[float, float]) -> float:
    """
    Calculate the euclidean distance squared between two grid coordinates.
    """
    # Square root isn't performed because it's unnecessary for simply sorting
    # (euclidean distance is never used for actual render distance — that would
    # cause fisheye)
    return (coord_b[0] - coord_a[0]) ** 2 + (coord_b[1] - coord_a[1]) ** 2
