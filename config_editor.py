"""
Contains the definition for ConfigEditorApp, a GUI for editing the game's
config file easily.
"""
import configparser
import os
import tkinter
import tkinter.ttk
from typing import Dict, Optional, Tuple


class ConfigEditorApp:
    """
    A tkinter GUI providing a user-friendly way to easily edit the game's
    config file. While the app should still function if the file is erroneous
    or missing, unexpected behaviour may occur.
    """
    def __init__(self):
        self.config_file_path = os.path.join(
            os.path.dirname(__file__), "config.ini"
        )
        self.config = configparser.ConfigParser(allow_no_value=True)
        # Preserve the case of option names
        self.config.optionxform = str  # type: ignore
        # Looks for the config.ini file in the script directory regardless of
        # working directory
        self.config.read(self.config_file_path)
        if 'OPTIONS' not in self.config:
            self.config['OPTIONS'] = {}
        self.config_options = self.config['OPTIONS']

        self.window = tkinter.Tk()
        self.window.wm_title("PyGame Maze Config")

        # Stores the labels above sliders along with their template strings
        # so that their text values can be dynamically changed easily
        self.scale_labels: Dict[str, Tuple[tkinter.Label, str]] = {}
        # Stores the checkbox variables for each bool field so that their state
        # can be dynamically retrieved easily
        self.checkbuttons: Dict[str, tkinter.IntVar] = {}

        self.gui_top_tab_control = tkinter.ttk.Notebook(self.window)
        self.gui_top_tab_control.pack(fill="both", expand=True)

        self.gui_basic_config_frame = tkinter.Frame(self.gui_top_tab_control)
        self.gui_top_tab_control.add(self.gui_basic_config_frame, text="Basic")

        self.gui_advanced_config_frame = tkinter.Frame(
            self.gui_top_tab_control
        )
        self.gui_top_tab_control.add(
            self.gui_advanced_config_frame, text="Advanced"
        )

        self.gui_viewport_width_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text=f"View Width — ({self.parse_int('VIEWPORT_WIDTH', 500)})"
        )
        self.scale_labels['VIEWPORT_WIDTH'] = (
            self.gui_viewport_width_label, "View Width — ({})"
        )
        self.gui_viewport_width_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=500, to=3840,
            value=self.parse_int('VIEWPORT_WIDTH', 500),
            command=lambda x: self.on_scale_change('VIEWPORT_WIDTH', x, 0)
        )
        self.gui_viewport_width_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_viewport_width_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_viewport_height_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text=f"View Height — ({self.parse_int('VIEWPORT_HEIGHT', 500)})"
        )
        self.scale_labels['VIEWPORT_HEIGHT'] = (
            self.gui_viewport_height_label, "View Height — ({})"
        )
        self.gui_viewport_height_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=500, to=2160,
            value=self.parse_int('VIEWPORT_HEIGHT', 500),
            command=lambda x: self.on_scale_change('VIEWPORT_HEIGHT', x, 0)
        )
        self.gui_viewport_height_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_viewport_height_slider.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['ENABLE_CHEAT_MAP'] = tkinter.IntVar()
        self.gui_cheat_map_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['ENABLE_CHEAT_MAP'],
            text="Enable the cheat map"
        )
        if self.parse_bool('ENABLE_CHEAT_MAP', False):
            self.gui_cheat_map_check.select()
        # Set command after select to prevent it being called
        self.gui_cheat_map_check.config(
            command=lambda: self.on_checkbutton_click('ENABLE_CHEAT_MAP')
        )
        self.gui_cheat_map_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['MONSTER_ENABLED'] = tkinter.IntVar()
        self.gui_monster_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['MONSTER_ENABLED'],
            text="Enable the monster"
        )
        if self.parse_bool('MONSTER_ENABLED', True):
            self.gui_monster_check.select()
        # Set command after select to prevent it being called
        self.gui_monster_check.config(
            command=lambda: self.on_checkbutton_click('MONSTER_ENABLED')
        )
        self.gui_monster_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['MONSTER_SOUND_ON_KILL'] = tkinter.IntVar()
        self.gui_monster_kill_sound_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['MONSTER_SOUND_ON_KILL'],
            text="Play the jumpscare sound on death"
        )
        if self.parse_bool('MONSTER_SOUND_ON_KILL', True):
            self.gui_monster_kill_sound_check.select()
        # Set command after select to prevent it being called
        self.gui_monster_kill_sound_check.config(
            command=lambda: self.on_checkbutton_click('MONSTER_SOUND_ON_KILL')
        )
        self.gui_monster_kill_sound_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['MONSTER_DISPLAY_ON_KILL'] = tkinter.IntVar()
        self.gui_monster_kill_display_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['MONSTER_DISPLAY_ON_KILL'],
            text="Display the monster fullscreen on death"
        )
        if self.parse_bool('MONSTER_DISPLAY_ON_KILL', True):
            self.gui_monster_kill_display_check.select()
        # Set command after select to prevent it being called
        self.gui_monster_kill_display_check.config(
            command=lambda:
                self.on_checkbutton_click('MONSTER_DISPLAY_ON_KILL')
        )
        self.gui_monster_kill_display_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['MONSTER_SOUND_ON_SPOT'] = tkinter.IntVar()
        self.gui_monster_spot_sound_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['MONSTER_SOUND_ON_SPOT'],
            text="Play a jumpscare sound when the monster is spotted"
        )
        if self.parse_bool('MONSTER_SOUND_ON_SPOT', True):
            self.gui_monster_spot_sound_check.select()
        # Set command after select to prevent it being called
        self.gui_monster_spot_sound_check.config(
            command=lambda: self.on_checkbutton_click('MONSTER_SOUND_ON_SPOT')
        )
        self.gui_monster_spot_sound_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['MONSTER_FLICKER_LIGHTS'] = tkinter.IntVar()
        self.gui_monster_flicker_lights_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['MONSTER_FLICKER_LIGHTS'],
            text="Flicker lights based on distance to the monster"
        )
        if self.parse_bool('MONSTER_FLICKER_LIGHTS', True):
            self.gui_monster_flicker_lights_check.select()
        # Set command after select to prevent it being called
        self.gui_monster_flicker_lights_check.config(
            command=lambda: self.on_checkbutton_click('MONSTER_FLICKER_LIGHTS')
        )
        self.gui_monster_flicker_lights_check.pack(fill="x", anchor=tkinter.NW)

        self.gui_frame_rate_limit_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text=f"Max FPS — ({self.parse_int('FRAME_RATE_LIMIT', 75)})"
        )
        self.scale_labels['FRAME_RATE_LIMIT'] = (
            self.gui_frame_rate_limit_label, "Max FPS — ({})"
        )
        self.gui_frame_rate_limit_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=1, to=360,
            value=self.parse_int('FRAME_RATE_LIMIT', 75),
            command=lambda x: self.on_scale_change('FRAME_RATE_LIMIT', x, 0)
        )
        self.gui_frame_rate_limit_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_frame_rate_limit_slider.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['TEXTURES_ENABLED'] = tkinter.IntVar()
        self.gui_textures_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['TEXTURES_ENABLED'],
            text="Display textures on walls (impacts performance heavily)"
        )
        if self.parse_bool('TEXTURES_ENABLED', True):
            self.gui_textures_check.select()
        # Set command after select to prevent it being called
        self.gui_textures_check.config(
            command=lambda: self.on_checkbutton_click('TEXTURES_ENABLED')
        )
        self.gui_textures_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['SKY_TEXTURES_ENABLED'] = tkinter.IntVar()
        self.gui_sky_textures_check = tkinter.Checkbutton(
            self.gui_basic_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['SKY_TEXTURES_ENABLED'],
            text="Display textured sky (impacts performance)"
        )
        if self.parse_bool('SKY_TEXTURES_ENABLED', True):
            self.gui_sky_textures_check.select()
        # Set command after select to prevent it being called
        self.gui_sky_textures_check.config(
            command=lambda: self.on_checkbutton_click('SKY_TEXTURES_ENABLED')
        )
        self.gui_sky_textures_check.pack(fill="x", anchor=tkinter.NW)

        display_columns_default = self.parse_int(
            'DISPLAY_COLUMNS', self.parse_int('VIEWPORT_WIDTH', 500)
        )
        self.gui_display_columns_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text="Render Resolution (lower this to improve performance) — "
            + f"({display_columns_default})"
        )
        self.scale_labels['DISPLAY_COLUMNS'] = (
            self.gui_display_columns_label,
            "Render Resolution (lower this to improve performance) — ({})"
        )
        self.gui_display_columns_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=24,
            to=self.parse_int('VIEWPORT_WIDTH', 500),
            value=display_columns_default,
            command=lambda x: self.on_scale_change('DISPLAY_COLUMNS', x, 0)
        )
        self.gui_display_columns_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_display_columns_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_turn_speed_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text=f"Turn Sensitivity — ({self.parse_float('TURN_SPEED', 2.5)})"
        )
        self.scale_labels['TURN_SPEED'] = (
            self.gui_turn_speed_label, "Turn Sensitivity — ({})"
        )
        self.gui_turn_speed_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=0.1, to=10.0,
            value=self.parse_float('TURN_SPEED', 2.5),
            command=lambda x: self.on_scale_change('TURN_SPEED', x, 1)
        )
        self.gui_turn_speed_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_turn_speed_slider.pack(fill="x", anchor=tkinter.NW)

        monster_start_override_value = self.parse_optional_float(
            'MONSTER_START_OVERRIDE', None
        )
        self.gui_monster_start_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Monster spawn override (seconds) — "
            + f"({self.parse_optional_float('MONSTER_START_OVERRIDE', None)})"
        )
        self.gui_monster_start_info_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Note: This will not affect levels with no monster", fg="blue"
        )
        self.scale_labels['MONSTER_START_OVERRIDE'] = (
            self.gui_monster_start_label,
            "Monster spawn override (seconds) — ({})"
        )
        self.gui_monster_start_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=-0.1, to=999.9,
            value=(
                monster_start_override_value
                if monster_start_override_value is not None else -0.1
            ),
            command=lambda x: self.on_scale_change(
                'MONSTER_START_OVERRIDE', x, 1
            )
        )
        self.gui_monster_start_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_monster_start_info_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_monster_start_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_monster_movement_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Time between monster movements (seconds) — "
            + f"({self.parse_float('MONSTER_MOVEMENT_WAIT', 0.5)})"
        )
        self.gui_monster_movement_warning_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Warning: This will affect the rate at which lights flicker",
            fg="darkorange"
        )
        self.scale_labels['MONSTER_MOVEMENT_WAIT'] = (
            self.gui_monster_movement_label,
            "Time between monster movements (seconds) — ({})"
        )
        self.gui_monster_movement_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=0.01, to=10.0,
            value=self.parse_float('MONSTER_MOVEMENT_WAIT', 0.5),
            command=lambda x: self.on_scale_change(
                'MONSTER_MOVEMENT_WAIT', x, 2
            )
        )
        self.gui_monster_movement_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_monster_movement_warning_label.pack(
            fill="x", anchor=tkinter.NW
        )
        self.gui_monster_movement_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_monster_spot_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Minimum time between spotted jumpscare sounds (seconds) — "
            + f"({self.parse_float('MONSTER_SPOT_TIMEOUT', 10.0)})"
        )
        self.scale_labels['MONSTER_SPOT_TIMEOUT'] = (
            self.gui_monster_spot_label,
            "Minimum time between spotted jumpscare sounds (seconds) — ({})"
        )
        self.gui_monster_spot_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=0.1, to=60.0,
            value=self.parse_float('MONSTER_SPOT_TIMEOUT', 10.0),
            command=lambda x: self.on_scale_change(
                'MONSTER_SPOT_TIMEOUT', x, 1
            )
        )
        self.gui_monster_spot_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_monster_spot_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_compass_time_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Time before compass burnout (seconds) — "
            + f"({self.parse_float('COMPASS_TIME', 10.0)})"
        )
        self.scale_labels['COMPASS_TIME'] = (
            self.gui_compass_time_label,
            "Time before compass burnout (seconds) — ({})"
        )
        self.gui_compass_time_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=1.0, to=60.0,
            value=self.parse_float('COMPASS_TIME', 10.0),
            command=lambda x: self.on_scale_change('COMPASS_TIME', x, 1)
        )
        self.gui_compass_time_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_compass_time_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_compass_norm_charge_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Normal compass recharge multiplier — "
            + f"({self.parse_float('COMPASS_CHARGE_NORM_MULTIPLIER', 0.5)})"
        )
        self.scale_labels['COMPASS_CHARGE_NORM_MULTIPLIER'] = (
            self.gui_compass_norm_charge_label,
            "Normal compass recharge multiplier — ({})"
        )
        self.gui_compass_norm_charge_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=0.1, to=10.0,
            value=self.parse_float('COMPASS_CHARGE_NORM_MULTIPLIER', 0.5),
            command=lambda x: self.on_scale_change(
                'COMPASS_CHARGE_NORM_MULTIPLIER', x, 1
            )
        )
        self.gui_compass_norm_charge_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_compass_norm_charge_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_compass_burn_charge_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Burned compass recharge multiplier — "
            + f"({self.parse_float('COMPASS_CHARGE_BURN_MULTIPLIER', 1.0)})"
        )
        self.scale_labels['COMPASS_CHARGE_BURN_MULTIPLIER'] = (
            self.gui_compass_burn_charge_label,
            "Burned compass recharge multiplier — ({})"
        )
        self.gui_compass_burn_charge_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=0.1, to=10.0,
            value=self.parse_float('COMPASS_CHARGE_BURN_MULTIPLIER', 1.0),
            command=lambda x: self.on_scale_change(
                'COMPASS_CHARGE_BURN_MULTIPLIER', x, 1
            )
        )
        self.gui_compass_burn_charge_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_compass_burn_charge_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_compass_charge_delay_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Delay before compass begins recharging (seconds) — "
            + f"({self.parse_float('COMPASS_CHARGE_DELAY', 1.5)})"
        )
        self.scale_labels['COMPASS_CHARGE_DELAY'] = (
            self.gui_compass_charge_delay_label,
            "Delay before compass begins recharging (seconds) — ({})"
        )
        self.gui_compass_charge_delay_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=0.1, to=10.0,
            value=self.parse_float('COMPASS_CHARGE_DELAY', 1.5),
            command=lambda x: self.on_scale_change(
                'COMPASS_CHARGE_DELAY', x, 1
            )
        )
        self.gui_compass_charge_delay_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_compass_charge_delay_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_texture_scale_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text="Internal texture stretch limit — "
            + f"({self.parse_int('TEXTURE_SCALE_LIMIT', 10000)})"
        )
        self.gui_texture_scale_info_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W, fg="blue",
            text="Note: Higher values will make nearby textures appear jagged"
        )
        self.scale_labels['TEXTURE_SCALE_LIMIT'] = (
            self.gui_texture_scale_label,
            "Internal texture stretch limit — ({})"
        )
        self.gui_texture_scale_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=1, to=100000,
            value=self.parse_int('TEXTURE_SCALE_LIMIT', 10000),
            command=lambda x: self.on_scale_change('TEXTURE_SCALE_LIMIT', x, 0)
        )
        self.gui_texture_scale_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_texture_scale_info_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_texture_scale_slider.pack(fill="x", anchor=tkinter.NW)

        self.gui_display_fov_label = tkinter.Label(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            text=f"Field of View — ({self.parse_int('DISPLAY_FOV', 50)})"
        )
        self.scale_labels['DISPLAY_FOV'] = (
            self.gui_display_fov_label, "Field of View — ({})"
        )
        self.gui_display_fov_slider = tkinter.ttk.Scale(
            self.gui_advanced_config_frame, from_=1, to=100,
            value=self.parse_int('DISPLAY_FOV', 50),
            command=lambda x: self.on_scale_change('DISPLAY_FOV', x, 0)
        )
        self.gui_display_fov_label.pack(fill="x", anchor=tkinter.NW)
        self.gui_display_fov_slider.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['DRAW_MAZE_EDGE_AS_WALL'] = tkinter.IntVar()
        self.gui_draw_maze_edge_check = tkinter.Checkbutton(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['DRAW_MAZE_EDGE_AS_WALL'],
            text="Draw the edge of the maze as if it were a wall"
        )
        if self.parse_bool('DRAW_MAZE_EDGE_AS_WALL', True):
            self.gui_draw_maze_edge_check.select()
        # Set command after select to prevent it being called
        self.gui_draw_maze_edge_check.config(
            command=lambda: self.on_checkbutton_click('DRAW_MAZE_EDGE_AS_WALL')
        )
        self.gui_draw_maze_edge_check.pack(fill="x", anchor=tkinter.NW)

        self.checkbuttons['ALLOW_REALTIME_EDITING'] = tkinter.IntVar()
        self.gui_realtime_edit_check = tkinter.Checkbutton(
            self.gui_advanced_config_frame, anchor=tkinter.W,
            variable=self.checkbuttons['ALLOW_REALTIME_EDITING'],
            text="Allow realtime editing on the cheat map (disables solutions)"
        )
        if self.parse_bool('ALLOW_REALTIME_EDITING', True):
            self.gui_realtime_edit_check.select()
        # Set command after select to prevent it being called
        self.gui_realtime_edit_check.config(
            command=lambda: self.on_checkbutton_click('ALLOW_REALTIME_EDITING')
        )
        self.gui_realtime_edit_check.pack(fill="x", anchor=tkinter.NW)

        self.gui_save_button = tkinter.ttk.Button(
            self.window, command=self.save_config, text="Save"
        )
        self.gui_save_button.pack()

        self.window.mainloop()

    def on_scale_change(self, field: str, new_value: str, decimal_places: int):
        """
        To be called when the user moves a slider. New_value will always be a
        floating point value represented as a str because of how Tkinter Scales
        work, which will be truncated to the provided number of decimal places.
        Field is the name of the ini field to change. If new_value is negative,
        an empty string will be stored in the ini field instead to represent
        None.
        """
        if field == "VIEWPORT_WIDTH":
            new_width = int(new_value.split(".")[0])
            # Display columns must always be less than or equal to view width
            self.gui_display_columns_slider.config(to=new_width)
            if (int(self.gui_display_columns_slider.get())
                    >= self.parse_int('VIEWPORT_WIDTH', 500)):
                self.gui_display_columns_slider.set(new_width)  # type: ignore
        # Truncate the number of decimal places on a float represented as a
        # string. If the float is negative, it will be converted to an empty
        # string to represent None.
        to_store = (
            new_value.split(".")[0] + "."
            + new_value.split(".")[1][:decimal_places]
        ).strip('.') if not new_value.startswith('-') else ''
        # INI files can only contain strings
        self.config_options[field] = to_store
        self.scale_labels[field][0].config(
            text=self.scale_labels[field][1].format(
                to_store if to_store != '' else 'None'
            )
        )

    def on_checkbutton_click(self, field: str):
        """
        To be called when the user checks or unchecks a checkbutton. Toggles
        the boolean value current in the specified field.
        """
        # INI files can only contain strings
        self.config_options[field] = str(self.checkbuttons[field].get())

    def save_config(self):
        """
        Save the potentially modified configuration options to config.ini
        """
        with open(self.config_file_path, 'w', encoding="utf8") as file:
            self.config.write(file)

    def parse_int(self, field_name: str, default_value: int):
        """
        Get a value from the configuration with the specified field name as an
        integer. If the value is missing or invalid, default_value will be
        returned.
        """
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.isnumeric():
            return default_value
        return int(field)

    def parse_float(self, field_name: str, default_value: float):
        """
        Get a value from the configuration with the specified field name as a
        float. If the value is missing or invalid, default_value will be
        returned.
        """
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.replace(".", "", 1).isnumeric():
            return default_value
        return float(field)

    def parse_optional_float(self, field_name: str,
                             default_value: Optional[float]):
        """
        Get a value from the configuration with the specified field name as a
        float or None. If the value is missing or invalid, default_value will
        be returned.
        """
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if field == '':
            return None
        if not field.replace(".", "", 1).isnumeric():
            return default_value
        return float(field)

    def parse_bool(self, field_name: str, default_value: bool):
        """
        Get a value from the configuration with the specified field name as a
        bool. If the value is missing or invalid, default_value will be
        returned.
        """
        if field_name not in self.config_options:
            return default_value
        field = self.config_options[field_name]
        if not field.isnumeric():
            return default_value
        return bool(int(field))


if __name__ == "__main__":
    ConfigEditorApp()
