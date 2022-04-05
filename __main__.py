"""
PyGame Maze - Copyright © 2022  Ptolemy Hill and Finlay Griffiths

The main script for the game. Creates the game window, receives and interprets
player input, and records time and movement scores. Also handles time-based
events such as monster movement and spawning.
"""
import math
import os
import pickle
import random
import sys
import threading
from glob import glob
from typing import Dict, List, Optional, Set, Tuple

import pygame

import config_editor
import config_loader
import level
import raycasting
import screen_drawing
from maze_levels import levels


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
        max(cfg.viewport_width, 500), max(cfg.viewport_height, 500)
    ))
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    # X+Y facing directions, times, moves, etc. are specific to each level,
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
    darkener.fill(screen_drawing.BLACK)
    darkener.set_alpha(127)
    # {(level_indices, ...): (light_texture, dark_texture)}
    wall_textures: Dict[Tuple[int], Tuple[pygame.Surface, pygame.Surface]] = {
        # Parse wall texture surfaces to tuples of integers
        tuple(int(y) for y in os.path.split(x)[-1].split(".")[0].split("-")):
        (pygame.image.load(x).convert(), pygame.image.load(x).convert())
        for x in glob(os.path.join("textures", "wall", "*.png"))
    }
    for _, (_, surface_to_dark) in wall_textures.items():
        surface_to_dark.blit(darkener, (0, 0))
    # {degradation_stage: (light_texture, dark_texture)}
    player_wall_textures: Dict[int, Tuple[pygame.Surface, pygame.Surface]] = {
        # Parse player wall texture surfaces to integer
        int(os.path.split(x)[-1].split(".")[0]):
            (pygame.image.load(x).convert(), pygame.image.load(x).convert())
        for x in glob(os.path.join("textures", "player_wall", "*.png"))
    }
    for _, (_, surface_to_dark) in player_wall_textures.items():
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
    # Used to calculate how far mouse has travelled for mouse control
    old_mouse_pos = (cfg.viewport_width // 2, cfg.viewport_height // 2)

    display_map = False
    display_compass = False
    display_stats = False
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
    wall_place_cooldown = [0.0] * len(levels)
    flicker_time_remaining = [0.0] * len(levels)
    pickup_flash_time_remaining = 0.0

    # [None | (grid_x, grid_y, time_of_placement)]
    player_walls: List[Optional[Tuple[int, int, float]]] = [None] * len(levels)

    # Used to draw level behind victory/reset screens without having to raycast
    # during every new frame.
    last_level_frame = [
        pygame.Surface((cfg.viewport_width, cfg.viewport_height))
        for _ in range(len(levels))
    ]

    # Game loop
    while True:
        screen.fill(screen_drawing.BLACK)
        if os.path.getmtime('config.ini') > last_config_edit:
            # Config has been edited so it should be reloaded.
            last_config_edit = os.path.getmtime('config.ini')
            cfg = config_loader.Config()
        # Limit FPS and record time last frame took to render
        frame_time = clock.tick(cfg.frame_rate_limit) / 1000
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
                        grid_coords = level.floor_coordinates(
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
                    elif event.key == pygame.K_e:
                        # Stats and map cannot be displayed together
                        if not display_map or cfg.enable_cheat_map:
                            display_stats = not display_stats
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
                    elif (event.key == pygame.K_q
                            and player_walls[current_level] is None
                            and wall_place_cooldown[current_level] == 0
                            and has_started_level[current_level]):
                        cardinal_facing = (
                            round(facing_directions[current_level][0]),
                            round(facing_directions[current_level][1])
                        )
                        grid_coords = level.floor_coordinates(
                            levels[current_level].player_coords
                        )
                        target = (
                            grid_coords[0] + cardinal_facing[0],
                            grid_coords[1] + cardinal_facing[1]
                        )
                        if (levels[current_level].is_coord_in_bounds(target)
                                and not levels[current_level][target]):
                            player_walls[current_level] = (
                                target[0], target[1],
                                time_scores[current_level]
                            )
                            levels[current_level][target] = True
                    elif event.key == pygame.K_r:
                        is_reset_prompt_shown = True
                    elif event.key == pygame.K_SPACE:
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_RCTRL] or pressed[pygame.K_LCTRL]:
                            display_rays = not display_rays
                        else:
                            display_map = not display_map
                    elif event.key == pygame.K_ESCAPE:
                        enable_mouse_control = False
                        # Return the mouse to normal
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    elif event.key == pygame.K_SLASH:
                        pressed = pygame.key.get_pressed()
                        if pressed[pygame.K_RCTRL] or pressed[pygame.K_LCTRL]:
                            # Launch config editor in separate thread to
                            # prevent blocking the main game.
                            threading.Thread(
                                target=config_editor.ConfigEditorApp
                            ).start()
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
                        screen_drawing.total_time_on_screen[current_level] = 0
                        display_compass = False
                        if not cfg.enable_cheat_map:
                            display_map = False
                        if player_walls[current_level] is not None:
                            levels[current_level][
                                player_walls[current_level][:2]
                            ] = False
                            player_walls[current_level] = None
                        wall_place_cooldown[current_level] = 0.0
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
                        and mouse_coords[0] > cfg.viewport_width):
                    clicked_tile = (
                        (mouse_coords[0] - cfg.viewport_width) // tile_width,
                        mouse_coords[1] // tile_height
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
            max(cfg.viewport_height, 500)
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
            # A set of events that occurred due to player movement
            events: Set[int] = set()
            if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    events.update(levels[current_level].move_player((
                        facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier,
                        facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier
                    )))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    events.update(levels[current_level].move_player((
                        -facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier,
                        -facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier
                    )))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_a]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    events.update(levels[current_level].move_player((
                        facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier,
                        -facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier
                    )))
                    has_started_level[current_level] = True
            if pressed_keys[pygame.K_d]:
                if (not levels[current_level].won
                        and not levels[current_level].killed):
                    events.update(levels[current_level].move_player((
                        -facing_directions[current_level][1] * move_speed_mod
                        * move_multiplier,
                        facing_directions[current_level][0] * move_speed_mod
                        * move_multiplier
                    )))
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
            if level.PICKED_UP_KEY in events:
                pickup_flash_time_remaining = 0.4
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
            screen_drawing.draw_victory_screen(
                screen, cfg, last_level_frame[current_level],
                highscores, current_level, time_scores[current_level],
                move_scores[current_level], frame_time
            )
        # Death screen
        elif levels[current_level].killed:
            if cfg.monster_sound_on_kill and has_started_level[current_level]:
                monster_jumpscare_sound.play()
                has_started_level[current_level] = False
            screen_drawing.draw_kill_screen(
                screen, cfg, jumpscare_monster_texture
            )
        # Currently playing
        elif not is_reset_prompt_shown:
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
                if wall_place_cooldown[current_level] > 0:
                    wall_place_cooldown[current_level] -= frame_time
                    wall_place_cooldown[current_level] = max(
                        0.0, wall_place_cooldown[current_level]
                    )
                if (player_walls[current_level] is not None
                        and time_scores[current_level]
                        >= player_walls[current_level][2]
                        + cfg.player_wall_time):
                    # Remove player placed wall if enough time has passed
                    levels[current_level][
                        player_walls[current_level][:2]
                    ] = False
                    player_walls[current_level] = None
                    wall_place_cooldown[current_level] = (
                        cfg.player_wall_cooldown
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
                        compass_charge_delays[current_level] = max(
                            0.0, compass_charge_delays[current_level]
                        )
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
            if not display_map or cfg.enable_cheat_map:
                screen_drawing.draw_solid_background(screen, cfg)

            if (cfg.sky_textures_enabled
                    and (not display_map or cfg.enable_cheat_map)):
                screen_drawing.draw_sky_texture(
                    screen, cfg, facing_directions[current_level],
                    camera_planes[current_level], sky_texture
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
            objects: List[Tuple[int, int, float]] = [
                (i, type_column, x[3]) for i, x in enumerate(columns)
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
                    screen_drawing.draw_sprite(
                        screen, cfg, coord,
                        levels[current_level].player_coords,
                        camera_planes[current_level],
                        facing_directions[current_level],
                        sprite_textures[sprite_type]
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
                    coord, tile, distance, _, side_was_ns = columns[index]
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
                        if (player_walls[current_level] is not None
                                and tile == player_walls[current_level][:2]):
                            # Select appropriate player wall texture depending
                            # on how long the wall has left until breaking.
                            both_textures = player_wall_textures[
                                math.floor(
                                    (
                                        time_scores[current_level]
                                        - player_walls[current_level][2]
                                    ) / cfg.player_wall_time * len(
                                        player_wall_textures
                                    )
                                )
                            ]
                        else:
                            for indices, images in wall_textures.items():
                                if current_level in indices:
                                    both_textures = images
                                    break
                        if both_textures is not None:
                            # Select either light or dark texture
                            # depending on side
                            texture = both_textures[int(side_was_ns)]
                            screen_drawing.draw_textured_column(
                                screen, cfg, coord, side_was_ns, column_height,
                                index, facing_directions[current_level],
                                texture
                            )
                            texture_draw_successful = True
                    if not texture_draw_successful:
                        # Fallback to drawing solid textureless walls if a
                        # texture for the current level's walls was not found.
                        screen_drawing.draw_untextured_column(
                            screen, cfg, index, side_was_ns, column_height
                        )
            if display_map:
                screen_drawing.draw_map(
                    screen, cfg, levels[current_level], display_rays,
                    ray_end_coords, facing_directions[current_level],
                    None if player_walls[current_level] is None else
                    player_walls[current_level][:2]
                )

            if pickup_flash_time_remaining > 0:
                screen_drawing.flash_viewport(
                    screen, cfg, False, pickup_flash_time_remaining
                )
                pickup_flash_time_remaining -= frame_time
                pickup_flash_time_remaining = max(
                    0.0, pickup_flash_time_remaining
                )

            monster_coords = levels[current_level].monster_coords
            if (monster_coords is not None
                    and (not display_map or cfg.enable_cheat_map)):
                # Darken viewport intermittently based on monster distance
                if cfg.monster_flicker_lights:
                    if flicker_time_remaining[current_level] > 0:
                        screen_drawing.flash_viewport(screen, cfg, True, 0.5)
                        flicker_time_remaining[current_level] -= frame_time
                        flicker_time_remaining[current_level] = max(
                            0.0, flicker_time_remaining[current_level]
                        )

            if display_compass and (not display_map or cfg.enable_cheat_map):
                monster_coords = levels[current_level].monster_coords
                if monster_coords is not None:
                    monster_coords = (
                        monster_coords[0] + 0.5, monster_coords[1] + 0.5
                    )
                screen_drawing.draw_compass(
                    screen, cfg, monster_coords,
                    levels[current_level].player_coords,
                    facing_directions[current_level],
                    compass_burned_out[current_level],
                    compass_times[current_level]
                )

            # Stats are always shown before the player begins a level to
            # display highscores and the key count.
            if ((display_stats or not has_started_level[current_level])
                    and (not display_map or cfg.enable_cheat_map)):
                time_score = (
                    time_scores[current_level]
                    if has_started_level[current_level] else
                    highscores[current_level][0]
                )
                move_score = (
                    move_scores[current_level]
                    if has_started_level[current_level] else
                    highscores[current_level][1]
                )
                screen_drawing.draw_stats(
                    screen, cfg,
                    levels[current_level].monster_coords is not None,
                    time_score, move_score,
                    len(levels[current_level].original_exit_keys)
                    - len(levels[current_level].exit_keys),
                    len(levels[current_level].original_exit_keys)
                )

            last_level_frame[current_level] = screen.copy()

        if is_reset_prompt_shown:
            screen_drawing.draw_reset_prompt(
                screen, cfg, last_level_frame[current_level]
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
