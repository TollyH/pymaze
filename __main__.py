"""
PyGame Maze - Tolly Hill 2022

The main script for the game. Creates and draws to the game window, as well as
receiving and interpreting player input and recording time and movement scores.
"""
import math
import os
import pickle
import sys
from typing import List, Tuple

import pygame

import raycasting
from level import floor_coordinates
from maze_levels import levels

WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)
BLUE = (0x00, 0x30, 0xFF)
GOLD = (0xE1, 0xBB, 0x12)
DARK_GOLD = (0x70, 0x5E, 0x09)
GREEN = (0x00, 0xFF, 0x10)
DARK_GREEN = (0x00, 0x80, 0x00)
GREY = (0xAA, 0xAA, 0xAA)
DARK_GREY = (0x10, 0x10, 0x10)

VIEWPORT_WIDTH = 500
VIEWPORT_HEIGHT = 500

DISPLAY_COLUMNS = VIEWPORT_WIDTH
DISPLAY_FOV = 75

DRAW_MAZE_EDGE_AS_WALL = True

TURN_SPEED = 2.5
MOVE_SPEED = 4.0


def main():
    pygame.init()

    # Minimum window resolution is 400x400
    screen = pygame.display.set_mode(
        (max(VIEWPORT_WIDTH, 400), max(VIEWPORT_HEIGHT + 50, 400))
    )
    pygame.display.set_caption("Maze - Level 1")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Tahoma', 24, True)

    facing_directions = [(0.0, 1.0)] * len(levels)
    # Camera planes are always perpendicular to facing directions
    camera_planes = [(-DISPLAY_FOV / 100, 0.0)] * len(levels)
    frame_scores = [0] * len(levels)
    move_scores = [0] * len(levels)
    has_started_level = [False] * len(levels)
    if os.path.isfile("highscores.pickle"):
        with open("highscores.pickle", 'rb') as file:
            highscores: List[Tuple[int, int]] = pickle.load(file)
            if len(highscores) < len(levels):
                highscores += [(0, 0)] * (len(levels) - len(highscores))
    else:
        highscores: List[Tuple[int, int]] = [(0, 0)] * len(levels)

    current_level = 0

    # Game loop
    while True:
        # Limit to 50 FPS
        frame_time = clock.tick(50) / 1000
        display_column_width = VIEWPORT_WIDTH // DISPLAY_COLUMNS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Standard "press-once" keys
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFTBRACKET,
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
                elif event.key == pygame.K_r:
                    levels[current_level].reset()
                    facing_directions[current_level] = (0.0, 1.0)
                    camera_planes[current_level] = (-DISPLAY_FOV / 100, 0.0)
                    frame_scores[current_level] = 0
                    move_scores[current_level] = 0
                    has_started_level[current_level] = False

        old_grid_position = floor_coordinates(
            levels[current_level].player_coords
        )
        # Ensure framerate does not affect speed values
        turn_speed_mod = frame_time * TURN_SPEED
        move_speed_mod = frame_time * MOVE_SPEED
        # Held down keys
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_w] or pressed_keys[pygame.K_UP]:
            if not levels[current_level].won:
                levels[current_level].move_player((
                    facing_directions[current_level][0] * move_speed_mod,
                    facing_directions[current_level][1] * move_speed_mod
                ))
                has_started_level[current_level] = True
        if pressed_keys[pygame.K_s] or pressed_keys[pygame.K_DOWN]:
            if not levels[current_level].won:
                levels[current_level].move_player((
                    -facing_directions[current_level][0] * move_speed_mod,
                    -facing_directions[current_level][1] * move_speed_mod
                ))
                has_started_level[current_level] = True
        if pressed_keys[pygame.K_a]:
            if not levels[current_level].won:
                levels[current_level].move_player((
                    facing_directions[current_level][1] * move_speed_mod,
                    -facing_directions[current_level][0] * move_speed_mod
                ))
                has_started_level[current_level] = True
        if pressed_keys[pygame.K_d]:
            if not levels[current_level].won:
                levels[current_level].move_player((
                    -facing_directions[current_level][1] * move_speed_mod,
                    facing_directions[current_level][0] * move_speed_mod
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
            # Ceiling
            pygame.draw.rect(
                screen, BLUE,
                (0, 50, VIEWPORT_WIDTH, VIEWPORT_HEIGHT // 2)
            )
            # Floor
            pygame.draw.rect(
                screen, WHITE,
                (
                    0, VIEWPORT_HEIGHT // 2 + 50,
                    VIEWPORT_WIDTH, VIEWPORT_HEIGHT // 2
                )
            )

            for index, (column_distance, side_was_ns, hit_type) in enumerate(
                    raycasting.get_column_distances(
                        DISPLAY_COLUMNS, levels[current_level],
                        DRAW_MAZE_EDGE_AS_WALL,
                        facing_directions[current_level],
                        camera_planes[current_level])):
                # Edge of maze when drawing maze edges as walls is disabled
                if column_distance == float('inf'):
                    continue
                # Prevent division by 0
                column_distance = max(1e-30, column_distance)
                column_height = round(VIEWPORT_HEIGHT / column_distance)
                column_height = min(column_height, VIEWPORT_HEIGHT)
                if hit_type == raycasting.WALL:
                    colour = DARK_GREY if side_was_ns else BLACK
                elif hit_type == raycasting.END_POINT:
                    colour = GREEN if side_was_ns else DARK_GREEN
                elif hit_type == raycasting.KEY:
                    colour = GOLD if side_was_ns else DARK_GOLD
                else:
                    continue
                pygame.draw.rect(
                    screen, colour, (
                        display_column_width * index,
                        max(
                            0, -column_height // 2 + VIEWPORT_HEIGHT // 2
                        ) + 50,
                        display_column_width, column_height
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
        pygame.display.flip()


if __name__ == "__main__":
    main()
