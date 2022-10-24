# PyMaze

[![python-analysis](https://github.com/TollyH/pygame_maze/actions/workflows/python-analysis.yml/badge.svg?branch=raycasting&event=push)](https://github.com/TollyH/pygame_maze/actions/workflows/python-analysis.yml)

A pseudo-3D, grid-based maze game written in Python with PyGame using a DDA
algorithm for raycasting.

- [PyMaze](#pymaze)
  - [Installation](#installation)
  - [Controls](#controls)
  - [Cheat Map Controls](#cheat-map-controls)
  - [Instructions](#instructions)
    - [Multiplayer](#multiplayer)
  - [Map Colours](#map-colours)
    - [Game and Designer](#game-and-designer)
    - [Game Only](#game-only)
    - [Designer Only](#designer-only)
  - [Command Line Arguments (Optional)](#command-line-arguments-optional)
    - [Client](#client)
    - [Server](#server)

## Installation

*Python 3.6 or greater is required.*

1. Download the files by pressing the green "Code" button above, followed by "Download ZIP" — extracting all the files once the download is complete.
   - Alternatively, if you have git installed, run `git clone https://github.com/TollyH/pymaze.git` in a terminal to download the repository.
2. Install PyGame with the command `pip3 install pygame` on Linux or `pip install pygame` on Windows.
3. Run `__main__.py` to start the game.

## Controls

- `WASD` or `Up` and `Down` — Move around
- `Left` and `Right` or `Mouse` — Turn camera
- `Left Click` — Toggle mouse control (`ESC` can also be used to leave)
- `[` and `]` — Previous/Next Level Respectively
- `W` — Escape from monster (rapid click)
- `F` — Place/pick up flag
- `Q` — Place temporary barricade
- `T` (with gun) — Shoot
- `R` (or `ESC` outside mouse control) — Pause menu (+`Y` reset level)
- `Shift` — Run while held
- `CTRL` — Crawl while held
- `Space` — Toggle map
- `C` — Toggle monster compass
- `E` — Toggle statistics (time, moves, key counts)
- `CTRL` + `/` — Open config window

## Cheat Map Controls

*Requires the cheat map to be enabled in the configuration*

- `Space` — Toggle cheat map display
- `CTRL` + `Space` — Toggle displaying of field of view on map

## Instructions

- Simply collect all the golden keys before reaching the exit.
- In many levels, after a specific amount of time has passed, a monster may spawn. Getting hit by the monster will give you an opportunity to spam `W` to attempt to escape. There is only a certain amount of time you have per level for this, however, and running out will result in you dying and having to restart the level.
- You can place flags on the ground to help you navigate, however if the monster comes into contact with one of these flags, it may destroy it.
- You have a compass which will point toward the monster's location, however you only have a limited amount of time to use it before you must wait for it to recharge.
- You can place a temporary barricade which will act like any other wall until it breaks. You may only have one built at a time, it cannot be broken early, and it will block you as well as the monster.
- Some levels contain single use key sensor which will display the location of every key on the map for a limited amount of time.
- Levels may also contain guns. These can be fired once each and, if you hit the monster, it will be sent back to its spawn point.

### Multiplayer

PyMaze also has a multiplayer death-match mode, operating with a simple client/server model. In this mode, the monster and all pickups are removed, and instead you must simply shoot at other players to kill them. You start with a gun, and have infinite ammo.

Right-clicking on the play button on the title screen will prompt for a server address and port to connect to, and middle-clicking will start hosting a server from your machine. You can play with people on the same network as you by giving them your private IP address (usually in the form `192.168.xxx.xxx` - lookup online how to find this). If you want to play over a wider area, you will need to find your public IP address and setup port forwarding, tutorials for which can also be found online.

**Disclaimer: The developers of PyMaze make no guarantee as to the security of the multiplayer server included in this repository. Forwarding a port being used by this server to the public internet is not recommended and is done entirely at your own risk. Under no circumstances will the developers of PyMaze accept any responsibility for any consequences that may arise as a result of running this software.**

## Map Colours

### Game and Designer

- Black — Walls
- White — Floor
- Green — End point (Cheat map only)
- Gold — Keys (Always with cheat map, otherwise only with key sensor)
- Dark green (dark red in designer) — Monster spawn
- Red — Start point
- Dark gold — Key sensors (Cheat map only)
- Grey — Guns (Cheat map only)

### Game Only

- Blue — Player tile
- Dark red — Monster (Cheat map only)
- Turquoise — Flags
- Purple — Player placed wall

### Designer Only

- Purple — Decorations

## Command Line Arguments (Optional)

### Client

- `-P=/path/to/maze_levels.json` or `--level-json-path=/path/to/maze_levels.json`
- `-C=/path/to/config.ini` or `--config-ini-path=/path/to/config.ini`
- `-S="host:port"` or `--multiplayer-server="host:port"`

### Server

- `-P=/path/to/maze_levels.json` or `--level-json-path=/path/to/maze_levels.json`
- `-T=port` or `--port=port`
- `-L=level_index` or `--level=level_index`

---

**Copyright © 2022  Ptolemy Hill, Finlay Griffiths, and Tomas Reynolds**
