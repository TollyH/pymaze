# PyGame Maze

A simple, grid-based maze game written in Python with PyGame. For the "3D" version, see the ["raycasting" branch](https://github.com/TollyH/pygame_maze/tree/raycasting).

## Installation

1. Download the files by pressing the green "Code" button above, followed by "Download ZIP" - extracting all of the files once the download is complete.
   - Alternatively, if you have git installed, run `git clone https://github.com/TollyH/pygame_maze.git` in a terminal to download the repository.
2. Install PyGame with the command `pip3 install pygame` on Linux or `pip install pygame` on Windows.
3. Run `__main__.py` to start the game.

## Controls

- `Arrow keys` or `WASD` - Move around
- `[` and `]` - Previous/Next Level Respectively
- `R` - Reset level

## Cheat Controls

- `Click` - Teleport
- `Space` - Reveal all paths and shortest path to exit/keys
- `CTRL` + `Space` - Auto complete level
- `Mouse Wheel` - Increase/Decrease auto completion delay

## Instructions

- White tiles can be moved on, black tiles cannot.
- You (the blue tile) need to collect all of the keys (the gold tiles)
before reaching the exit (the green tile).
- When showing the solution, all possible paths are highlighted in lilac, with
the shortest one being highlighted in purple.
