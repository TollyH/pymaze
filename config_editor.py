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
            self.gui_basic_config_frame, from_=10, to=1000,
            value=self.parse_int('VIEWPORT_WIDTH', 500),
            command=lambda x: self.on_scale_change('VIEWPORT_WIDTH', x, 0)
        )
        self.gui_viewport_width_label.pack(fill="x", expand=True)
        self.gui_viewport_width_slider.pack(fill="x", expand=True)

        self.gui_viewport_height_label = tkinter.Label(
            self.gui_basic_config_frame, anchor=tkinter.W,
            text=f"View Height — ({self.parse_int('VIEWPORT_HEIGHT', 500)})"
        )
        self.scale_labels['VIEWPORT_HEIGHT'] = (
            self.gui_viewport_height_label, "View Height — ({})"
        )
        self.gui_viewport_height_slider = tkinter.ttk.Scale(
            self.gui_basic_config_frame, from_=10, to=1000,
            value=self.parse_int('VIEWPORT_HEIGHT', 500),
            command=lambda x: self.on_scale_change('VIEWPORT_HEIGHT', x, 0)
        )
        self.gui_viewport_height_label.pack(fill="x", expand=True)
        self.gui_viewport_height_slider.pack(fill="x", expand=True)

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
        self.gui_cheat_map_check.pack(fill="x", expand=True)

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
        self.gui_monster_check.pack(fill="x", expand=True)

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
        self.gui_monster_kill_sound_check.pack(fill="x", expand=True)

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
        self.gui_monster_kill_display_check.pack(fill="x", expand=True)

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
        self.gui_monster_spot_sound_check.pack(fill="x", expand=True)

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
        self.gui_monster_flicker_lights_check.pack(fill="x", expand=True)

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
        self.gui_frame_rate_limit_label.pack(fill="x", expand=True)
        self.gui_frame_rate_limit_slider.pack(fill="x", expand=True)

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
        self.gui_textures_check.pack(fill="x", expand=True)

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
        self.gui_display_columns_label.pack(fill="x", expand=True)
        self.gui_display_columns_slider.pack(fill="x", expand=True)

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
        Field is the name of the ini field to change.
        """
        if field == "VIEWPORT_WIDTH":
            new_width = int(new_value.split(".")[0])
            # Display columns must always be less than or equal to view width
            self.gui_display_columns_slider.config(to=new_width)
            if (int(self.gui_display_columns_slider.get())
                    >= self.parse_int('VIEWPORT_WIDTH', 500)):
                self.gui_display_columns_slider.set(new_width)  # type: ignore
        # Truncate the number of decimal places on a float represented as a
        # string.
        to_store = (
            new_value.split(".")[0] + "."
            + new_value.split(".")[1][:decimal_places]
        ).strip('.')
        # INI files can only contain strings
        self.config_options[field] = to_store
        self.scale_labels[field][0].config(
            text=self.scale_labels[field][1].format(to_store)
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
