# PyGame Maze

A pseudo-3D, grid-based maze game written in Python with PyGame using a DDA
algorithm for raycasting. For the fully 2D version without raycasting, see the ["flat" branch](https://github.com/TollyH/pygame_maze/tree/flat).

## Installation

1. Download the files by pressing the green "Code" button above, followed by "Download ZIP" - extracting all of the files once the download is complete.
   - Alternatively, if you have git installed, run `git clone https://github.com/TollyH/pygame_maze.git` in a terminal to download the repository.
2. Install PyGame with the command `pip3 install pygame` on Linux or `pip install pygame` on Windows.
3. Run `__main__.py` to start the game.

## Controls

- `WASD` or `Up` and `Down` - Move around
- `Left` and `Right` - Turn camera
- `[` and `]` - Previous/Next Level Respectively
- `F` - Place/pick up flag
- `R` - Reset level
- `Shift` - Run while held
- `CTRL` - Crawl while held

## Cheat Controls

- `Space` - Toggle map display
- `CTRL` + `Space` - Toggle displaying of field of view on map
- `Alt` + `Space` - Toggle displaying of shortest path to exit/keys on map

## Instructions

- Simply collect all of the golden keys before reaching the exit.
- In many levels, after a specific amount of time has passed, a monster may spawn. Getting hit by the monster will result in you losing the level immediately.
- You can place flags on the ground to help you navigate, however if the monster comes into contact with one of these flags, it may destroy it.

## Map Colours

- Black - Walls
- White - Floor
- Blue - Player tile
- Green - End point
- Gold - Keys
- Dark red - Monster
- Red - Start point
- Light grey - Flags
- Purple - Shortest path
- Lilac - Possible path
