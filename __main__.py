"""
PyGame Maze - Copyright © 2022  Ptolemy Hill and Finlay Griffiths

The script that launches the game, config editor, and level designer.
"""
import os
import sys

import pygame

from config_editor import ConfigEditorApp
from level_designer import LevelDesignerApp
from maze_game import maze_game
from screen_drawing import BLUE, GREEN, WHITE


def main() -> None:
    """
    Gives the user the option to launch either the game, config editor, or
    level designer.
    """
    # Change working directory to the directory where the script is located.
    # This prevents issues with required files not being found.
    os.chdir(os.path.dirname(__file__))
    pygame.init()

    # Minimum window resolution is 500×500
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("PyGame Maze")
    pygame.display.set_icon(
        pygame.image.load(os.path.join("window_icons", "main.png")).convert()
    )

    normal_font = pygame.font.SysFont('Tahoma', 18, True)
    button_font = pygame.font.SysFont('Tahoma', 28, True)
    title_font = pygame.font.SysFont('Tahoma', 36, True)

    title_text = title_font.render("PyGame Maze", True, BLUE)
    copyright_text = normal_font.render(
        "Copyright © 2022  Ptolemy Hill and Finlay Griffiths", True, BLUE
    )
    play_text = button_font.render("Play", True, WHITE)
    config_text = button_font.render("Settings", True, WHITE)
    design_text = button_font.render("Designer", True, WHITE)
    button_width = max(
        x.get_width() for x in (play_text, config_text, design_text)
    ) + 10

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    clicked_pos = pygame.mouse.get_pos()
                    if (250 - button_width // 2 <= clicked_pos[0]
                            <= 250 + button_width // 2):
                        if 108 <= clicked_pos[1] <= 158:
                            maze_game()
                        elif 224 <= clicked_pos[1] <= 274:
                            screen.fill(BLUE)
                            pygame.display.update()
                            ConfigEditorApp()
                        elif 340 <= clicked_pos[1] <= 390:
                            screen.fill(BLUE)
                            pygame.display.update()
                            LevelDesignerApp()
        screen.fill(GREEN)
        screen.blit(title_text, (250 - title_text.get_width() // 2, 5))
        screen.blit(copyright_text,
                    (250 - copyright_text.get_width() // 2, 450))
        pygame.draw.rect(
            screen, BLUE, (250 - button_width // 2, 108, button_width, 50)
        )
        pygame.draw.rect(
            screen, BLUE, (250 - button_width // 2, 224, button_width, 50)
        )
        pygame.draw.rect(
            screen, BLUE, (250 - button_width // 2, 340, button_width, 50)
        )
        screen.blit(play_text, (250 - play_text.get_width() // 2, 113))
        screen.blit(config_text, (250 - config_text.get_width() // 2, 229))
        screen.blit(design_text, (250 - design_text.get_width() // 2, 345))
        pygame.display.update()


if __name__ == "__main__":
    main()
