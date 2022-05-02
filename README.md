# PyGame Maze

A simple, grid-based maze game written in Python with PyGame. **Note: This 2D version will not be receiving any new features. See the ["3D" version](https://github.com/TollyH/pymaze/tree/raycasting) for the more up-to-date experience.**

## Installation

1. Download the files by pressing the green "Code" button above, followed by "Download ZIP" - extracting all of the files once the download is complete.
   - Alternatively, if you have git installed, run `git clone https://github.com/TollyH/pymaze.git` in a terminal to download the repository, then `git checkout flat` from the repository folder to switch to the flat branch.
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
- You (the blue tile) need to collect all of the keys (the gold tiles) before reaching the exit (the green tile).
- In many levels, after a specific amount of time has passed, a monster may spawn (a dark red tile). Getting hit by the monster will result in you losing the level immediately.
- When showing the solution, all possible paths are highlighted in lilac, with the shortest one being highlighted in purple.
