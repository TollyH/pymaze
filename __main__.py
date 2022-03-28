"""
PyGame Maze - Copyright © 2022  Ptolemy Hill and Finlay Griffiths

The main script for the game. Creates and draws to the game window, as well as
receiving and interpreting player input and recording time and movement scores.
Also handles time-based events such as monster movement and spawning.
"""
import math
import os
import pickle
import random
import sys
from glob import glob
from typing import List, Literal, Set, Tuple

import pygame

import config_loader as cfg
import raycasting
from level import floor_coordinates
from maze_levels import levels

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
    """
    Main function for the maze game. Manages all input, output, and timing.
    """
    # Change working directory to the directory where the script is located
    # Prevents issues with required files not being found
    os.chdir(os.path.dirname(__file__))
    pygame.init()

    # Minimum window resolution is 500x500
    screen = pygame.display.set_mode((
        max(cfg.VIEWPORT_WIDTH, 500), max(cfg.VIEWPORT_HEIGHT + 50, 500)
    ))
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    facing_directions = [(0.0, 1.0)] * len(levels)
    # Camera planes are always perpendicular to facing directions
    camera_planes = [(-cfg.DISPLAY_FOV / 100, 0.0)] * len(levels)
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
    darkener = pygame.Surface((cfg.TEXTURE_WIDTH, cfg.TEXTURE_HEIGHT))
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
        sprite_textures[raycasting.MONSTER],
        (cfg.VIEWPORT_WIDTH, cfg.VIEWPORT_HEIGHT)
    )
    monster_jumpscare_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_jumpscare.wav")
    )
    monster_spotted_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_spotted.wav")
    )

    enable_mouse_control = False
    old_mouse_pos = (cfg.VIEWPORT_WIDTH // 2, cfg.VIEWPORT_HEIGHT // 2)

    display_map = False
    display_compass = False
    display_rays = False
    display_solutions = False

    current_level = 0
    monster_timeouts = [0.0] * len(levels)
    monster_spotted = [cfg.MONSTER_SPOT_TIMEOUT] * len(levels)
    compass_times = [cfg.COMPASS_TIME] * len(levels)
    compass_burned_out = [False] * len(levels)
    compass_charge_delays = [cfg.COMPASS_CHARGE_DELAY] * len(levels)
    flicker_time_remaining = [0.0] * len(levels)

    # Game loop
    while True:
        # Limit FPS and record time last frame took to render
        frame_time = clock.tick(cfg.FRAME_RATE_LIMIT) / 1000
        display_column_width = cfg.VIEWPORT_WIDTH // cfg.DISPLAY_COLUMNS
        tile_width = cfg.VIEWPORT_WIDTH // levels[current_level].dimensions[0]
        tile_height = (
            cfg.VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
        )
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
                    if not display_map or cfg.ENABLE_CHEAT_MAP:
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
                        cfg.VIEWPORT_WIDTH
                        // levels[current_level].dimensions[0]
                    )
                    tile_height = (
                        cfg.VIEWPORT_HEIGHT
                        // levels[current_level].dimensions[1]
                    )
                    pygame.display.set_caption(
                        f"Maze - Level {current_level + 1}"
                    )
                elif event.key == pygame.K_r:
                    levels[current_level].reset()
                    facing_directions[current_level] = (0.0, 1.0)
                    camera_planes[current_level] = (
                        -cfg.DISPLAY_FOV / 100, 0.0
                    )
                    monster_timeouts[current_level] = 0.0
                    monster_spotted[current_level] = cfg.MONSTER_SPOT_TIMEOUT
                    compass_times[current_level] = cfg.COMPASS_TIME
                    compass_burned_out[current_level] = False
                    flicker_time_remaining[current_level] = 0.0
                    time_scores[current_level] = 0
                    move_scores[current_level] = 0
                    has_started_level[current_level] = False
                    display_compass = False
                    if not cfg.ENABLE_CHEAT_MAP:
                        display_map = False
                elif event.key == pygame.K_SPACE:
                    pressed = pygame.key.get_pressed()
                    if pressed[pygame.K_RCTRL] or pressed[pygame.K_LCTRL]:
                        display_rays = not display_rays
                    elif pressed[pygame.K_RALT] or pressed[pygame.K_LALT]:
                        display_solutions = not display_solutions
                    else:
                        display_map = not display_map
                        if not cfg.ENABLE_CHEAT_MAP:
                            display_compass = False
                elif event.key == pygame.K_ESCAPE:
                    enable_mouse_control = False
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_coords = pygame.mouse.get_pos()
                if (mouse_coords[0] <= cfg.VIEWPORT_WIDTH
                        and event.button == pygame.BUTTON_LEFT):
                    enable_mouse_control = not enable_mouse_control
                    if enable_mouse_control:
                        pygame.mouse.set_pos(
                            (cfg.VIEWPORT_WIDTH // 2, cfg.VIEWPORT_HEIGHT // 2)
                        )
                        old_mouse_pos = (
                            cfg.VIEWPORT_WIDTH // 2, cfg.VIEWPORT_HEIGHT // 2
                        )
                    # Hide cursor and confine to window if controlling with
                    # mouse
                    pygame.mouse.set_visible(not enable_mouse_control)
                    pygame.event.set_grab(enable_mouse_control)
                elif (cfg.ALLOW_REALTIME_EDITING and cfg.ENABLE_CHEAT_MAP
                        and event.button == pygame.BUTTON_LEFT
                        and mouse_coords[0] > cfg.VIEWPORT_WIDTH
                        and mouse_coords[1] >= 50):
                    clicked_tile = (
                        (mouse_coords[0] - cfg.VIEWPORT_WIDTH) // tile_width,
                        (mouse_coords[1] - 50) // tile_height
                    )
                    levels[current_level][clicked_tile] = (
                        not levels[current_level][clicked_tile]
                    )
            elif (event.type == pygame.MOUSEMOTION and enable_mouse_control
                    and (not display_map or cfg.ENABLE_CHEAT_MAP)):
                mouse_coords = pygame.mouse.get_pos()
                relative_pos = (
                    old_mouse_pos[0] - mouse_coords[0],
                    old_mouse_pos[1] - mouse_coords[1]
                )
                # Wrap mouse around screen edges
                if mouse_coords[0] == 0:
                    pygame.mouse.set_pos(
                        (cfg.VIEWPORT_WIDTH - 2, mouse_coords[1])
                    )
                elif mouse_coords[0] >= cfg.VIEWPORT_WIDTH - 1:
                    pygame.mouse.set_pos((1, mouse_coords[1]))
                turn_speed_mod = cfg.TURN_SPEED * -relative_pos[0] * 0.0025
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
                old_mouse_pos = pygame.mouse.get_pos()

        if (display_map and cfg.ENABLE_CHEAT_MAP
                and screen.get_size()[0] < cfg.VIEWPORT_WIDTH * 2):
            screen = pygame.display.set_mode(
                (
                    max(cfg.VIEWPORT_WIDTH * 2, 500),
                    max(cfg.VIEWPORT_HEIGHT + 50, 500)
                )
            )
        elif (not display_map and cfg.ENABLE_CHEAT_MAP
                and screen.get_size()[0] > cfg.VIEWPORT_WIDTH):
            screen = pygame.display.set_mode(
                (
                    max(cfg.VIEWPORT_WIDTH, 500),
                    max(cfg.VIEWPORT_HEIGHT + 50, 500)
                )
            )

        old_grid_position = floor_coordinates(
            levels[current_level].player_coords
        )
        # Do not allow player to move while map is open if cheat map is not
        # enabled
        if cfg.ENABLE_CHEAT_MAP or not display_map:
            # Held down keys
            pressed_keys = pygame.key.get_pressed()
            move_multiplier = 1
            if pressed_keys[pygame.K_RCTRL] or pressed_keys[pygame.K_LCTRL]:
                move_multiplier *= cfg.CRAWL_MULTIPLIER
            if pressed_keys[pygame.K_RSHIFT] or pressed_keys[pygame.K_LSHIFT]:
                move_multiplier *= cfg.RUN_MULTIPLIER
            # Ensure framerate does not affect speed values
            turn_speed_mod = frame_time * cfg.TURN_SPEED
            move_speed_mod = frame_time * cfg.MOVE_SPEED
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
            if cfg.MONSTER_SOUND_ON_KILL and has_started_level[current_level]:
                monster_jumpscare_sound.play()
                has_started_level[current_level] = False
            if cfg.MONSTER_DISPLAY_ON_KILL:
                screen.blit(monster_texture_scaled, (
                    0, 50, cfg.VIEWPORT_WIDTH, cfg.VIEWPORT_HEIGHT
                ))
        else:
            if has_started_level[current_level]:
                time_scores[current_level] += frame_time
                monster_timeouts[current_level] += frame_time
                if (monster_spotted[current_level]
                        < cfg.MONSTER_SPOT_TIMEOUT):
                    monster_spotted[current_level] += frame_time
                    if (monster_spotted[current_level]
                            > cfg.MONSTER_SPOT_TIMEOUT):
                        monster_spotted[current_level] = (
                            cfg.MONSTER_SPOT_TIMEOUT
                        )
                if (display_compass and not compass_burned_out[current_level]
                        and levels[current_level].monster_coords is not None):
                    compass_charge_delays[current_level] = (
                        cfg.COMPASS_CHARGE_DELAY
                    )
                    compass_times[current_level] -= frame_time
                    if compass_times[current_level] <= 0.0:
                        compass_times[current_level] = 0.0
                        compass_burned_out[current_level] = True
                elif compass_times[current_level] < cfg.COMPASS_TIME:
                    if (compass_charge_delays[current_level] == 0.0
                            or compass_burned_out[current_level]):
                        multiplier = 1 / (
                            cfg.COMPASS_CHARGE_BURN_MULTIPLIER
                            if compass_burned_out[current_level] else
                            cfg.COMPASS_CHARGE_NORM_MULTIPLIER
                        )
                        compass_times[current_level] += frame_time * multiplier
                        if compass_times[current_level] >= cfg.COMPASS_TIME:
                            compass_times[current_level] = cfg.COMPASS_TIME
                            compass_burned_out[current_level] = False
                    elif compass_charge_delays[current_level] > 0.0:
                        compass_charge_delays[current_level] -= frame_time
                        if compass_charge_delays[current_level] < 0.0:
                            compass_charge_delays[current_level] = 0.0
                monster_wait = levels[current_level].monster_wait
                if (cfg.MONSTER_ENABLED and monster_wait is not None
                    and time_scores[current_level] > (
                            monster_wait
                            if cfg.MONSTER_START_OVERRIDE is None else
                            cfg.MONSTER_START_OVERRIDE
                        )
                        and monster_timeouts[current_level]
                        > cfg.MONSTER_MOVEMENT_WAIT):
                    levels[current_level].move_monster()
                    monster_timeouts[current_level] = 0
                    monster_coords = levels[current_level].monster_coords
                    if (monster_coords is not None
                            and cfg.MONSTER_FLICKER_LIGHTS
                            and flicker_time_remaining[current_level] <= 0):
                        flicker_time_remaining[current_level] = 0.0
                        distance = raycasting.no_sqrt_coord_distance(
                            levels[current_level].player_coords,
                            monster_coords
                        )
                        # Flicker on every monster movement when close.
                        # Also don't divide by anything less than 1, it will
                        # have no more effect than just 1.
                        distance = max(1, distance - 10)
                        # < 1 exponent makes probability decay less with
                        # distance
                        if random.random() < 1 / distance ** 0.6:
                            flicker_time_remaining[current_level] = (
                                random.uniform(0.0, 0.5)
                            )
            screen.fill(GREY)
            if not display_map or cfg.ENABLE_CHEAT_MAP:
                # Ceiling
                pygame.draw.rect(
                    screen, BLUE,
                    (0, 50, cfg.VIEWPORT_WIDTH, cfg.VIEWPORT_HEIGHT // 2)
                )
                monster_coords = levels[current_level].monster_coords
                # Floor
                pygame.draw.rect(
                    screen, LIGHT_GREY,
                    (
                        0, cfg.VIEWPORT_HEIGHT // 2 + 50,
                        cfg.VIEWPORT_WIDTH, cfg.VIEWPORT_HEIGHT // 2
                    )
                )

            if not display_map or cfg.ENABLE_CHEAT_MAP:
                columns, sprites = raycasting.get_columns_sprites(
                    cfg.DISPLAY_COLUMNS, levels[current_level],
                    cfg.DRAW_MAZE_EDGE_AS_WALL,
                    facing_directions[current_level],
                    camera_planes[current_level]
                )
            else:
                columns = []
                sprites = []
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
                        (cfg.VIEWPORT_WIDTH / 2)
                        * (1 + transformation[0] / transformation[1])
                    )
                    if (screen_x_pos
                            > cfg.VIEWPORT_WIDTH + cfg.TEXTURE_WIDTH // 2
                            or screen_x_pos < -cfg.TEXTURE_WIDTH // 2):
                        continue
                    sprite_size = (
                        abs(cfg.VIEWPORT_WIDTH // transformation[1]),
                        abs(cfg.VIEWPORT_HEIGHT // transformation[1])
                    )
                    scaled_texture = pygame.transform.scale(
                        sprite_textures[sprite_type], sprite_size
                    )
                    screen.blit(
                        scaled_texture,
                        (
                            screen_x_pos - sprite_size[0] // 2,
                            cfg.VIEWPORT_HEIGHT // 2 - sprite_size[1] // 2 + 50
                        )
                    )
                    if sprite_type == raycasting.MONSTER:
                        if (cfg.MONSTER_SOUND_ON_SPOT and
                                monster_spotted[current_level]
                                == cfg.MONSTER_SPOT_TIMEOUT):
                            monster_spotted_sound.play()
                        monster_spotted[current_level] = 0.0
                elif object_type == type_column:
                    coord, distance, _, side_was_ns = columns[index]
                    # Edge of maze when drawing maze edges as walls is disabled
                    if distance == float('inf'):
                        continue
                    if display_rays:
                        ray_end_coords.append(coord)
                    # Prevent division by 0
                    distance = max(1e-5, distance)
                    column_height = round(cfg.VIEWPORT_HEIGHT / distance)
                    texture_draw_successful = False
                    if cfg.TEXTURES_ENABLED:
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
                                position_along_wall * cfg.TEXTURE_WIDTH
                            )
                            if (not side_was_ns and
                                    facing_directions[current_level][0] > 0):
                                texture_x = cfg.TEXTURE_WIDTH - texture_x - 1
                            elif (side_was_ns and
                                    facing_directions[current_level][1] < 0):
                                texture_x = cfg.TEXTURE_WIDTH - texture_x - 1
                            draw_x = display_column_width * index
                            draw_y = max(
                                0,
                                -column_height // 2 + cfg.VIEWPORT_HEIGHT // 2
                            ) + 50
                            # Get a single column of pixels
                            pixel_column = texture.subsurface(
                                texture_x, 0, 1, cfg.TEXTURE_HEIGHT
                            )
                            if (column_height > cfg.VIEWPORT_HEIGHT
                                    and column_height
                                    > cfg.TEXTURE_SCALE_LIMIT):
                                overlap = math.floor(
                                    (column_height - cfg.VIEWPORT_HEIGHT)
                                    / (
                                        (column_height - cfg.TEXTURE_HEIGHT)
                                        / cfg.TEXTURE_HEIGHT
                                    )
                                )
                                # Crop column so we are only scaling pixels
                                # that we will use to boost performance, at the
                                # cost of making textures uneven
                                pixel_column = pixel_column.subsurface(
                                    0, overlap // 2,
                                    1, cfg.TEXTURE_HEIGHT - overlap
                                )
                            pixel_column = pygame.transform.scale(
                                pixel_column,
                                (
                                    display_column_width,
                                    min(column_height, cfg.VIEWPORT_HEIGHT)
                                    if column_height > cfg.TEXTURE_SCALE_LIMIT
                                    else column_height
                                )
                            )
                            if (cfg.VIEWPORT_HEIGHT < column_height
                                    <= cfg.TEXTURE_SCALE_LIMIT):
                                overlap = (
                                    column_height - cfg.VIEWPORT_HEIGHT
                                ) // 2
                                pixel_column = pixel_column.subsurface(
                                    0, overlap,
                                    display_column_width, cfg.VIEWPORT_HEIGHT
                                )
                            screen.blit(pixel_column, (draw_x, draw_y))
                            texture_draw_successful = True
                    if not texture_draw_successful:
                        column_height = min(column_height, cfg.VIEWPORT_HEIGHT)
                        colour = DARK_GREY if side_was_ns else BLACK
                        pygame.draw.rect(
                            screen, colour, (
                                display_column_width * index,
                                max(
                                    0,
                                    -column_height // 2
                                    + cfg.VIEWPORT_HEIGHT // 2
                                ) + 50,
                                display_column_width, column_height
                            )
                        )
            if display_map:
                x_offset = cfg.VIEWPORT_WIDTH if cfg.ENABLE_CHEAT_MAP else 0
                solutions: List[List[Tuple[int, int]]] = []
                # A set of all coordinates appearing in any solution
                solution_coords: Set[Tuple[int, int]] = set()
                if (display_solutions and not cfg.ALLOW_REALTIME_EDITING
                        and cfg.ENABLE_CHEAT_MAP):
                    solutions = levels[current_level].find_possible_paths()
                    solution_coords = {x for y in solutions[1:] for x in y}
                for y, row in enumerate(levels[current_level].wall_map):
                    for x, point in enumerate(row):
                        if floor_coordinates(
                                levels[current_level].player_coords) == (x, y):
                            colour = BLUE
                        elif (levels[current_level].monster_coords == (x, y)
                                and cfg.ENABLE_CHEAT_MAP):
                            colour = DARK_RED
                        elif ((x, y) in levels[current_level].exit_keys
                                and cfg.ENABLE_CHEAT_MAP):
                            colour = GOLD
                        elif (x, y) in levels[current_level].player_flags:
                            colour = LIGHT_BLUE
                        elif levels[current_level].start_point == (x, y):
                            colour = RED
                        elif (levels[current_level].end_point == (x, y)
                                and cfg.ENABLE_CHEAT_MAP):
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
                if display_rays and cfg.ENABLE_CHEAT_MAP:
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

            monster_coords = levels[current_level].monster_coords
            if (monster_coords is not None
                    and (not display_map or cfg.ENABLE_CHEAT_MAP)):
                # Darken viewport intermittently based on monster distance
                if cfg.MONSTER_FLICKER_LIGHTS:
                    if flicker_time_remaining[current_level] > 0:
                        ceiling_darkener = pygame.Surface(
                            (cfg.VIEWPORT_WIDTH, cfg.VIEWPORT_HEIGHT)
                        )
                        ceiling_darkener.fill(BLACK)
                        ceiling_darkener.set_alpha(127)
                        screen.blit(ceiling_darkener, (0, 50))
                        flicker_time_remaining[current_level] -= frame_time
                        if flicker_time_remaining[current_level] < 0:
                            flicker_time_remaining[current_level] = 0.0

            if display_compass:
                compass_outer_radius = cfg.VIEWPORT_WIDTH // 6
                compass_inner_radius = (
                    compass_outer_radius - cfg.VIEWPORT_WIDTH // 100
                )
                compass_centre = (
                    cfg.VIEWPORT_WIDTH - compass_outer_radius
                    - cfg.VIEWPORT_WIDTH // 50,
                    cfg.VIEWPORT_HEIGHT + 50 - compass_outer_radius
                    - cfg.VIEWPORT_WIDTH // 50
                )
                pygame.draw.circle(
                    screen, GREY, compass_centre, compass_outer_radius
                )
                pygame.draw.circle(
                    screen, DARK_GREY, compass_centre, compass_inner_radius
                )
                monster_coords = levels[current_level].monster_coords
                if (monster_coords is not None
                        and not compass_burned_out[current_level]):
                    monster_coords = (
                        monster_coords[0] + 0.5, monster_coords[1] + 0.5
                    )
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
                    line_length = compass_inner_radius * (
                        compass_times[current_level] / cfg.COMPASS_TIME
                    )
                    line_end_coords = floor_coordinates((
                        line_length * math.sin(direction) + compass_centre[0],
                        line_length * math.cos(direction) + compass_centre[1]
                    ))
                    pygame.draw.line(
                        screen, RED, compass_centre, line_end_coords,
                        # Cannot be any thinner than 1px
                        max(1, cfg.VIEWPORT_WIDTH // 100)
                    )
                elif compass_burned_out[current_level]:
                    pygame.draw.circle(
                        screen, RED, compass_centre, compass_inner_radius
                        * (
                            (cfg.COMPASS_TIME - compass_times[current_level])
                            / cfg.COMPASS_TIME
                        )
                    )

            # HUD is drawn last to prevent it being obstructed
            pygame.draw.rect(screen, GREY, (0, 0, cfg.VIEWPORT_WIDTH, 50))
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
