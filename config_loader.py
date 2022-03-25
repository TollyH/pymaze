"""
Loads configuration options from config.ini as individual variables.
"""
import configparser
import os
from typing import Dict, Optional

_config = configparser.ConfigParser(allow_no_value=True)
# Preserve the case of option names
_config.optionxform = str  # type: ignore
_config_file_path = os.path.join(os.path.dirname(__file__), "config.ini")
if os.path.isfile(_config_file_path):
    # Looks for the config.ini file in the script directory regardless of
    # working directory
    _config.read(_config_file_path)
    _config_options: Dict[str, str] = dict(_config['OPTIONS'])
else:
    # Will cause every config option to resort to default values
    _config_options: Dict[str, str] = {}


def _parse_int(field_name: str, default_value: int):
    if field_name not in _config_options:
        return default_value
    field = _config_options[field_name]
    if not field.isnumeric():
        return default_value
    return int(field)


def _parse_float(field_name: str, default_value: float):
    if field_name not in _config_options:
        return default_value
    field = _config_options[field_name]
    if not field.replace(".", "", 1).isnumeric():
        return default_value
    return float(field)


def _parse_optional_float(field_name: str, default_value: Optional[float]):
    if field_name not in _config_options:
        return default_value
    field = _config_options[field_name]
    if field == '':
        return None
    if not field.replace(".", "", 1).isnumeric():
        return default_value
    return float(field)


def _parse_bool(field_name: str, default_value: bool):
    if field_name not in _config_options:
        return default_value
    field = _config_options[field_name]
    if not field.isnumeric():
        return default_value
    return bool(int(field))


# The dimensions used for the 3D view and the map (not including the HUD).
VIEWPORT_WIDTH = _parse_int('VIEWPORT_WIDTH', 500)
VIEWPORT_HEIGHT = _parse_int('VIEWPORT_HEIGHT', 500)

# Whether a more detailed version of the map should be displayed instead of the
# default limited one.
ENABLE_CHEAT_MAP = _parse_bool('ENABLE_CHEAT_MAP', False)

# Whether the monster should be spawned at all.
MONSTER_ENABLED = _parse_bool('MONSTER_ENABLED', True)
# If this is not None, it will be used as the time taken in seconds to spawn
# the monster, overriding the times specific to each level.
MONSTER_START_OVERRIDE = _parse_optional_float('MONSTER_START_OVERRIDE', None)
# How many seconds the monster will wait between each movement. Decreasing this
# will increase the rate at which the lights flicker.
MONSTER_MOVEMENT_WAIT = _parse_float('MONSTER_MOVEMENT_WAIT', 0.5)
# Whether the scream sound should be played when the player is killed
MONSTER_SOUND_ON_KILL = _parse_bool('MONSTER_SOUND_ON_KILL', True)
# Whether the monster should be displayed fullscreen when the player is killed
MONSTER_DISPLAY_ON_KILL = _parse_bool('MONSTER_DISPLAY_ON_KILL', True)
# Whether the spotted sound should be played when the monster enters the
# player's field of view
MONSTER_SOUND_ON_SPOT = _parse_bool('MONSTER_SOUND_ON_SPOT', True)
# The amount of time in seconds that the monster must have been outside the
# player's field of view before the spotted sound effect will play again
MONSTER_SPOT_TIMEOUT = _parse_float('MONSTER_SPOT_TIMEOUT', 10.0)
# Whether the "lights" should flicker based on the distance of the monster
MONSTER_FLICKER_LIGHTS = _parse_bool('MONSTER_FLICKER_LIGHTS', True)

# The length of time in seconds that the compass can be used before burning out
COMPASS_TIME = _parse_float('COMPASS_TIME', 10.0)
# The multiplier applied to COMPASS_TIME that it will take to recharge the
# compass if it isn't burned out
COMPASS_CHARGE_NORM_MULTIPLIER = _parse_float(
    'COMPASS_CHARGE_NORM_MULTIPLIER', 0.5
)
# The multiplier applied to COMPASS_TIME that it will take to recharge the
# compass if it's burned out
COMPASS_CHARGE_BURN_MULTIPLIER = _parse_float(
    'COMPASS_CHARGE_BURN_MULTIPLIER', 1.0
)
# The amount of time in seconds that must have elapsed since the compass was
# last put away before it will begin to recharge.
COMPASS_CHARGE_DELAY = _parse_float('COMPASS_CHARGE_DELAY', 1.5)

# The maximum frames per second that the game will render at. Low values may
# cause the game window to become unresponsive.
FRAME_RATE_LIMIT = _parse_int('FRAME_RATE_LIMIT', 75)

# Whether walls will be rendered with the image textures associated with each
# level. Setting this to False will cause all walls to appear in solid colour,
# which may also provide some performance boosts.
TEXTURES_ENABLED = _parse_bool('TEXTURES_ENABLED', True)

# The dimensions of all the PNGs found in the textures folder.
TEXTURE_WIDTH = _parse_int('TEXTURE_WIDTH', 128)
TEXTURE_HEIGHT = _parse_int('TEXTURE_HEIGHT', 128)

# The maximum height that textures will be stretched to internally before they
# start getting cropped to save on resources. Decreasing this will improve
# performance, at the cost of nearby textures looking jagged.
TEXTURE_SCALE_LIMIT = _parse_int('TEXTURE_SCALE_LIMIT', 10000)

# The number of rays that will be cast to determine the height of walls.
# Decreasing this will improve performance, but will decrease visual clarity.
DISPLAY_COLUMNS = _parse_int('DISPLAY_COLUMNS', VIEWPORT_WIDTH)
# Your field of vision corresponds to how spread out the rays being cast are.
# Smaller values result in a narrower field of vision, causing the walls to
# appear wider. A value of 50 will make each grid square appear in the same
# aspect ratio as the 3D frame itself.
DISPLAY_FOV = _parse_int('DISPLAY_FOV', 50)

# Whether maze edges will appear as walls in the 3D view. Disabling this will
# cause the horizon to be visible, slightly ruining the ceiling/floor effect.
DRAW_MAZE_EDGE_AS_WALL = _parse_bool('DRAW_MAZE_EDGE_AS_WALL', True)

# Larger values will result in faster speeds. Move speed is measured in grid
# squares per second, and turn speed in radians per second. Run and crawl
# multipliers are applied when holding Shift or CTRL respectively.
TURN_SPEED = _parse_float('TURN_SPEED', 2.5)
MOVE_SPEED = _parse_float('MOVE_SPEED', 4.0)
RUN_MULTIPLIER = _parse_float('RUN_MULTIPLIER', 2.0)
CRAWL_MULTIPLIER = _parse_float('CRAWL_MULTIPLIER', 0.5)

# Allow the presence of walls to be toggled by clicking on the map. Enabling
# this will disable the ability to view solutions. ENABLE_CHEAT_MAP must be
# True for this to work.
ALLOW_REALTIME_EDITING = _parse_bool('ALLOW_REALTIME_EDITING', False)
