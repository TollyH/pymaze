"""
Loads configuration options from config.ini as individual attributes.
"""
import configparser
import os
from typing import Dict, Optional


class Config:
    """
    Contains the loaded configuration options. Options will be reloaded from
    the file every time a new instance of this class is created.
    """
    def __init__(self):
        self.config = configparser.ConfigParser(allow_no_value=True)
        # Preserve the case of option names
        self.config.optionxform = str  # type: ignore
        # Look for the config.ini file in the script directory regardless of
        # working directory
        config_file_path = os.path.join(
            os.path.dirname(__file__), "config.ini"
        )
        if os.path.isfile(config_file_path):
            self.config.read(config_file_path)
            self.config_options: Dict[str, str] = dict(self.config['OPTIONS'])
        else:
            # Will cause every config option to resort to default values
            self.config_options: Dict[str, str] = {}

        # The dimensions used for the 3D view and the map
        # (not including the HUD).
        self.viewport_width = self._parse_int('VIEWPORT_WIDTH', 500)
        self.viewport_height = self._parse_int('VIEWPORT_HEIGHT', 500)

        # Whether a more detailed version of the map should be displayed
        # instead of the default limited one.
        self.enable_cheat_map = self._parse_bool('ENABLE_CHEAT_MAP', False)

        # Whether the monster should be spawned at all.
        self.monster_enabled = self._parse_bool('MONSTER_ENABLED', True)
        # If this is not None, it will be used as the time taken in seconds to
        # spawn the monster, overriding the times specific to each level.
        self.monster_start_override = self._parse_optional_float(
            'MONSTER_START_OVERRIDE', None
        )
        # How many seconds the monster will wait between each movement.
        # Decreasing this will increase the rate at which the lights flicker.
        self.monster_movement_wait = self._parse_float(
            'MONSTER_MOVEMENT_WAIT', 0.5
        )
        # Whether the scream sound should be played when the player is killed
        self.monster_sound_on_kill = self._parse_bool(
            'MONSTER_SOUND_ON_KILL', True
        )
        # Whether the monster should be displayed fullscreen when the player is
        # killed
        self.monster_display_on_kill = self._parse_bool(
            'MONSTER_DISPLAY_ON_KILL', True
        )
        # Whether the spotted sound should be played when the monster enters
        # the player's field of view
        self.monster_sound_on_spot = self._parse_bool(
            'MONSTER_SOUND_ON_SPOT', True
        )
        # The amount of time in seconds that the monster must have been outside
        # the player's field of view before the spotted sound effect will
        # play again
        self.monster_spot_timeout = self._parse_float(
            'MONSTER_SPOT_TIMEOUT', 10.0
        )
        # Whether the "lights" should flicker based on the distance of the
        # monster
        self.monster_flicker_lights = self._parse_bool(
            'MONSTER_FLICKER_LIGHTS', True
        )

        # The length of time in seconds that the compass can be used before
        # burning out
        self.compass_time = self._parse_float('COMPASS_TIME', 10.0)
        # The multiplier applied to COMPASS_TIME that it will take to recharge
        # the compass if it isn't burned out
        self.compass_charge_norm_multiplier = self._parse_float(
            'COMPASS_CHARGE_NORM_MULTIPLIER', 0.5
        )
        # The multiplier applied to COMPASS_TIME that it will take to recharge
        # the compass if it's burned out
        self.compass_charge_burn_multiplier = self._parse_float(
            'COMPASS_CHARGE_BURN_MULTIPLIER', 1.0
        )
        # The amount of time in seconds that must have elapsed since the
        # compass was last put away before it will begin to recharge.
        self.compass_charge_delay = self._parse_float(
            'COMPASS_CHARGE_DELAY', 1.5
        )

        # Amount of time in seconds before player placed walls are broken.
        self.player_wall_time = self._parse_float('PLAYER_WALL_TIME', 15.0)

        # The maximum frames per second that the game will render at.
        # Low values may cause the game window to become unresponsive.
        self.frame_rate_limit = self._parse_int('FRAME_RATE_LIMIT', 75)

        # Whether walls will be rendered with the image textures associated
        # with each level. Setting this to False will cause all walls to appear
        # in solid colour, which may also provide some performance boosts.
        self.textures_enabled = self._parse_bool('TEXTURES_ENABLED', True)
        # Similar to textures_enabled, but for the sky.
        self.sky_textures_enabled = self._parse_bool(
            'SKY_TEXTURES_ENABLED', True
        )

        # The dimensions of all the PNGs found in the textures folder.
        self.texture_width = self._parse_int('TEXTURE_WIDTH', 128)
        self.texture_height = self._parse_int('TEXTURE_HEIGHT', 128)

        # The maximum height that textures will be stretched to internally
        # before they start getting cropped to save on resources. Decreasing
        # this will improve performance, at the cost of nearby textures looking
        # jagged.
        self.texture_scale_limit = self._parse_int(
            'TEXTURE_SCALE_LIMIT', 10000
        )

        # The number of rays that will be cast to determine the height of
        # walls. Decreasing this will improve performance, but will decrease
        # visual clarity.
        self.display_columns = self._parse_int(
            'DISPLAY_COLUMNS', self.viewport_width
        )
        # Your field of vision corresponds to how spread out the rays being
        # cast are. Smaller values result in a narrower field of vision,
        # causing the walls to appear wider. A value of 50 will make each grid
        # square appear in the same aspect ratio as the 3D frame itself.
        self.display_fov = self._parse_int('DISPLAY_FOV', 50)

        # Whether maze edges will appear as walls in the 3D view.
        # Disabling this will cause the horizon to be visible, slightly ruining
        # the ceiling/floor effect.
        self.draw_maze_edge_as_wall = self._parse_bool(
            'DRAW_MAZE_EDGE_AS_WALL', True
        )

        # Larger values will result in faster speeds. Move speed is measured in
        # grid squares per second, and turn speed in radians per second.
        # Run and crawl multipliers are applied when holding Shift or CTRL
        # respectively.
        self.turn_speed = self._parse_float('TURN_SPEED', 2.5)
        self.move_speed = self._parse_float('MOVE_SPEED', 4.0)
        self.run_multiplier = self._parse_float('RUN_MULTIPLIER', 2.0)
        self.crawl_multiplier = self._parse_float('CRAWL_MULTIPLIER', 0.5)

        # Allow the presence of walls to be toggled by clicking on the map.
        # Enabling this will disable the ability to view solutions.
        # enable_cheat_map must be True for this to work.
        self.allow_realtime_editing = self._parse_bool(
            'ALLOW_REALTIME_EDITING', False
        )

    def _parse_int(self, field_name: str, default_value: int):
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.isnumeric():
            return default_value
        return int(field)

    def _parse_float(self, field_name: str, default_value: float):
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.replace(".", "", 1).isnumeric():
            return default_value
        return float(field)

    def _parse_optional_float(self, field_name: str,
                              default_value: Optional[float]):
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if field == '':
            return None
        if not field.replace(".", "", 1).isnumeric():
            return default_value
        return float(field)

    def _parse_bool(self, field_name: str,
                    default_value: bool):
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.isnumeric():
            return default_value
        return bool(int(field))
