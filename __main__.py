"""
PyGame Maze - Tolly Hill 2022

The main script for the game. Creates and draws to the game window, as well as
receiving and interpreting player input and recording time and movement scores.
"""
import os
import pickle
import sys
from typing import List, Set, Tuple

import pygame

from maze_levels import levels

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
PURPLE = (0x87, 0x23, 0xD9)
LILAC = (0xD7, 0xA6, 0xFF)
GREY = (0xAA, 0xAA, 0xAA)

VIEWPORT_WIDTH = 500
VIEWPORT_HEIGHT = 500


def main():
    pygame.init()

    # Minimum window resolution is 350x350
    screen = pygame.display.set_mode(
        (max(VIEWPORT_WIDTH, 350), max(VIEWPORT_HEIGHT + 50, 350))
    )
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    frame_scores = [0] * len(levels)
    move_scores = [0] * len(levels)
    has_started_level = [False] * len(levels)
    if os.path.isfile("highscores.pickle"):
        with open("highscores.pickle", 'rb') as file:
            highscores: List[Tuple[int, int]] = pickle.load(file)
    else:
        highscores: List[Tuple[int, int]] = [(0, 0)] * len(levels)

    current_level = 0
    show_solution = False
    is_autosolving = False
    automove_delay = 1

    # Game loop
    while True:
        # Limit to 50 FPS
        clock.tick(50)
        tile_width = VIEWPORT_WIDTH // levels[current_level].dimensions[0]
        tile_height = VIEWPORT_HEIGHT // levels[current_level].dimensions[1]
        solutions = []
        solution_coords: Set[Tuple[int, int]] = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and not is_autosolving:
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    levels[current_level].move_player(UP)
                    if not levels[current_level].won:
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    levels[current_level].move_player(RIGHT)
                    if not levels[current_level].won:
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    levels[current_level].move_player(DOWN)
                    if not levels[current_level].won:
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    levels[current_level].move_player(LEFT)
                    if not levels[current_level].won:
                        move_scores[current_level] += 1
                        has_started_level[current_level] = True
                elif (event.key == pygame.K_LEFTBRACKET
                        or event.key == pygame.K_RIGHTBRACKET):
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
                    frame_scores[current_level] = 0
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
            if (frame_scores[current_level] < highscores[current_level][0]
                    or highscores[current_level][0] == 0):
                highscores[current_level] = (
                    frame_scores[current_level], highscores[current_level][1]
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
                f"Time Score: {frame_scores[current_level]}",
                True, BLUE
            )
            move_score_text = font.render(
                f"Move Score: {move_scores[current_level]}",
                True, BLUE
            )
            best_time_score_text = font.render(
                f"Best Time Score: {highscores[current_level][0]}",
                True, BLUE
            )
            best_move_score_text = font.render(
                f"Best Move Score: {highscores[current_level][1]}",
                True, BLUE
            )
            best_total_time_score_text = font.render(
                f"Best Game Time Score: {sum(x[0] for x in highscores)}",
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
        else:
            if has_started_level[current_level]:
                frame_scores[current_level] += 1
            screen.fill(GREY)
            time_score_text = font.render(
                f"Time: {frame_scores[current_level]}"
                if has_started_level[current_level] else
                f"Time: {highscores[current_level][0]}",
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
                if (is_autosolving
                        and frame_scores[current_level] % automove_delay == 0):
                    move_scores[current_level] += 1
                    levels[current_level].move_player(solutions[0][1], False)
                    # Find new solutions after move to display to player
                    solutions = levels[current_level].find_possible_paths()
                    if levels[current_level].won:
                        is_autosolving = False
            for y, row in enumerate(levels[current_level].wall_map):
                for x, point in enumerate(row):
                    if levels[current_level].player_coords == (x, y):
                        color = BLUE
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
            + f"Displaying {len(solutions):4d} solutions", end="", flush=True
        )
        pygame.display.flip()


if __name__ == "__main__":
    main()
