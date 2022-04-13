"""
Contains the definition for LevelDesigner, a GUI for editing the game's
level JSON files easily.
"""
import copy
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import tkinter.ttk
from glob import glob
from typing import Dict, List, Optional, Tuple

import config_loader
import maze_levels
import screen_drawing
from level import Level

# Tools
SELECT = 0
WALL = 1
START = 2
END = 3
KEY = 4
SENSOR = 5
GUN = 6
MONSTER = 7


def rgb_to_hex(red: int, green: int, blue: int) -> str:
    """
    Convert RGB colour values to a hex string
    """
    return f'#{red:02x}{green:02x}{blue:02x}'


def is_tile_free(level: Level, tile: Tuple[int, int]) -> bool:
    """
    Determine whether a particular tile in a level is free to have a wall
    placed on it.
    """
    if not level.is_coord_in_bounds(tile):
        return False
    if tile in (level.start_point, level.end_point, level.monster_start):
        return False
    if tile in (
            level.original_exit_keys | level.original_key_sensors
            | level.original_guns):
        return False
    return True


class LevelDesigner:
    """
    A tkinter GUI providing a user-friendly way to easily edit the game's
    level JSON files. The game will always load from 'maze_levels.json',
    however you can load and save to wherever you like with this editor.
    """
    def __init__(self) -> None:
        # Change working directory to the directory where the script is located
        # This prevents issues with required files not being found.
        os.chdir(os.path.dirname(__file__))

        self._cfg = config_loader.Config()
        self.current_path: Optional[str] = None
        self.levels: List[Level] = []
        self.current_level = -1
        self.current_tool = SELECT
        self.current_tile = (-1, -1)
        # [(current_level, [Level, ...]), ...]
        self.undo_stack: List[Tuple[int, List[Level]]] = []
        self.unsaved_changes = False
        # Used to prevent the slider commands being called when
        # programmatically setting the slider values.
        self.do_slider_update = True

        self.window = tkinter.Tk()
        self.window.wm_title("Level Designer - No File")
        self.window.wm_iconbitmap(
            os.path.join("window_icons", "editor.ico")
        )

        with open("level_designer_descriptions.txt") as file:
            # {CONSTANT_VALUE: description}
            self.descriptions: Dict[int, str] = {
                globals()[x.split("|")[0].upper()]: x.split("|")[1]
                for x in file.read().strip().splitlines()
            }
        self.textures: Dict[str, tkinter.PhotoImage] = {
            os.path.split(x)[-1].split(".")[0]: tkinter.PhotoImage(file=x)
            for x in glob(os.path.join("textures", "wall", "*.png"))
        }
        self.textures["placeholder"] = (
            tkinter.PhotoImage(
                file=os.path.join("textures", "placeholder.png")
            )
        )

        # {CONSTANT_VALUE: PhotoImage}
        self.tool_icons: Dict[int, tkinter.PhotoImage] = {
            globals()[os.path.split(x)[-1].split(".")[0].upper()]:
                tkinter.PhotoImage(file=x)
            for x in glob(os.path.join("designer_icons", "*.png"))
        }
        self.tool_icons[-1] = tkinter.PhotoImage()

        self.gui_tools_frame = tkinter.Frame(self.window)
        self.gui_tools_frame.pack(
            side=tkinter.LEFT, fill=tkinter.Y, padx=5, pady=5
        )
        self.gui_map_frame = tkinter.Frame(self.window)
        self.gui_map_frame.pack(
            side=tkinter.LEFT, fill=tkinter.Y, padx=5, pady=5
        )
        self.gui_properties_frame = tkinter.Frame(self.window)
        self.gui_properties_frame.pack(
            side=tkinter.LEFT, fill=tkinter.Y, padx=5, pady=5
        )
        self.gui_operation_frame = tkinter.Frame(self.window)
        self.gui_operation_frame.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=5, pady=5
        )

        self.gui_tool_select = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                SELECT, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, state=tkinter.DISABLED,
            command=lambda: self.select_tool(SELECT)
        )
        self.gui_tool_select.pack(pady=2)

        self.gui_tool_wall = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                WALL, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(WALL)
        )
        self.gui_tool_wall.pack(pady=2)

        self.gui_tool_start = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                START, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(START)
        )
        self.gui_tool_start.pack(pady=2)

        self.gui_tool_end = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                END, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(END)
        )
        self.gui_tool_end.pack(pady=2)

        self.gui_tool_key = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                KEY, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(KEY)
        )
        self.gui_tool_key.pack(pady=2)

        self.gui_tool_sensor = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                SENSOR, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(SENSOR)
        )
        self.gui_tool_sensor.pack(pady=2)

        self.gui_tool_gun = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                GUN, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(GUN)
        )
        self.gui_tool_gun.pack(pady=2)

        self.gui_tool_monster = tkinter.Button(
            self.gui_tools_frame, image=self.tool_icons.get(
                MONSTER, self.tool_icons[-1]  # Placeholder
            ), width=24, height=24, command=lambda: self.select_tool(MONSTER)
        )
        self.gui_tool_monster.pack(pady=2)

        self.tool_buttons = [
            self.gui_tool_select, self.gui_tool_wall, self.gui_tool_start,
            self.gui_tool_end, self.gui_tool_key, self.gui_tool_sensor,
            self.gui_tool_gun, self.gui_tool_monster
        ]

        self.gui_map_canvas = tkinter.Canvas(
            self.gui_map_frame, width=self._cfg.viewport_width + 1,
            height=self._cfg.viewport_height + 1
        )
        self.gui_map_canvas.bind("<Button-1>", self.on_map_canvas_click)
        self.gui_map_canvas.pack()

        self.blank_photo_image = tkinter.PhotoImage()
        self.gui_selected_square_description = tkinter.Label(
            self.gui_properties_frame, wraplength=150, borderwidth=1,
            relief=tkinter.SOLID, compound=tkinter.CENTER, anchor=tkinter.NW,
            text="Nothing is currently selected", justify=tkinter.LEFT,
            image=self.blank_photo_image, width=150, height=150
            # PhotoImage is so that width and height are given in pixels.
        )
        self.gui_selected_square_description.pack(padx=2, pady=2)

        # These are left unpacked deliberately
        self.gui_dimension_width_label = tkinter.Label(
            self.gui_properties_frame, anchor=tkinter.W
        )
        self.gui_dimension_width_slider = tkinter.ttk.Scale(
            self.gui_properties_frame, from_=2, to=50,
            command=self.dimensions_changed
        )
        self.gui_dimension_height_label = tkinter.Label(
            self.gui_properties_frame, anchor=tkinter.W
        )
        self.gui_dimension_height_slider = tkinter.ttk.Scale(
            self.gui_properties_frame, from_=2, to=50,
            command=self.dimensions_changed
        )
        self.gui_monster_wait_label = tkinter.Label(
            self.gui_properties_frame, anchor=tkinter.W
        )
        self.gui_monster_wait_slider = tkinter.ttk.Scale(
            self.gui_properties_frame, from_=0, to=60,
            command=self.monster_time_change
        )

        self.gui_undo_button = tkinter.Button(
            self.gui_operation_frame, text="Undo",
            command=self.perform_undo, state=tkinter.DISABLED
        )
        self.gui_undo_button.grid(
            column=0, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_open_button = tkinter.Button(
            self.gui_operation_frame, text="Open", command=self.open_file
        )
        self.gui_open_button.grid(
            column=1, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_save_button = tkinter.Button(
            self.gui_operation_frame, text="Save",
            command=lambda: self.save_file(self.current_path)
        )
        self.gui_save_button.grid(
            column=2, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_save_as_button = tkinter.Button(
            self.gui_operation_frame, text="Save As",
            command=self.save_file
        )
        self.gui_save_as_button.grid(
            column=3, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_level_select = tkinter.Listbox(
            self.gui_operation_frame
        )
        self.gui_level_select.bind(
            '<<ListboxSelect>>', self.selected_level_changed
        )
        self.gui_level_select.grid(
            column=0, row=1, columnspan=4, padx=2, pady=2, sticky='NSEW'
        )
        self.gui_operation_frame.grid_rowconfigure(1, weight=1)

        self.gui_level_add = tkinter.Button(
            self.gui_operation_frame, text="Create", command=self.new_level
        )
        self.gui_level_add.grid(column=0, row=2, padx=2, pady=2, sticky='NSEW')

        self.gui_level_delete = tkinter.Button(
            self.gui_operation_frame, text="Delete", command=self.delete_level
        )
        self.gui_level_delete.grid(
            column=1, row=2, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_level_move_up = tkinter.Button(
            self.gui_operation_frame, text="↑",
            command=lambda: self.move_level(-1, True)
        )
        self.gui_level_move_up.grid(
            column=2, row=2, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_level_move_down = tkinter.Button(
            self.gui_operation_frame, text="↓",
            command=lambda: self.move_level(1, True)
        )
        self.gui_level_move_down.grid(
            column=3, row=2, padx=2, pady=2, sticky='NSEW'
        )

        # Ensure applicable columns are the same width
        for i in range(4):
            self.gui_operation_frame.grid_columnconfigure(
                i, uniform="true", weight=1
            )

        self.window.mainloop()

    def open_file(self) -> None:
        """
        Prompt the user to select a JSON file then load it, overwriting the
        data currently loaded.
        """
        if self.unsaved_changes and not tkinter.messagebox.askyesno(
                "Unsaved changes", "You currently have unsaved changes, "
                + "are you sure you wish to load a file? "
                + "This will overwrite everything here."):
            return
        filepath = tkinter.filedialog.askopenfilename(
            filetypes=[("JSON files", '*.json')]
        )
        if filepath == "":
            return
        if not os.path.isfile(filepath):
            tkinter.messagebox.showerror("Not found", "File does not exist")
            return
        try:
            self.levels = maze_levels.load_level_json(filepath)
            self.current_path = filepath
            self.window.wm_title(f"Level Designer - {filepath}")
            self.current_level = -1
            self.current_tile = (-1, -1)
            self.undo_stack = []
            self.gui_undo_button.config(state=tkinter.DISABLED)
            self.unsaved_changes = False
            self.update_level_list()
            self.update_map_canvas()
            self.update_properties_frame()
        except Exception as e:
            tkinter.messagebox.showerror(
                "Error",
                "An error occurred loading the file.\n"
                + "Is it definitely a valid levels file?\n\n"
                + f"The following info was given: {repr(e)}"
            )
            return

    def save_file(self, filepath: str = None) -> None:
        """
        Prompt the user to provide a location to save a JSON file then do so.
        If filepath is given, the user file prompt will be skipped.
        """
        if filepath is None or filepath == "":
            filepath = tkinter.filedialog.asksaveasfilename(
                filetypes=[("JSON files", '*.json')]
            )
        if filepath == "":
            return
        try:
            maze_levels.save_level_json(filepath, self.levels)
            self.window.wm_title(f"Level Designer - {filepath}")
            self.current_path = filepath
            self.unsaved_changes = False
        except Exception as e:
            tkinter.messagebox.showerror(
                "Error",
                "An error occurred saving the file.\n"
                + f"The following info was given: {repr(e)}"
            )
            return

    def update_map_canvas(self) -> None:
        """
        Draw the current level to the map canvas.
        """
        self.gui_map_canvas.delete(tkinter.ALL)
        if self.current_level < 0:
            return
        current_level = self.levels[self.current_level]
        tile_width = self._cfg.viewport_width // current_level.dimensions[0]
        tile_height = self._cfg.viewport_height // current_level.dimensions[1]
        tile_to_redraw: Optional[Tuple[int, int, int, int, str]] = None
        for y, row in enumerate(current_level.wall_map):
            for x, point in enumerate(row):
                if (x, y) in current_level.original_exit_keys:
                    colour = screen_drawing.GOLD
                elif (x, y) in current_level.original_key_sensors:
                    colour = screen_drawing.DARK_GOLD
                elif (x, y) in current_level.original_guns:
                    colour = screen_drawing.GREY
                elif current_level.monster_start == (x, y):
                    colour = screen_drawing.DARK_RED
                elif current_level.start_point == (x, y):
                    colour = screen_drawing.RED
                elif current_level.end_point == (x, y):
                    colour = screen_drawing.GREEN
                else:
                    colour = (
                        screen_drawing.BLACK
                        if point is not None else
                        screen_drawing.WHITE
                    )
                if self.current_tile == (x, y):
                    tile_to_redraw = (
                        tile_width * x + 2, tile_height * y + 2,
                        tile_width * (x + 1) + 2, tile_height * (y + 1) + 2,
                        rgb_to_hex(*colour)
                    )
                else:
                    self.gui_map_canvas.create_rectangle(
                        tile_width * x + 2, tile_height * y + 2,
                        tile_width * (x + 1) + 2, tile_height * (y + 1) + 2,
                        fill=rgb_to_hex(*colour)
                    )
        # Redraw the selected tile to keep the entire outline on top.
        if tile_to_redraw is not None:
            self.gui_map_canvas.create_rectangle(
                *tile_to_redraw[:4], fill=tile_to_redraw[4],
                outline=rgb_to_hex(*screen_drawing.RED)
            )

    def update_level_list(self) -> None:
        """
        Update level ListBox with the current state of all the levels.
        """
        self.gui_level_select.delete(0, tkinter.END)
        for index, level in enumerate(self.levels):
            self.gui_level_select.insert(
                tkinter.END, f"Level {index + 1} - "
                + f"{level.dimensions[0]}x{level.dimensions[1]}"
            )
        if 0 <= self.current_level < len(self.levels):
            self.gui_level_select.selection_set(self.current_level)

    def update_properties_frame(self) -> None:
        """
        Update the properties frame with information about the selected tile.
        Also updates the width and height sliders.
        """
        if self.current_level < 0:
            if self.gui_dimension_width_slider.winfo_ismapped():
                self.gui_dimension_width_label.forget()
                self.gui_dimension_width_slider.forget()
                self.gui_dimension_height_label.forget()
                self.gui_dimension_height_slider.forget()
            if self.gui_monster_wait_slider.winfo_ismapped():
                self.gui_monster_wait_label.forget()
                self.gui_monster_wait_slider.forget()
            return
        if not self.gui_dimension_width_slider.winfo_ismapped():
            self.gui_dimension_width_label.pack(padx=2, pady=2, fill="x")
            self.gui_dimension_width_slider.pack(padx=2, pady=2, fill="x")
            self.gui_dimension_height_label.pack(padx=2, pady=2, fill="x")
            self.gui_dimension_height_slider.pack(padx=2, pady=2, fill="x")
        current_level = self.levels[self.current_level]
        self.do_slider_update = False
        self.gui_dimension_width_label.config(
            text=f"Level width - ({current_level.dimensions[0]})"
        )
        self.gui_dimension_width_slider.set(current_level.dimensions[0])
        self.gui_dimension_height_label.config(
            text=f"Level height - ({current_level.dimensions[1]})"
        )
        self.gui_dimension_height_slider.set(current_level.dimensions[1])
        self.do_slider_update = True
        if self.gui_monster_wait_slider.winfo_ismapped():
            self.gui_monster_wait_label.forget()
            self.gui_monster_wait_slider.forget()
        if -1 in self.current_tile:
            self.gui_selected_square_description.config(
                bg="#f0f0f0", fg="black", text="Nothing is currently selected"
            )
        elif self.current_tile in current_level.original_exit_keys:
            self.gui_selected_square_description.config(
                text=self.descriptions[KEY],
                bg=rgb_to_hex(*screen_drawing.GOLD), fg="black"
            )
        elif self.current_tile in current_level.original_key_sensors:
            self.gui_selected_square_description.config(
                text=self.descriptions[SENSOR],
                bg=rgb_to_hex(*screen_drawing.DARK_GOLD), fg="white"
            )
        elif self.current_tile in current_level.original_guns:
            self.gui_selected_square_description.config(
                text=self.descriptions[GUN],
                bg=rgb_to_hex(*screen_drawing.GREY), fg="black"
            )
        elif current_level.monster_start == self.current_tile:
            self.gui_selected_square_description.config(
                text=self.descriptions[MONSTER],
                bg=rgb_to_hex(*screen_drawing.DARK_RED), fg="white"
            )
            self.gui_monster_wait_label.pack(padx=2, pady=2, fill="x")
            self.gui_monster_wait_slider.pack(padx=2, pady=2, fill="x")
            if current_level.monster_wait is not None:
                self.do_slider_update = False
                self.gui_monster_wait_label.config(
                    text="Monster spawn time - "
                    + f"({round(current_level.monster_wait)})"
                )
                self.gui_monster_wait_slider.set(
                    current_level.monster_wait // 5
                )
                self.do_slider_update = True
        elif current_level.start_point == self.current_tile:
            self.gui_selected_square_description.config(
                text=self.descriptions[START],
                bg=rgb_to_hex(*screen_drawing.RED), fg="white"
            )
        elif current_level.end_point == self.current_tile:
            self.gui_selected_square_description.config(
                text=self.descriptions[END],
                bg=rgb_to_hex(*screen_drawing.GREEN), fg="black"
            )
        else:
            if current_level[self.current_tile] is not None:
                self.gui_selected_square_description.config(
                    text=self.descriptions[WALL],
                    bg=rgb_to_hex(*screen_drawing.BLACK), fg="white"
                )
            else:
                self.gui_selected_square_description.config(
                    text=self.descriptions[SELECT],
                    bg=rgb_to_hex(*screen_drawing.WHITE), fg="black"
                )

    def select_tool(self, new_tool: int) -> None:
        """
        Change the currently selected tool and update buttons to match.
        """
        if 0 <= new_tool < len(self.tool_buttons):
            self.tool_buttons[self.current_tool].config(state=tkinter.ACTIVE)
            self.current_tool = new_tool
            self.tool_buttons[self.current_tool].config(state=tkinter.DISABLED)

    def add_to_undo(self) -> None:
        """
        Add the state of all the current levels to the undo stack.
        """
        self.undo_stack.append(
            (self.current_level, copy.deepcopy(self.levels))
        )
        self.gui_undo_button.config(state=tkinter.ACTIVE)

    def perform_undo(self) -> None:
        """
        Revert the current level to its state before the most recent non-undone
        action.
        """
        if len(self.undo_stack) > 0:
            self.current_level, self.levels = self.undo_stack.pop(-1)
            self.update_level_list()
            self.update_map_canvas()
            self.update_properties_frame()
        if len(self.undo_stack) == 0:
            self.gui_undo_button.config(state=tkinter.DISABLED)

    def selected_level_changed(self, _: tkinter.Event) -> None:
        """
        Called when the selection in the level ListBox is changed.
        """
        self.add_to_undo()
        selection = self.gui_level_select.curselection()
        self.current_level = selection[0] if len(selection) > 0 else -1
        self.current_tile = (-1, -1)
        self.update_map_canvas()
        self.update_properties_frame()

    def on_map_canvas_click(self, event: tkinter.Event) -> None:
        """
        Called when the map canvas is clicked by the user. Handles the event
        based on the currently selected tool.
        """
        if self.current_level < 0:
            return
        current_level = self.levels[self.current_level]
        tile_width = self._cfg.viewport_width // current_level.dimensions[0]
        tile_height = self._cfg.viewport_height // current_level.dimensions[1]
        clicked_tile = (
            (event.x - 2) // tile_width, (event.y - 2) // tile_height
        )
        if not current_level.is_coord_in_bounds(clicked_tile):
            return
        if self.current_tool == SELECT:
            self.current_tile = clicked_tile
        elif self.current_tool == WALL:
            if not is_tile_free(current_level, clicked_tile):
                return
            self.add_to_undo()
            current_level[clicked_tile] = (
                None
                if isinstance(current_level[clicked_tile], tuple) else
                (current_level.edge_wall_texture_name,) * 4
            )
            self.unsaved_changes = True
        elif self.current_tool == START:
            if current_level[clicked_tile] or not is_tile_free(
                    current_level, clicked_tile):
                return
            self.add_to_undo()
            current_level.start_point = clicked_tile
            self.unsaved_changes = True
        elif self.current_tool == END:
            if current_level[clicked_tile] or not is_tile_free(
                    current_level, clicked_tile):
                return
            self.add_to_undo()
            current_level.end_point = clicked_tile
            self.unsaved_changes = True
        elif self.current_tool == KEY:
            if clicked_tile in current_level.original_exit_keys:
                self.add_to_undo()
                current_level.original_exit_keys = (
                    current_level.original_exit_keys - {clicked_tile}
                )
            else:
                if current_level[clicked_tile] or not is_tile_free(
                        current_level, clicked_tile):
                    return
                self.add_to_undo()
                current_level.original_exit_keys = (
                        current_level.original_exit_keys | {clicked_tile}
                )
            self.unsaved_changes = True
        elif self.current_tool == SENSOR:
            if clicked_tile in current_level.original_key_sensors:
                self.add_to_undo()
                current_level.original_key_sensors = (
                        current_level.original_key_sensors - {clicked_tile}
                )
            else:
                if current_level[clicked_tile] or not is_tile_free(
                        current_level, clicked_tile):
                    return
                self.add_to_undo()
                current_level.original_key_sensors = (
                        current_level.original_key_sensors | {clicked_tile}
                )
            self.unsaved_changes = True
        elif self.current_tool == GUN:
            if clicked_tile in current_level.original_guns:
                self.add_to_undo()
                current_level.original_guns = (
                        current_level.original_guns - {clicked_tile}
                )
            else:
                if current_level[clicked_tile] or not is_tile_free(
                        current_level, clicked_tile):
                    return
                self.add_to_undo()
                current_level.original_guns = (
                        current_level.original_guns | {clicked_tile}
                )
            self.unsaved_changes = True
        elif self.current_tool == MONSTER:
            if clicked_tile == current_level.monster_start:
                self.add_to_undo()
                current_level.monster_start = None
                current_level.monster_wait = None
            else:
                if current_level[clicked_tile] or not is_tile_free(
                        current_level, clicked_tile):
                    return
                self.add_to_undo()
                current_level.monster_start = clicked_tile
                if current_level.monster_wait is None:
                    current_level.monster_wait = 10.0
        self.update_map_canvas()
        self.update_properties_frame()

    def dimensions_changed(self, _: str) -> None:
        """
        Called when the user updates the dimensions of the level.
        """
        if self.current_level < 0 or not self.do_slider_update:
            return
        new_dimensions = (
            round(self.gui_dimension_width_slider.get()),
            round(self.gui_dimension_height_slider.get())
        )
        current_level = self.levels[self.current_level]
        if new_dimensions == current_level.dimensions:
            return
        self.add_to_undo()
        current_level.dimensions = new_dimensions
        # Remove excess rows
        current_level.wall_map = (
            current_level.wall_map[:current_level.dimensions[1]]
        )
        # Pad new rows with empty space
        for __ in range(
                current_level.dimensions[1] - len(current_level.wall_map)):
            current_level.wall_map.append([None] * current_level.dimensions[0])
        for index, row in enumerate(current_level.wall_map):
            # Remove excess columns
            current_level.wall_map[index] = row[:current_level.dimensions[0]]
            # Pad new columns with empty space
            for __ in range(current_level.dimensions[0] - len(row)):
                current_level.wall_map[index].append(None)
        if not current_level.is_coord_in_bounds(self.current_tile):
            self.current_tile = (-1, -1)
        self.update_properties_frame()
        self.update_level_list()
        self.update_map_canvas()

    def monster_time_change(self, new_time: str) -> None:
        """
        Called when the user updates the monster spawn delay. Due to how
        tkinter scales work, new_time is given as a string.
        """
        if self.current_level < 0 or not self.do_slider_update:
            return
        rounded_time = round(float(new_time)) * 5
        current_level = self.levels[self.current_level]
        if rounded_time == current_level.monster_wait:
            return
        self.add_to_undo()
        current_level.monster_wait = rounded_time
        self.update_properties_frame()

    def new_level(self) -> None:
        """
        Create an empty level after the currently selected level.
        """
        self.add_to_undo()
        self.levels.insert(self.current_level + 1, Level(
            (10, 10), [[None] * 10 for _ in range(10)], (0, 0), (1, 0), set(),
            set(), set(), None, None, next(iter(self.textures))  # First key
        ))
        self.unsaved_changes = True
        self.update_level_list()
        self.update_map_canvas()
        self.update_properties_frame()

    def delete_level(self) -> None:
        """
        Prompt the user then delete the currently selected level.
        """
        if self.current_level < 0:
            return
        if not tkinter.messagebox.askyesno(
                "Delete level", "Are you sure you want to delete this level? "
                + "While it may be temporarily possible to undo, "
                + "it should not be depended upon!"):
            return
        self.add_to_undo()
        self.levels.pop(self.current_level)
        self.current_level = -1
        self.unsaved_changes = True
        self.update_level_list()
        self.update_map_canvas()
        self.update_properties_frame()

    def move_level(self, index: int, relative: bool) -> None:
        """
        Move the currently selected level to a new index. Silently fails if
        that index is invalid. If relative is True, the target index will be
        relative to the currently selected one.
        """
        if relative:
            target = self.current_level + index
        else:
            target = index
        if target < 0 or target >= len(self.levels):
            return
        self.add_to_undo()
        self.levels.insert(target, self.levels.pop(self.current_level))
        self.current_level = target
        self.update_level_list()


if __name__ == "__main__":
    LevelDesigner()
