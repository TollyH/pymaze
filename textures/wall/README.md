# Wall Texture Names

Wall textures are fixed-size (128x128 by default - configurable in `__main__.py`) PNG images named with the 0-based indices of the levels they will be used in, separated by dashes. For example, a wall texture for levels 1, 3 and 7 would be named `0-2-6.png`. This has been done to keep `maze_levels.py` compatible with the flat branch.
