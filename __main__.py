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
from typing import List, Literal, Tuple

import pygame

import config_loader
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

    last_config_edit = os.path.getmtime('config.ini')
    cfg = config_loader.Config()

    # Minimum window resolution is 500x500
    screen = pygame.display.set_mode((
        max(cfg.viewport_width, 500), max(cfg.viewport_height + 50, 500)
    ))
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    # X+Y facing directions, times, moves, etc are specific to each level,
    # so are each stored in a list
    facing_directions = [(0.0, 1.0)] * len(levels)
    # Camera planes are always perpendicular to facing directions
    camera_planes = [(-cfg.display_fov / 100, 0.0)] * len(levels)
    time_scores = [0.0] * len(levels)
    move_scores = [0.0] * len(levels)
    has_started_level = [False] * len(levels)
    if os.path.isfile("highscores.pickle"):
        with open("highscores.pickle", 'rb') as file:
            highscores: List[Tuple[float, float]] = pickle.load(file)
            if len(highscores) < len(levels):
                highscores += [(0.0, 0.0)] * (len(levels) - len(highscores))
    else:
        highscores: List[Tuple[float, float]] = [(0.0, 0.0)] * len(levels)

    # Used to create the darker versions of each texture
    darkener = pygame.Surface((cfg.texture_width, cfg.texture_height))
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

    sky_texture = pygame.image.load(
        os.path.join("textures", "sky.png")
    ).convert_alpha()

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

    jumpscare_monster_texture = pygame.transform.scale(
        pygame.image.load(
            os.path.join("textures", "death_monster.png")
        ).convert_alpha(),
        (cfg.viewport_width, cfg.viewport_height)
    )
    monster_jumpscare_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_jumpscare.wav")
    )
    monster_spotted_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_spotted.wav")
    )

    enable_mouse_control = False
    # Used to calculate gow far mouse has travelled for mouse control
    old_mouse_pos = (cfg.viewport_width // 2, cfg.viewport_height // 2)

    display_map = False
    display_compass = False
    display_rays = False

    is_reset_prompt_shown = False

    current_level = 0
    monster_timeouts = [0.0] * len(levels)
    # How long since the monster was last spotted. Used to prevent the
    # "spotted" jumpscare sound playing repeatedly.
    monster_spotted = [cfg.monster_spot_timeout] * len(levels)
    compass_times = [cfg.compass_time] * len(levels)
    compass_burned_out = [False] * len(levels)
    compass_charge_delays = [cfg.compass_charge_delay] * len(levels)
    flicker_time_remaining = [0.0] * len(levels)

    # Game loop
    while True:
        if os.path.getmtime('config.ini') > last_config_edit:
            # Config has been edited so it should be reloaded.
            last_config_edit = os.path.getmtime('config.ini')
            cfg = config_loader.Config()
        # Limit FPS and record time last frame took to render
        frame_time = clock.tick(cfg.frame_rate_limit) / 1000
        display_column_width = cfg.viewport_width // cfg.display_columns
        # If the width of the display columns does not divide nicely into the
        # total viewport width, there will be a border. This stores the width
        # of however much of the viewport is filled with actual content.
        filled_screen_width = display_column_width * cfg.display_columns
        # Used for the 2D map
        tile_width = cfg.viewport_width // levels[current_level].dimensions[0]
        tile_height = (
            cfg.viewport_height // levels[current_level].dimensions[1]
        )
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Standard "press-once" keys
            elif event.type == pygame.KEYDOWN:
                if not is_reset_prompt_shown:
                    if event.key == pygame.K_f:
                        grid_coords = floor_coordinates(
                            levels[current_level].player_coords
                        )
                        if grid_coords in levels[current_level].player_flags:
                            levels[current_level].player_flags.remove(
                                grid_coords
                            )
                        else:
                            levels[current_level].player_flags.add(
                                grid_coords
                            )
                    elif event.key == pygame.K_c:
                        # Compass and map cannot be displayed together
                        if not display_map or cfg.enable_cheat_map:
                            display_compass = not display_compass
                    elif event.key in (pygame.K_LEFTBRACKET,
                                       pygame.K_RIGHTBRACKET):
                        if (event.key == pygame.K_LEFTBRACKET
                                and current_level > 0):
                            current_level -= 1
                        elif (event.key == pygame.K_RIGHTBRACKET
                                and current_level < len(levels) - 1):
                            current_level += 1
                        else:
                            continue
                        # Adjust tile width and height for new level
                        tile_width = (
                            cfg.viewport_width
                            // levels[current_level].dimensions[0]
                        )
                        tile_height = (
                            cfg.viewport_height
                            // levels[current_level].dimensions[1]
                        )
                        pygame.display.set_caption(
                            f"Maze - Level {current_level + 1}"
                        )
                    elif event.key == pygame.K_r:
                        is_reset_prompt_shown = True
                    elif event.key == pygame.K_SPACE:
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_RCTRL] or pressed[pygame.K_LCTRL]:
                            display_rays = not display_rays
                        else:
                            display_map = not display_map
                            if not cfg.enable_cheat_map:
                                display_compass = False
                    elif event.key == pygame.K_ESCAPE:
                        enable_mouse_control = False
                        # Return the mouse to normal
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                else:
                    if event.key == pygame.K_y:
                        # Resets almost all attributes related to the current
                        # level. Position, direction, monster, compass, etc.
                        is_reset_prompt_shown = False
                        levels[current_level].reset()
                        facing_directions[current_level] = (0.0, 1.0)
                        camera_planes[current_level] = (
                            -cfg.display_fov / 100, 0.0
                        )
                        monster_timeouts[current_level] = 0.0
                        monster_spotted[current_level] = (
                            cfg.monster_spot_timeout
                        )
                        compass_times[current_level] = cfg.compass_time
                        compass_burned_out[current_level] = False
                        flicker_time_remaining[current_level] = 0.0
                        time_scores[current_level] = 0.0
                        move_scores[current_level] = 0.0
                        has_started_level[current_level] = False
                        display_compass = False
                        if not cfg.enable_cheat_map:
                            display_map = False
                    elif event.key == pygame.K_n:
                        is_reset_prompt_shown = False
            elif (event.type == pygame.MOUSEBUTTONDOWN
                    and not is_reset_prompt_shown):
                mouse_coords = pygame.mouse.get_pos()
                if (mouse_coords[0] <= cfg.viewport_width
                        and event.button == pygame.BUTTON_LEFT):
                    enable_mouse_control = not enable_mouse_control
                    if enable_mouse_control:
                        pygame.mouse.set_pos(
                            (cfg.viewport_width // 2, cfg.viewport_height // 2)
                        )
                        old_mouse_pos = (
                            cfg.viewport_width // 2, cfg.viewport_height // 2
                        )
                    # Hide cursor and confine to window if controlling with
                    # mouse
                    pygame.mouse.set_visible(not enable_mouse_control)
                    pygame.event.set_grab(enable_mouse_control)
                elif (cfg.allow_realtime_editing and cfg.enable_cheat_map
                        and event.button == pygame.BUTTON_LEFT
                        and mouse_coords[0] > cfg.viewport_width
                        and mouse_coords[1] >= 50):
                    clicked_tile = (
                        (mouse_coords[0] - cfg.viewport_width) // tile_width,
                        (mouse_coords[1] - 50) // tile_height
                    )
                    levels[current_level][clicked_tile] = (
                        not levels[current_level][clicked_tile]
                    )
            elif (event.type == pygame.MOUSEMOTION and enable_mouse_control
                    and (not display_map or cfg.enable_cheat_map)
                    and not is_reset_prompt_shown):
                mouse_coords = pygame.mouse.get_pos()
                # How far the mouse has actually moved since the last frame
                relative_pos = (
                    old_mouse_pos[0] - mouse_coords[0],
                    old_mouse_pos[1] - mouse_coords[1]
                )
                # Wrap mouse around screen edges
                if mouse_coords[0] == 0:
                    pygame.mouse.set_pos(
                        (cfg.viewport_width - 2, mouse_coords[1])
                    )
                elif mouse_coords[0] >= cfg.viewport_width - 1:
                    pygame.mouse.set_pos((1, mouse_coords[1]))
                # 0.0025 multiplier makes mouse speed more sensible while still
                # using the same turn speed multiplier as the keyboard
                turn_speed_mod = cfg.turn_speed * -relative_pos[0] * 0.0025
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

        target_screen_size = (
            # Window must be at least 500x500
            max(
                cfg.viewport_width *
                (2 if cfg.enable_cheat_map and display_map else 1), 500
            ),
            max(cfg.viewport_height + 50, 500)
        )
        if (screen.get_size()[0] != target_screen_size[0]
                or screen.get_size()[1] != target_screen_size[1]):
            screen = pygame.display.set_mode(target_screen_size)

        old_position = levels[current_level].player_coords
        # Do not allow player to move while map is open if cheat map is not
        # enabled - or if the reset prompt is open
        if ((cfg.enable_cheat_map or not display_map)
                and not is_reset_prompt_shown):
            # Held down keys - movement and turning
            pressed_keys = pygame.key.get_pressed()
            move_multiplier = 1
            if pressed_keys[pygame.K_RCTRL] or pressed_keys[pygame.K_LCTRL]:
                move_multiplier *= cfg.crawl_multiplier
            if pressed_keys[pygame.K_RSHIFT] or pressed_keys[pygame.K_LSHIFT]:
                move_multiplier *= cfg.run_multiplier
            # Ensure framerate does not affect speed values
            turn_speed_mod = frame_time * cfg.turn_speed
            move_speed_mod = frame_time * cfg.move_speed
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
            move_scores[current_level] += math.sqrt(
                raycasting.no_sqrt_coord_distance(
                    old_position, levels[current_level].player_coords
                )
            )

        # Victory screen
        if levels[current_level].won:
            # Overwrite existing highscores if required
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
                f"Move Score: {move_scores[current_level]:.1f}",
                True, BLUE
            )
            best_time_score_text = font.render(
                f"Best Time Score: {highscores[current_level][0]:.1f}",
                True, BLUE
            )
            best_move_score_text = font.render(
                f"Best Move Score: {highscores[current_level][1]:.1f}",
                True, BLUE
            )
            best_total_time_score_text = font.render(
                f"Best Game Time Score: {sum(x[0] for x in highscores):.1f}",
                True, BLUE
            )
            best_total_move_score_text = font.render(
                f"Best Game Move Score: {sum(x[1] for x in highscores):.1f}",
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
        # Death screen
        elif levels[current_level].killed:
            screen.fill(RED)
            if cfg.monster_sound_on_kill and has_started_level[current_level]:
                monster_jumpscare_sound.play()
                has_started_level[current_level] = False
            if cfg.monster_display_on_kill:
                screen.blit(jumpscare_monster_texture, (
                    0, 50, cfg.viewport_width, cfg.viewport_height
                ))
        # Currently playing
        else:
            if has_started_level[current_level] and not is_reset_prompt_shown:
                # Progress time-based attributes and events
                time_scores[current_level] += frame_time
                monster_timeouts[current_level] += frame_time
                if (monster_spotted[current_level]
                        < cfg.monster_spot_timeout):
                    # Increment time since monster was last spotted
                    monster_spotted[current_level] += frame_time
                    if (monster_spotted[current_level]
                            > cfg.monster_spot_timeout):
                        monster_spotted[current_level] = (
                            cfg.monster_spot_timeout
                        )
                if (display_compass and not compass_burned_out[current_level]
                        and levels[current_level].monster_coords is not None):
                    # Decay remaining compass time
                    compass_charge_delays[current_level] = (
                        cfg.compass_charge_delay
                    )
                    compass_times[current_level] -= frame_time
                    if compass_times[current_level] <= 0.0:
                        compass_times[current_level] = 0.0
                        compass_burned_out[current_level] = True
                elif compass_times[current_level] < cfg.compass_time:
                    # Compass recharging
                    if (compass_charge_delays[current_level] == 0.0
                            or compass_burned_out[current_level]):
                        multiplier = 1 / (
                            cfg.compass_charge_burn_multiplier
                            if compass_burned_out[current_level] else
                            cfg.compass_charge_norm_multiplier
                        )
                        compass_times[current_level] += frame_time * multiplier
                        if compass_times[current_level] >= cfg.compass_time:
                            compass_times[current_level] = cfg.compass_time
                            compass_burned_out[current_level] = False
                    elif compass_charge_delays[current_level] > 0.0:
                        # Decrement delay before compass charging
                        compass_charge_delays[current_level] -= frame_time
                        if compass_charge_delays[current_level] < 0.0:
                            compass_charge_delays[current_level] = 0.0
                monster_wait = levels[current_level].monster_wait
                # Move monster if it is enabled and a sufficient amount of time
                # has passed since last move/level start
                if (cfg.monster_enabled and monster_wait is not None
                    and time_scores[current_level] > (
                            monster_wait
                            if cfg.monster_start_override is None else
                            cfg.monster_start_override
                        )
                        and monster_timeouts[current_level]
                        > cfg.monster_movement_wait):
                    levels[current_level].move_monster()
                    monster_timeouts[current_level] = 0
                    monster_coords = levels[current_level].monster_coords
                    if (monster_coords is not None
                            and cfg.monster_flicker_lights
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
            if not display_map or cfg.enable_cheat_map:
                # Draw solid sky
                pygame.draw.rect(
                    screen, BLUE,
                    (0, 50, filled_screen_width, cfg.viewport_height // 2)
                )
                monster_coords = levels[current_level].monster_coords
                # Draw solid floor
                pygame.draw.rect(
                    screen, LIGHT_GREY,
                    (
                        0, cfg.viewport_height // 2 + 50,
                        filled_screen_width, cfg.viewport_height // 2
                    )
                )

            if (cfg.sky_textures_enabled
                    and (not display_map or cfg.enable_cheat_map)):
                # Draw textured sky based on facing direction.
                # Player position does not affect sky, only direction.
                for index in range(cfg.display_columns):
                    camera_x = 2 * index / cfg.display_columns - 1
                    direction = facing_directions[current_level]
                    camera_plane = camera_planes[current_level]
                    cast_direction = (
                        direction[0] + camera_plane[0] * camera_x,
                        direction[1] + camera_plane[1] * camera_x,
                    )
                    angle = math.atan2(*cast_direction)
                    texture_x = math.floor(
                        angle / math.pi * cfg.texture_width
                    )
                    # Creates a "mirror" effect preventing a seam when the
                    # texture repeats
                    texture_x = (
                        texture_x % cfg.texture_width
                        if angle >= 0 else
                        cfg.texture_width - (texture_x % cfg.texture_width) - 1
                    )
                    # Get a single column of pixels
                    scaled_pixel_column = pygame.transform.scale(
                        sky_texture.subsurface(
                            texture_x, 0, 1, cfg.texture_height
                        ), (display_column_width, cfg.viewport_height // 2)
                    )
                    screen.blit(
                        scaled_pixel_column, (index * display_column_width, 50)
                    )

            if not display_map or cfg.enable_cheat_map:
                columns, sprites = raycasting.get_columns_sprites(
                    cfg.display_columns, levels[current_level],
                    cfg.draw_maze_edge_as_wall,
                    facing_directions[current_level],
                    camera_planes[current_level]
                )
            else:
                # Skip maze rendering if map is open as it will be obscuring
                # entire viewport anyway
                columns = []
                sprites = []
            type_column = 0
            type_sprite = 1
            # A generic combination of both wall columns and sprites
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
            # Used for displaying rays on cheat map, not used in rendering
            ray_end_coords: List[Tuple[float, float]] = []
            for index, object_type, _ in objects:
                if object_type == type_sprite:
                    # Sprites are just flat images scaled and blitted onto the
                    # 3D view.
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
                        (filled_screen_width / 2)
                        * (1 + transformation[0] / transformation[1])
                    )
                    if (screen_x_pos
                            > filled_screen_width + cfg.texture_width // 2
                            or screen_x_pos < -cfg.texture_width // 2):
                        # Sprite is fully off screen - don't render it and move
                        # onto the next render object
                        continue
                    sprite_size = (
                        abs(filled_screen_width // transformation[1]),
                        abs(cfg.viewport_height // transformation[1])
                    )
                    scaled_texture = pygame.transform.scale(
                        sprite_textures[sprite_type], sprite_size
                    )
                    screen.blit(
                        scaled_texture,
                        (
                            screen_x_pos - sprite_size[0] // 2,
                            cfg.viewport_height // 2 - sprite_size[1] // 2 + 50
                        )
                    )
                    if sprite_type == raycasting.MONSTER:
                        # If the monster has been rendered, play the jumpscare
                        # sound if enough time has passed since the last play.
                        # Also set the timer to 0 to reset it.
                        if (cfg.monster_sound_on_spot and
                                monster_spotted[current_level]
                                == cfg.monster_spot_timeout):
                            monster_spotted_sound.play()
                        monster_spotted[current_level] = 0.0
                elif object_type == type_column:
                    # A column is a portion of a wall that was hit by a ray.
                    coord, distance, _, side_was_ns = columns[index]
                    # Edge of maze when drawing maze edges as walls is disabled
                    # Entire ray will be skipped, revealing the horizon.
                    if distance == float('inf'):
                        continue
                    if display_rays:
                        # For cheat map only
                        ray_end_coords.append(coord)
                    # Prevent division by 0
                    distance = max(1e-5, distance)
                    # An illusion of distance is achieved by drawing lines at
                    # different heights depending on the distance a ray
                    # travelled.
                    column_height = round(cfg.viewport_height / distance)
                    # If a texture for the current level has been found or not
                    texture_draw_successful = False
                    if cfg.textures_enabled:
                        both_textures = None
                        for indices, images in wall_textures.items():
                            if current_level in indices:
                                both_textures = images
                                break
                        if both_textures is not None:
                            # Select either light or dark texture
                            # depending on side
                            texture = both_textures[int(side_was_ns)]
                            # Determines how far along the texture we need to
                            # go by keeping only the decimal part of the
                            # collision coordinate
                            position_along_wall = coord[
                                int(not side_was_ns)
                            ] % 1
                            texture_x = math.floor(
                                position_along_wall * cfg.texture_width
                            )
                            if (not side_was_ns and
                                    facing_directions[current_level][0] > 0):
                                texture_x = cfg.texture_width - texture_x - 1
                            elif (side_was_ns and
                                    facing_directions[current_level][1] < 0):
                                texture_x = cfg.texture_width - texture_x - 1
                            # The location on the screen to start drawing the
                            # column
                            draw_x = display_column_width * index
                            draw_y = max(
                                0,
                                -column_height // 2 + cfg.viewport_height // 2
                            ) + 50
                            # Get a single column of pixels
                            pixel_column = texture.subsurface(
                                texture_x, 0, 1, cfg.texture_height
                            )
                            if (column_height > cfg.viewport_height
                                    and column_height
                                    > cfg.texture_scale_limit):
                                # Crop the column so we are only scaling pixels
                                # that will be within the viewport. This will
                                # boost performance, at the cost of making
                                # textures uneven. This will only occur if the
                                # column is taller than the config value in
                                # texture_scale_limit
                                overlap = math.floor(
                                    (column_height - cfg.viewport_height)
                                    / (
                                        (column_height - cfg.texture_height)
                                        / cfg.texture_height
                                    )
                                )
                                pixel_column = pixel_column.subsurface(
                                    0, overlap // 2,
                                    1, cfg.texture_height - overlap
                                )
                            # Scale the pixel column to fill required height
                            pixel_column = pygame.transform.scale(
                                pixel_column,
                                (
                                    display_column_width,
                                    min(column_height, cfg.viewport_height)
                                    if column_height > cfg.texture_scale_limit
                                    else column_height
                                )
                            )
                            # Ensure capped height pixel columns still render
                            # in the correct Y position.
                            if (cfg.viewport_height < column_height
                                    <= cfg.texture_scale_limit):
                                overlap = (
                                    column_height - cfg.viewport_height
                                ) // 2
                                pixel_column = pixel_column.subsurface(
                                    0, overlap,
                                    display_column_width, cfg.viewport_height
                                )
                            screen.blit(pixel_column, (draw_x, draw_y))
                            texture_draw_successful = True
                    if not texture_draw_successful:
                        # Fallback to drawing solid textureless walls if a
                        # texture for the current level's walls was not found.
                        column_height = min(column_height, cfg.viewport_height)
                        colour = DARK_GREY if side_was_ns else BLACK
                        pygame.draw.rect(
                            screen, colour, (
                                display_column_width * index,
                                max(
                                    0,
                                    -column_height // 2
                                    + cfg.viewport_height // 2
                                ) + 50,
                                display_column_width, column_height
                            )
                        )
            if display_map:
                x_offset = cfg.viewport_width if cfg.enable_cheat_map else 0
                for y, row in enumerate(levels[current_level].wall_map):
                    for x, point in enumerate(row):
                        if floor_coordinates(
                                levels[current_level].player_coords) == (x, y):
                            colour = BLUE
                        elif (levels[current_level].monster_coords == (x, y)
                                and cfg.enable_cheat_map):
                            colour = DARK_RED
                        elif ((x, y) in levels[current_level].exit_keys
                                and cfg.enable_cheat_map):
                            colour = GOLD
                        elif (x, y) in levels[current_level].player_flags:
                            colour = LIGHT_BLUE
                        elif levels[current_level].start_point == (x, y):
                            colour = RED
                        elif (levels[current_level].end_point == (x, y)
                                and cfg.enable_cheat_map):
                            colour = GREEN
                        else:
                            colour = BLACK if point else WHITE
                        pygame.draw.rect(
                            screen, colour, (
                                tile_width * x + x_offset,
                                tile_height * y + 50, tile_width, tile_height
                            )
                        )
                # Raycast rays
                if display_rays and cfg.enable_cheat_map:
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
                    and (not display_map or cfg.enable_cheat_map)):
                # Darken viewport intermittently based on monster distance
                if cfg.monster_flicker_lights:
                    if flicker_time_remaining[current_level] > 0:
                        viewport_darkener = pygame.Surface(
                            (cfg.viewport_width, cfg.viewport_height)
                        )
                        viewport_darkener.fill(BLACK)
                        viewport_darkener.set_alpha(127)
                        screen.blit(viewport_darkener, (0, 50))
                        flicker_time_remaining[current_level] -= frame_time
                        if flicker_time_remaining[current_level] < 0:
                            flicker_time_remaining[current_level] = 0.0

            if display_compass:
                compass_outer_radius = cfg.viewport_width // 6
                compass_inner_radius = (
                    compass_outer_radius - cfg.viewport_width // 100
                )
                compass_centre = (
                    cfg.viewport_width - compass_outer_radius
                    - cfg.viewport_width // 50,
                    cfg.viewport_height + 50 - compass_outer_radius
                    - cfg.viewport_width // 50
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
                    # The distance between the player and the monster in each
                    # axis
                    relative_pos = (
                        levels[current_level].player_coords[0]
                        - monster_coords[0],
                        levels[current_level].player_coords[1]
                        - monster_coords[1]
                    )
                    # The angle to the monster relative to the facing direction
                    direction = (
                        math.atan2(*relative_pos)
                        - math.atan2(*facing_directions[current_level])
                    )
                    # Compass line gets shorter as it runs out of charge
                    line_length = compass_inner_radius * (
                        compass_times[current_level] / cfg.compass_time
                    )
                    line_end_coords = floor_coordinates((
                        line_length * math.sin(direction) + compass_centre[0],
                        line_length * math.cos(direction) + compass_centre[1]
                    ))
                    pygame.draw.line(
                        screen, RED, compass_centre, line_end_coords,
                        # Cannot be any thinner than 1px
                        max(1, cfg.viewport_width // 100)
                    )
                elif compass_burned_out[current_level]:
                    pygame.draw.circle(
                        screen, RED, compass_centre, compass_inner_radius
                        * (
                            (cfg.compass_time - compass_times[current_level])
                            / cfg.compass_time
                        )
                    )

            # HUD is drawn last to prevent it being obstructed
            pygame.draw.rect(screen, GREY, (0, 0, cfg.viewport_width, 50))
            time_score_text = font.render(
                f"Time: {time_scores[current_level]:.1f}"
                if has_started_level[current_level] else
                f"Time: {highscores[current_level][0]:.1f}",
                True,
                WHITE if levels[current_level].monster_coords is None else RED
            )
            move_score_text = font.render(
                f"Moves: {move_scores[current_level]:.1f}"
                if has_started_level[current_level] else
                f"Moves: {highscores[current_level][1]:.1f}",
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
            screen.blit(move_score_text, (170, 10))
            screen.blit(keys_text, (340, 10))

        if is_reset_prompt_shown:
            prompt_background = pygame.Surface(
                (cfg.viewport_width, cfg.viewport_height + 50)
            )
            prompt_background.fill(LIGHT_BLUE)
            prompt_background.set_alpha(195)
            screen.blit(prompt_background, (0, 0))
            confirm_text = font.render(
                "Press 'y' to reset or 'n' to cancel", True, DARK_GREY
            )
            screen.blit(
                confirm_text, (
                    cfg.viewport_width // 2
                    - confirm_text.get_width() // 2,
                    cfg.viewport_height // 2
                    - confirm_text.get_height() // 2 + 50,
                )
            )

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
