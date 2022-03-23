"""
PyGame Maze - Tolly Hill 2022

The main script for the game. Creates and draws to the game window, as well as
receiving and interpreting player input and recording time and movement scores.
Also handles time-based events such as monster movement and spawning.
"""
import math
import os
import pickle
import sys
from glob import glob
from typing import List, Literal, Set, Tuple

import pygame

import raycasting
from level import floor_coordinates
from maze_levels import levels

# ADVANCED OPTIONS ============================================================

# The dimensions used for the 3D view and the map (not including the HUD).
VIEWPORT_WIDTH = 500
VIEWPORT_HEIGHT = 500

# Whether a more detailed version of the map should be displayed instead of the
# default limited one.
ENABLE_CHEAT_MAP = False

# Whether the monster should be spawned at all.
MONSTER_ENABLED = True
# If this is not None, it will be used as the time taken in seconds to spawn
# the monster, overriding the times specific to each level.
MONSTER_START_OVERRIDE = 0
# How many seconds the monster will wait between each movement.
MONSTER_MOVEMENT_WAIT = 0.5
# Whether the scream sound should be played when the player is killed
MONSTER_SOUND_ON_KILL = True
# Whether the monster should be displayed fullscreen when the player is killed
MONSTER_DISPLAY_ON_KILL = True

# The length of time in seconds that the compass can be used before burning out
COMPASS_TIME = 10.0
# The multiplier applied to COMPASS_TIME that it will take to recharge the
# compass if it isn't burned out
COMPASS_CHARGE_NORM_MULTIPLIER = 0.5
# The multiplier applied to COMPASS_TIME that it will take to recharge the
# compass if it's burned out
COMPASS_CHARGE_BURN_MULTIPLIER = 1.0

# The maximum frames per second that the game will render at. Low values may
# cause the game window to become unresponsive.
FRAME_RATE_LIMIT = 75

# Whether walls will be rendered with the image textures associated with each
# level. Setting this to False will cause all walls to appear in solid colour,
# which may also provide some performance boosts.
TEXTURES_ENABLED = True

# The dimensions of all the PNGs found in the textures folder.
TEXTURE_WIDTH = 128
TEXTURE_HEIGHT = 128

# The maximum height that textures will be stretched to internally before they
# start getting cropped to save on resources. Decreasing this will improve
# performance, at the cost of nearby textures looking jagged.
TEXTURE_SCALE_LIMIT = 10000

# The number of rays that will be cast to determine the height of walls.
# Decreasing this will improve performance, but will decrease visual clarity.
DISPLAY_COLUMNS = VIEWPORT_WIDTH
# Your field of vision corresponds to how spread out the rays being cast are.
# Smaller values result in a narrower field of vision, causing the walls to
# appear wider. A value of 50 will make each grid square appear in the same
# aspect ratio as the 3D frame itself.
DISPLAY_FOV = 50

# Whether maze edges will appear as walls in the 3D view. Disabling this will
# cause the horizon to be visible, slightly ruining the ceiling/floor effect.
DRAW_MAZE_EDGE_AS_WALL = True

# Larger values will result in faster speeds. Move speed is measured in grid
# squares per second, and turn speed in radians per second. Run and crawl
# multipliers are applied when holding Shift or CTRL respectively.
TURN_SPEED = 2.5
MOVE_SPEED = 4.0
RUN_MULTIPLIER = 2.0
CRAWL_MULTIPLIER = 0.5

# Allow the presence of walls to be toggled by clicking on the map. Enabling
# this will disable the ability to view solutions. ENABLE_CHEAT_MAP must be
# True for this to work.
ALLOW_REALTIME_EDITING = False

# =============================================================================

WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)
BLUE = (0x00, 0x30, 0xFF)
LIGHT_BLUE = (0x07, 0xF0, 0xF0)
GOLD = (0xE1, 0xBB, 0x12)
DARK_GOLD = (0x70, 0x5E, 0x09)
GREEN = (0x00, 0xFF, 0x10)
DARK_GREEN = (0x00, 0x80, 0x00)
RED = (0xFF, 0x00, 0x00)
DARK_RED = (0x80, 0x00, 0x00)
PURPLE = (0x87, 0x23, 0xD9)
LILAC = (0xD7, 0xA6, 0xFF)
GREY = (0xAA, 0xAA, 0xAA)
DARK_GREY = (0x20, 0x20, 0x20)
LIGHT_GREY = (0xCD, 0xCD, 0xCD)


def main():
    pygame.init()

    # Minimum window resolution is 500x500
    screen = pygame.display.set_mode(
        (max(VIEWPORT_WIDTH, 500), max(VIEWPORT_HEIGHT + 50, 500))
    )
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    facing_directions = [(0.0, 1.0)] * len(levels)
    # Camera planes are always perpendicular to facing directions
    camera_planes = [(-DISPLAY_FOV / 100, 0.0)] * len(levels)
    time_scores = [0.0] * len(levels)
    move_scores = [0] * len(levels)
    has_started_level = [False] * len(levels)
    if os.path.isfile("highscores.pickle"):
        with open("highscores.pickle", 'rb') as file:
            highscores: List[Tuple[float, int]] = pickle.load(file)
            if len(highscores) < len(levels):
                highscores += [(0.0, 0)] * (len(levels) - len(highscores))
    else:
        highscores: List[Tuple[float, int]] = [(0.0, 0)] * len(levels)

    # Used to create the darker versions of each texture
    darkener = pygame.Surface((TEXTURE_WIDTH, TEXTURE_HEIGHT))
    darkener.fill(BLACK)
    darkener.set_alpha(127)
    # {(level_indices, ...): (light_texture, dark_texture)}
    wall_textures = {
        # Parse wall texture names to tuples of integers
        tuple(int(y) for y in os.path.split(x)[-1].split(".")[0].split("-")):
        (pygame.image.load(x).convert(), pygame.image.load(x).convert())
        for x in glob(os.path.join("textures", "wall", "*.png"))
    }
    for _, (_, surface_to_dark) in wall_textures.items():
        surface_to_dark.blit(darkener, (0, 0))

    sprite_textures = {
        raycasting.KEY: pygame.image.load(
            os.path.join("textures", "sprite", "key.png")
        ).convert_alpha(),
        raycasting.END_POINT: pygame.image.load(
            os.path.join("textures", "sprite", "end_point.png")
        ).convert_alpha(),
        raycasting.MONSTER: pygame.image.load(
            os.path.join("textures", "sprite", "monster.png")
        ).convert_alpha(),
        raycasting.START_POINT: pygame.image.load(
            os.path.join("textures", "sprite", "start_point.png")
        ).convert_alpha(),
        raycasting.FLAG: pygame.image.load(
            os.path.join("textures", "sprite", "flag.png")
        ).convert_alpha(),
        raycasting.END_POINT_ACTIVE: pygame.image.load(
            os.path.join("textures", "sprite", "end_point_active.png")
        ).convert_alpha()
    }

    monster_texture_scaled = pygame.transform.scale(
        sprite_textures[raycasting.MONSTER], (VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
    )
    monster_jumpscare_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_jumpscare.wav")
    )

    display_map = False
    display_compass = False
    display_rays = False
    display_solutions = False

    current_level = 0
    monster_timeouts = [0.0] * len(levels)
    compass_times = [COMPASS_TIME] * len(levels)
    compass_burned_out = [False] * len(levels)

    # Game loop
    while True:
        # Limit FPS and record time last frame took to render
        frame_time = clock.tick(FRAME_RATE_LIMIT) / 1000
        display_column_width = VIEWPORT_WIDTH // DISPLAY_COLUMNS
        tile_width = VIEWPORT_WIDTH // levels[current_level].dimensions[0]
        tile_height = VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Standard "press-once" keys
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    grid_coords = floor_coordinates(
                        levels[current_level].player_coords
                    )
                    if grid_coords in levels[current_level].player_flags:
                        levels[current_level].player_flags.remove(grid_coords)
                    else:
                        levels[current_level].player_flags.add(grid_coords)
                elif event.key == pygame.K_c:
                    if not display_map or ENABLE_CHEAT_MAP:
                        display_compass = not display_compass
                elif event.key in (pygame.K_LEFTBRACKET,
                                   pygame.K_RIGHTBRACKET):
                    if event.key == pygame.K_LEFTBRACKET and current_level > 0:
                        current_level -= 1
                    elif (event.key == pygame.K_RIGHTBRACKET
                            and current_level < len(levels) - 1):
                        current_level += 1
                    else:
                        continue
                    # Adjust tile width and height for new level
                    tile_width = (
                        VIEWPORT_WIDTH // levels[current_level].dimensions[0]
                    )
                    tile_height = (
                        VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
                    )
                    pygame.display.set_caption(
                        f"Maze - Level {current_level + 1}"
                    )
                elif event.key == pygame.K_r:
                    levels[current_level].reset()
                    facing_directions[current_level] = (0.0, 1.0)
                    camera_planes[current_level] = (-DISPLAY_FOV / 100, 0.0)
                    time_scores[current_level] = 0
                    move_scores[current_level] = 0
                    has_started_level[current_level] = False
                elif event.key == pygame.K_SPACE:
                    pressed = pygame.key.get_pressed()
                    if pressed[pygame.K_RCTRL] or pressed[pygame.K_LCTRL]:
                        display_rays = not display_rays
                    elif pressed[pygame.K_RALT] or pressed[pygame.K_LALT]:
                        display_solutions = not display_solutions
                    else:
                        display_map = not display_map
                        if not ENABLE_CHEAT_MAP:
                            display_compass = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_coords = pygame.mouse.get_pos()
                if (ALLOW_REALTIME_EDITING and ENABLE_CHEAT_MAP
                        and event.button == pygame.BUTTON_LEFT
                        and mouse_coords[0] > VIEWPORT_WIDTH
                        and mouse_coords[1] >= 50):
                    clicked_tile = (
                        (mouse_coords[0] - VIEWPORT_WIDTH) // tile_width,
                        (mouse_coords[1] - 50) // tile_height
                    )
                    levels[current_level][clicked_tile] = (
                        not levels[current_level][clicked_tile]
                    )

        if (display_map and ENABLE_CHEAT_MAP
                and screen.get_size()[0] < VIEWPORT_WIDTH * 2):
            screen = pygame.display.set_mode(
                (
                    max(VIEWPORT_WIDTH * 2, 500),
                    max(VIEWPORT_HEIGHT + 50, 500)
                )
            )
        elif (not display_map and ENABLE_CHEAT_MAP
                and screen.get_size()[0] > VIEWPORT_WIDTH):
            screen = pygame.display.set_mode(
                (
                    max(VIEWPORT_WIDTH, 500),
                    max(VIEWPORT_HEIGHT + 50, 500)
                )
            )

        old_grid_position = floor_coordinates(
            levels[current_level].player_coords
        )
        # Do not allow player to move while map is open if cheat map is not
        # enabled
        if ENABLE_CHEAT_MAP or not display_map:
            # Held down keys
            pressed_keys = pygame.key.get_pressed()
            move_multiplier = 1
            if pressed_keys[pygame.K_RCTRL] or pressed_keys[pygame.K_LCTRL]:
                move_multiplier *= CRAWL_MULTIPLIER
            if pressed_keys[pygame.K_RSHIFT] or pressed_keys[pygame.K_LSHIFT]:
                move_multiplier *= RUN_MULTIPLIER
            # Ensure framerate does not affect speed values
            turn_speed_mod = frame_time * TURN_SPEED
            move_speed_mod = frame_time * MOVE_SPEED
            if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    levels[current_level].move_player((
                        facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier,
                        facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier
                    ))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    levels[current_level].move_player((
                        -facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier,
                        -facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier
                    ))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_a]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    levels[current_level].move_player((
                        facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier,
                        -facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier
                    ))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_d]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    levels[current_level].move_player((
                        -facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier,
                        facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier
                    ))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_RIGHT]:
                old_direction = facing_directions[current_level]
                facing_directions[current_level] = (
                    old_direction[0] * math.cos(turn_speed_mod)
                    - old_direction[1] * math.sin(turn_speed_mod),
                    old_direction[0] * math.sin(turn_speed_mod)
                    + old_direction[1] * math.cos(turn_speed_mod)
                )
                old_camera_plane = camera_planes[current_level]
                camera_planes[current_level] = (
                    old_camera_plane[0] * math.cos(turn_speed_mod)
                    - old_camera_plane[1] * math.sin(turn_speed_mod),
                    old_camera_plane[0] * math.sin(turn_speed_mod)
                    + old_camera_plane[1] * math.cos(turn_speed_mod)
                )
            if pressed_keys[pygame.K_LEFT]:
                old_direction = facing_directions[current_level]
                facing_directions[current_level] = (
                    old_direction[0] * math.cos(-turn_speed_mod)
                    - old_direction[1] * math.sin(-turn_speed_mod),
                    old_direction[0] * math.sin(-turn_speed_mod)
                    + old_direction[1] * math.cos(-turn_speed_mod)
                )
                old_camera_plane = camera_planes[current_level]
                camera_planes[current_level] = (
                    old_camera_plane[0] * math.cos(-turn_speed_mod)
                    - old_camera_plane[1] * math.sin(-turn_speed_mod),
                    old_camera_plane[0] * math.sin(-turn_speed_mod)
                    + old_camera_plane[1] * math.cos(-turn_speed_mod)
                )
            # Only count up one move score if player crossed a gridline
            if floor_coordinates(
                    levels[current_level].player_coords) != old_grid_position:
                move_scores[current_level] += 1

        if levels[current_level].won:
            highscores_updated = False
            if (time_scores[current_level] < highscores[current_level][0]
                    or highscores[current_level][0] == 0):
                highscores[current_level] = (
                    time_scores[current_level], highscores[current_level][1]
                )
                highscores_updated = True
            if (move_scores[current_level] < highscores[current_level][1]
                    or highscores[current_level][1] == 0):
                highscores[current_level] = (
                    highscores[current_level][0], move_scores[current_level]
                )
                highscores_updated = True
            if highscores_updated and not os.path.isdir("highscores.pickle"):
                with open("highscores.pickle", 'wb') as file:
                    pickle.dump(highscores, file)
            screen.fill(GREEN)
            time_score_text = font.render(
                f"Time Score: {time_scores[current_level]:.1f}",
                True, BLUE
            )
            move_score_text = font.render(
                f"Move Score: {move_scores[current_level]}",
                True, BLUE
            )
            best_time_score_text = font.render(
                f"Best Time Score: {highscores[current_level][0]:.1f}",
                True, BLUE
            )
            best_move_score_text = font.render(
                f"Best Move Score: {highscores[current_level][1]}",
                True, BLUE
            )
            best_total_time_score_text = font.render(
                f"Best Game Time Score: {sum(x[0] for x in highscores):.1f}",
                True, BLUE
            )
            best_total_move_score_text = font.render(
                f"Best Game Move Score: {sum(x[1] for x in highscores)}",
                True, BLUE
            )
            lower_hint_text = font.render(
                "(Lower scores are better)", True, BLUE
            )
            screen.blit(time_score_text, (10, 10))
            screen.blit(move_score_text, (10, 40))
            screen.blit(best_time_score_text, (10, 90))
            screen.blit(best_move_score_text, (10, 120))
            screen.blit(best_total_time_score_text, (10, 200))
            screen.blit(best_total_move_score_text, (10, 230))
            screen.blit(lower_hint_text, (10, 280))
        elif levels[current_level].killed:
            screen.fill(RED)
            if MONSTER_SOUND_ON_KILL and has_started_level[current_level]:
                monster_jumpscare_sound.play()
                has_started_level[current_level] = False
            if MONSTER_DISPLAY_ON_KILL:
                screen.blit(monster_texture_scaled, (
                    0, 50, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
                ))
        else:
            if has_started_level[current_level]:
                time_scores[current_level] += frame_time
                monster_timeouts[current_level] += frame_time
                if (display_compass and not compass_burned_out[current_level]
                        and levels[current_level].monster_coords is not None):
                    compass_times[current_level] -= frame_time
                    if compass_times[current_level] <= 0.0:
                        compass_times[current_level] = 0.0
                        compass_burned_out[current_level] = True
                elif compass_times[current_level] < COMPASS_TIME:
                    multiplier = 1 / (
                        COMPASS_CHARGE_BURN_MULTIPLIER
                        if compass_burned_out[current_level] else
                        COMPASS_CHARGE_NORM_MULTIPLIER
                    )
                    compass_times[current_level] += frame_time * multiplier
                    if compass_times[current_level] >= COMPASS_TIME:
                        compass_times[current_level] = COMPASS_TIME
                        compass_burned_out[current_level] = False
                monster_wait = levels[current_level].monster_wait
                if (MONSTER_ENABLED and monster_wait is not None
                    and time_scores[current_level] > (
                            monster_wait
                            if MONSTER_START_OVERRIDE is None else
                            MONSTER_START_OVERRIDE
                        )
                        and monster_timeouts[current_level]
                        > MONSTER_MOVEMENT_WAIT):
                    levels[current_level].move_monster()
                    monster_timeouts[current_level] = 0
            screen.fill(GREY)
            # Ceiling
            pygame.draw.rect(
                screen, BLUE,
                (0, 50, VIEWPORT_WIDTH, VIEWPORT_HEIGHT // 2)
            )
            monster_coords = levels[current_level].monster_coords
            if monster_coords is not None:
                # Darken ceiling based on monster distance
                ceiling_darkener = pygame.Surface(
                    (VIEWPORT_WIDTH, VIEWPORT_HEIGHT // 2)
                )
                ceiling_darkener.fill(BLACK)
                ceiling_darkener.set_alpha(
                    round(255 / math.sqrt(raycasting.no_sqrt_coord_distance(
                        levels[current_level].player_coords, monster_coords
                    )))
                )
                screen.blit(ceiling_darkener, (0, 50))
            # Floor
            pygame.draw.rect(
                screen, LIGHT_GREY,
                (
                    0, VIEWPORT_HEIGHT // 2 + 50,
                    VIEWPORT_WIDTH, VIEWPORT_HEIGHT // 2
                )
            )

            columns, sprites = raycasting.get_columns_sprites(
                DISPLAY_COLUMNS, levels[current_level], DRAW_MAZE_EDGE_AS_WALL,
                facing_directions[current_level], camera_planes[current_level]
            )
            type_column = 0
            type_sprite = 1
            # A combination of both wall columns and sprites
            # [(index, type, euclidean_squared), ...]
            objects: List[Tuple[int, Literal[0, 1], float]] = [
                (i, type_column, x[2]) for i, x in enumerate(columns)
            ]
            objects += [
                (i, type_sprite, x[2]) for i, x in enumerate(sprites)
            ]
            # Draw further away objects first so that closer walls obstruct
            # sprites behind them
            objects.sort(key=lambda x: x[2], reverse=True)
            ray_end_coords: List[Tuple[float, float]] = []
            for index, object_type, _ in objects:
                if object_type == type_sprite:
                    coord, sprite_type, _ = sprites[index]
                    relative_pos = (
                        coord[0] - levels[current_level].player_coords[0],
                        coord[1] - levels[current_level].player_coords[1]
                    )
                    inverse_camera = (
                        1 / (
                            camera_planes[current_level][0]
                            * facing_directions[current_level][1]
                            - facing_directions[current_level][0]
                            * camera_planes[current_level][1]
                        )
                    )
                    transformation = (
                        inverse_camera * (
                            facing_directions[current_level][1]
                            * relative_pos[0]
                            - facing_directions[current_level][0]
                            * relative_pos[1]
                        ),
                        inverse_camera * (
                            -camera_planes[current_level][1] * relative_pos[0]
                            + camera_planes[current_level][0] * relative_pos[1]
                        )
                    )
                    # Prevent divisions by 0
                    transformation = (
                        transformation[0] if transformation[0] != 0 else 1e-5,
                        transformation[1] if transformation[1] != 0 else 1e-5
                    )
                    screen_x_pos = math.floor(
                        (VIEWPORT_WIDTH / 2)
                        * (1 + transformation[0] / transformation[1])
                    )
                    if (screen_x_pos > VIEWPORT_WIDTH + TEXTURE_WIDTH // 2
                            or screen_x_pos < -TEXTURE_WIDTH // 2):
                        continue
                    sprite_size = (
                        abs(VIEWPORT_WIDTH // transformation[1]),
                        abs(VIEWPORT_HEIGHT // transformation[1])
                    )
                    scaled_texture = pygame.transform.scale(
                        sprite_textures[sprite_type], sprite_size
                    )
                    screen.blit(
                        scaled_texture,
                        (
                            screen_x_pos - sprite_size[0] // 2,
                            VIEWPORT_HEIGHT // 2 - sprite_size[1] // 2 + 50
                        )
                    )
                elif object_type == type_column:
                    coord, distance, _, side_was_ns = columns[index]
                    # Edge of maze when drawing maze edges as walls is disabled
                    if distance == float('inf'):
                        continue
                    if display_rays:
                        ray_end_coords.append(coord)
                    # Prevent division by 0
                    distance = max(1e-5, distance)
                    column_height = round(VIEWPORT_HEIGHT / distance)
                    texture_draw_successful = False
                    if TEXTURES_ENABLED:
                        both_textures = None
                        for indices, images in wall_textures.items():
                            if current_level in indices:
                                both_textures = images
                                break
                        if both_textures is not None:
                            # Select either light or dark texture
                            # depending on side
                            texture = both_textures[int(side_was_ns)]
                            position_along_wall = coord[
                                int(not side_was_ns)
                            ] % 1
                            texture_x = math.floor(
                                position_along_wall * TEXTURE_WIDTH
                            )
                            if (not side_was_ns and
                                    facing_directions[current_level][0] > 0):
                                texture_x = TEXTURE_WIDTH - texture_x - 1
                            elif (side_was_ns and
                                    facing_directions[current_level][1] < 0):
                                texture_x = TEXTURE_WIDTH - texture_x - 1
                            draw_x = display_column_width * index
                            draw_y = max(
                                0, -column_height // 2 + VIEWPORT_HEIGHT // 2
                            ) + 50
                            # Get a single column of pixels
                            pixel_column = texture.subsurface(
                                texture_x, 0, 1, TEXTURE_HEIGHT
                            )
                            if (column_height > VIEWPORT_HEIGHT
                                    and column_height > TEXTURE_SCALE_LIMIT):
                                overlap = math.floor(
                                    (column_height - VIEWPORT_HEIGHT)
                                    / (
                                        (column_height - TEXTURE_HEIGHT)
                                        / TEXTURE_HEIGHT
                                    )
                                )
                                # Crop column so we are only scaling pixels
                                # that we will use to boost performance, at the
                                # cost of making textures uneven
                                pixel_column = pixel_column.subsurface(
                                    0, overlap // 2,
                                    1, TEXTURE_HEIGHT - overlap
                                )
                            pixel_column = pygame.transform.scale(
                                pixel_column,
                                (
                                    display_column_width,
                                    min(column_height, VIEWPORT_HEIGHT)
                                    if column_height > TEXTURE_SCALE_LIMIT else
                                    column_height
                                )
                            )
                            if (VIEWPORT_HEIGHT < column_height
                                    <= TEXTURE_SCALE_LIMIT):
                                overlap = (
                                    column_height - VIEWPORT_HEIGHT
                                ) // 2
                                pixel_column = pixel_column.subsurface(
                                    0, overlap,
                                    display_column_width, VIEWPORT_HEIGHT
                                )
                            screen.blit(pixel_column, (draw_x, draw_y))
                            texture_draw_successful = True
                    if not texture_draw_successful:
                        column_height = min(column_height, VIEWPORT_HEIGHT)
                        colour = DARK_GREY if side_was_ns else BLACK
                        pygame.draw.rect(
                            screen, colour, (
                                display_column_width * index,
                                max(
                                    0,
                                    -column_height // 2 + VIEWPORT_HEIGHT // 2
                                ) + 50,
                                display_column_width, column_height
                            )
                        )
            if display_map:
                x_offset = VIEWPORT_WIDTH if ENABLE_CHEAT_MAP else 0
                solutions: List[List[Tuple[int, int]]] = []
                # A set of all coordinates appearing in any solution
                solution_coords: Set[Tuple[int, int]] = set()
                if (display_solutions and not ALLOW_REALTIME_EDITING
                        and ENABLE_CHEAT_MAP):
                    solutions = levels[current_level].find_possible_paths()
                    solution_coords = {x for y in solutions[1:] for x in y}
                for y, row in enumerate(levels[current_level].wall_map):
                    for x, point in enumerate(row):
                        if floor_coordinates(
                                levels[current_level].player_coords) == (x, y):
                            colour = BLUE
                        elif (levels[current_level].monster_coords == (x, y)
                                and ENABLE_CHEAT_MAP):
                            colour = DARK_RED
                        elif ((x, y) in levels[current_level].exit_keys
                                and ENABLE_CHEAT_MAP):
                            colour = GOLD
                        elif (x, y) in levels[current_level].player_flags:
                            colour = LIGHT_BLUE
                        elif levels[current_level].start_point == (x, y):
                            colour = RED
                        elif (levels[current_level].end_point == (x, y)
                                and ENABLE_CHEAT_MAP):
                            colour = GREEN
                        elif len(solutions) >= 1 and (x, y) in solutions[0]:
                            colour = PURPLE
                        elif len(solutions) >= 1 and (x, y) in solution_coords:
                            colour = LILAC
                        else:
                            colour = BLACK if point else WHITE
                        pygame.draw.rect(
                            screen, colour, (
                                tile_width * x + x_offset,
                                tile_height * y + 50, tile_width, tile_height
                            )
                        )
                # Raycast rays
                if display_rays and ENABLE_CHEAT_MAP:
                    for point in ray_end_coords:
                        pygame.draw.line(
                            screen, DARK_GOLD, (
                                levels[current_level].player_coords[0]
                                * tile_width + x_offset,
                                levels[current_level].player_coords[1]
                                * tile_height + 50
                            ),
                            (
                                point[0] * tile_width + x_offset,
                                point[1] * tile_height + 50
                            ), 1
                        )
                # Player direction
                pygame.draw.line(
                    screen, DARK_RED, (
                        levels[current_level].player_coords[0] * tile_width
                        + x_offset,
                        levels[current_level].player_coords[1] * tile_height
                        + 50
                    ),
                    (
                        levels[current_level].player_coords[0] * tile_width
                        + x_offset
                        + facing_directions[current_level][0] * tile_width
                        // 2,
                        levels[current_level].player_coords[1] * tile_height
                        + 50 + facing_directions[current_level][1] * tile_width
                        // 2
                    ), 3
                )
                # Exact player position
                pygame.draw.circle(
                    screen, DARK_GREEN, (
                        levels[current_level].player_coords[0] * tile_width
                        + x_offset,
                        levels[current_level].player_coords[1] * tile_height
                        + 50
                    ), tile_width / 8
                )
            elif display_compass:
                pygame.draw.circle(
                    screen, GREY, (VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT + 50),
                    VIEWPORT_WIDTH / 4
                )
                pygame.draw.circle(
                    screen, DARK_GREY,
                    (VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT + 50),
                    VIEWPORT_WIDTH / 4 - 10
                )
                monster_coords = levels[current_level].monster_coords
                if (monster_coords is not None
                        and not compass_burned_out[current_level]):
                    relative_pos = (
                        levels[current_level].player_coords[0]
                        - monster_coords[0],
                        levels[current_level].player_coords[1]
                        - monster_coords[1]
                    )
                    direction = (
                        math.atan2(*relative_pos)
                        - math.atan2(*facing_directions[current_level])
                    )
                    line_length = (VIEWPORT_WIDTH / 4 - 10) * (
                        compass_times[current_level] / COMPASS_TIME
                    )
                    offsets = (
                        VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT + 50
                    )
                    line_end_coords = floor_coordinates((
                        line_length * math.sin(direction) + offsets[0],
                        line_length * math.cos(direction) + offsets[1]
                    ))
                    pygame.draw.line(
                        screen, RED,
                        (VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT + 50),
                        line_end_coords, 4
                    )
                elif compass_burned_out[current_level]:
                    pygame.draw.circle(
                        screen, RED,
                        (VIEWPORT_WIDTH // 2, VIEWPORT_HEIGHT + 50),
                        (VIEWPORT_WIDTH // 4 - 10) * (
                            (COMPASS_TIME - compass_times[current_level])
                            / COMPASS_TIME
                        )
                    )

            # HUD is drawn last to prevent it being obstructed
            pygame.draw.rect(screen, GREY, (0, 0, VIEWPORT_WIDTH, 50))
            time_score_text = font.render(
                f"Time: {time_scores[current_level]:.1f}"
                if has_started_level[current_level] else
                f"Time: {highscores[current_level][0]:.1f}",
                True,
                WHITE if levels[current_level].monster_coords is None else RED
            )
            move_score_text = font.render(
                f"Moves: {move_scores[current_level]}"
                if has_started_level[current_level] else
                f"Moves: {highscores[current_level][1]}",
                True, WHITE
            )
            starting_keys = len(levels[current_level].original_exit_keys)
            remaining_keys = (
                starting_keys - len(levels[current_level].exit_keys)
            )
            keys_text = font.render(
                f"Keys: {remaining_keys}/{starting_keys}", True, WHITE
            )
            screen.blit(time_score_text, (10, 10))
            screen.blit(move_score_text, (180, 10))
            screen.blit(keys_text, (340, 10))
        print(
            f"\r{clock.get_fps():5.2f} FPS - "
            + f"Position ({levels[current_level].player_coords[0]:5.2f},"
            + f"{levels[current_level].player_coords[1]:5.2f}) - "
            + f"Direction ({facing_directions[current_level][0]:5.2f},"
            + f"{facing_directions[current_level][1]:5.2f}) - "
            + f"Camera ({camera_planes[current_level][0]:5.2f},"
            + f"{camera_planes[current_level][1]:5.2f})",
            end="", flush=True
        )
        pygame.display.update()


if __name__ == "__main__":
    main()
