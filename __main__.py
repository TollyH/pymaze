"""
PyGame Maze - Copyright © 2022  Ptolemy Hill and Finlay Griffiths

The main script for the game. Creates and draws to the game window, as well as
receiving and interpreting player input and recording time and movement scores.
Also handles time-based events such as monster movement and spawning.
"""
import os
import pickle
import sys
from typing import List, Set, Tuple

import pygame

from maze_levels import levels

# ADVANCED OPTIONS ============================================================

# The dimensions used for the maze view (not including the HUD).
VIEWPORT_WIDTH = 500
VIEWPORT_HEIGHT = 500

# Whether the monster should be spawned at all.
MONSTER_ENABLED = True
# If this is not None, it will be used as the time taken in seconds to spawn
# the monster, overriding the times specific to each level.
MONSTER_START_OVERRIDE = None
# How many seconds the monster will wait between each movement.
MONSTER_MOVEMENT_WAIT = 0.5
# Whether the scream sound should be played when the player is killed
MONSTER_SOUND_ON_KILL = True
# Whether the monster should be displayed fullscreen when the player is killed
MONSTER_DISPLAY_ON_KILL = True

# The maximum frames per second that the game will render at. Low values may
# cause the game window to become unresponsive.
FRAME_RATE_LIMIT = 75

# =============================================================================

UP = (0, -1)
RIGHT = (1, 0)
DOWN = (0, 1)
LEFT = (-1, 0)

WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)
BLUE = (0x00, 0x30, 0xFF)
GOLD = (0xE1, 0xBB, 0x12)
GREEN = (0x00, 0xFF, 0x10)
RED = (0xFF, 0x00, 0x00)
DARK_RED = (0x80, 0x00, 0x00)
PURPLE = (0x87, 0x23, 0xD9)
LILAC = (0xD7, 0xA6, 0xFF)
GREY = (0xAA, 0xAA, 0xAA)


def main():
    pygame.init()

    # Minimum window resolution is 400x400
    screen = pygame.display.set_mode(
        (max(VIEWPORT_WIDTH, 400), max(VIEWPORT_HEIGHT + 50, 400))
    )
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    time_scores = [0.0] * len(levels)
    move_scores = [0] * len(levels)
    has_started_level = [False] * len(levels)
    if os.path.isfile("highscores.pickle"):
        with open("highscores.pickle", 'rb') as file:
            highscores: List[Tuple[float, int]] = pickle.load(file)
            if len(highscores) < len(levels):
                highscores += [(0, 0)] * (len(levels) - len(highscores))
    else:
        highscores: List[Tuple[float, int]] = [(0, 0)] * len(levels)

    current_level = 0
    show_solution = False
    is_autosolving = False
    automove_delay = 1

    frame_counters = [0] * len(levels)
    monster_timeouts = [0.0] * len(levels)

    monster_texture = pygame.transform.scale(pygame.image.load(
        os.path.join("textures", "sprite", "monster.png")
    ).convert_alpha(), (VIEWPORT_WIDTH, VIEWPORT_HEIGHT))
    monster_jumpscare_sound = pygame.mixer.Sound(
        os.path.join("sounds", "monster_jumpscare.wav")
    )

    # Game loop
    while True:
        # Limit FPS and record time last frame took to render
        frame_time = clock.tick(FRAME_RATE_LIMIT) / 1000
        tile_width = VIEWPORT_WIDTH // levels[current_level].dimensions[0]
        tile_height = VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
        solutions = []
        solution_coords: Set[Tuple[int, int]] = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and not is_autosolving:
                if event.key in (pygame.K_w, pygame.K_UP):
                    levels[current_level].move_player(UP)
                    if (not levels[current_level].won
                            and not levels[current_level].killed):
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    levels[current_level].move_player(RIGHT)
                    if (not levels[current_level].won
                            and not levels[current_level].killed):
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    levels[current_level].move_player(DOWN)
                    if (not levels[current_level].won
                            and not levels[current_level].killed):
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    levels[current_level].move_player(LEFT)
                    if (not levels[current_level].won
                            and not levels[current_level].killed):
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key in (pygame.K_LEFTBRACKET,
                                   pygame.K_RIGHTBRACKET):
                    if event.key == pygame.K_LEFTBRACKET and current_level > 0:
                        current_level -= 1
                    elif (event.key == pygame.K_RIGHTBRACKET
                            and current_level < len(levels) - 1):
                        current_level += 1
                    else:
                        continue
                    pygame.display.set_caption(
                        f"Maze - Level {current_level + 1}"
                    )
                    # Update tile dimensions to fit new level
                    tile_width = (
                        VIEWPORT_WIDTH // levels[current_level].dimensions[0]
                    )
                    tile_height = (
                        VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
                    )
                elif event.key == pygame.K_r:
                    levels[current_level].reset()
                    time_scores[current_level] = 0
                    move_scores[current_level] = 0
                    has_started_level[current_level] = False
                elif event.key == pygame.K_SPACE:
                    key_states = pygame.key.get_pressed()
                    if (key_states[pygame.K_LCTRL]
                            or key_states[pygame.K_RCTRL]):
                        is_autosolving = True
                        has_started_level[current_level] = True
                    else:
                        show_solution = not show_solution
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT and not is_autosolving:
                    mouse_position = pygame.mouse.get_pos()
                    levels[current_level].move_player(
                        (
                            mouse_position[0] // tile_width,
                            (mouse_position[1] - 50) // tile_height
                        ), False
                    )
                    if not levels[current_level].won:
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.button == pygame.BUTTON_WHEELUP:
                    automove_delay += 1
                elif (event.button == pygame.BUTTON_WHEELDOWN
                        and automove_delay > 1):
                    automove_delay -= 1

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
                screen.blit(monster_texture, (
                    0, 50, VIEWPORT_WIDTH, VIEWPORT_HEIGHT
                ))
        else:
            if has_started_level[current_level]:
                time_scores[current_level] += frame_time
                monster_timeouts[current_level] += frame_time
                frame_counters[current_level] += 1
                if (MONSTER_ENABLED and levels[current_level].monster_wait
                        is not None and time_scores[current_level]
                        > (
                            levels[current_level].monster_wait  # type: ignore
                            if MONSTER_START_OVERRIDE is None else
                            MONSTER_START_OVERRIDE
                        )
                        and monster_timeouts[current_level]
                        > MONSTER_MOVEMENT_WAIT):
                    levels[current_level].move_monster()
                    monster_timeouts[current_level] = 0
            screen.fill(GREY)
            time_score_text = font.render(
                f"Time: {time_scores[current_level]:.1f}"
                if has_started_level[current_level] else
                f"Time: {highscores[current_level][0]:.1f}",
                True, WHITE
            )
            move_score_text = font.render(
                f"Moves: {move_scores[current_level]}"
                if has_started_level[current_level] else
                f"Moves: {highscores[current_level][1]}",
                True, WHITE
            )
            screen.blit(time_score_text, (10, 10))
            screen.blit(move_score_text, (200, 10))
            if show_solution or is_autosolving:
                solutions = levels[current_level].find_possible_paths()
                # A set of all coordinates appearing in any solution
                solution_coords = {x for y in solutions[1:] for x in y}
                if (is_autosolving and
                        frame_counters[current_level] % automove_delay == 0):
                    if len(solutions) < 1:
                        is_autosolving = False
                    else:
                        move_scores[current_level] += 1
                        levels[current_level].move_player(
                            solutions[0][1], False
                        )
                        # Find new solutions after move to display to player
                        solutions = levels[current_level].find_possible_paths()
                        if levels[current_level].won:
                            is_autosolving = False
            for y, row in enumerate(levels[current_level].wall_map):
                for x, point in enumerate(row):
                    if levels[current_level].player_coords == (x, y):
                        color = BLUE
                    elif levels[current_level].monster_coords == (x, y):
                        color = DARK_RED
                    elif (x, y) in levels[current_level].exit_keys:
                        color = GOLD
                    elif levels[current_level].start_point == (x, y):
                        color = RED
                    elif levels[current_level].end_point == (x, y):
                        color = GREEN
                    elif len(solutions) >= 1 and (x, y) in solutions[0]:
                        color = PURPLE
                    elif len(solutions) >= 1 and (x, y) in solution_coords:
                        color = LILAC
                    else:
                        color = BLACK if point else WHITE
                    pygame.draw.rect(
                        screen, color, (
                            tile_width * x, tile_height * y + 50,
                            tile_width, tile_height
                        )
                    )
        print(
            f"\r{clock.get_fps():5.2f} FPS - "
            + f"({levels[current_level].player_coords[0]:3d},"
            + f"{levels[current_level].player_coords[1]:3d}) - "
            + f"Displaying {len(solutions):4d} solutions",
            end="", flush=True
        )
        pygame.display.flip()


if __name__ == "__main__":
    main()
