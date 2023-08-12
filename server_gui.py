"""
Contains the definition for ServerGuiApp, a GUI for managing running PyMaze
server instances.
"""
import base64
import os
import tkinter
from typing import List, Optional, Tuple

import net_data
import netcode


class ServerGuiApp:
    """
    A Tkinter GUI providing management tools for PyMaze multiplayer server
    instances. Can be used remotely.
    """
    def __init__(self, root: tkinter.Tk) -> None:
        # Change working directory to the directory where the script is located
        # This prevents issues with required files not being found.
        os.chdir(os.path.dirname(__file__))

        self.sock = netcode.create_client_socket()
        self.current_server: Optional[Tuple[str, int]] = None
        self.current_key: Optional[bytes] = None
        self.connected = False

        self.current_level = 0
        self.coop = False
        self.players: List[net_data.PrivatePlayer] = []

        self.window = tkinter.Toplevel(root)
        self.window.wm_title("Server Management GUI - Not Connected")
        self.window.wm_iconbitmap(
            os.path.join("window_icons", "server_gui_discon.ico")
        )

        self.gui_map_frame = tkinter.Frame(self.window)
        self.gui_map_frame.pack(
            side=tkinter.LEFT, fill=tkinter.Y, padx=5, pady=5
        )
        self.gui_operation_frame = tkinter.Frame(self.window)
        self.gui_operation_frame.pack(
            side=tkinter.LEFT, fill=tkinter.BOTH, expand=True, padx=5, pady=5
        )

        self.gui_map_canvas = tkinter.Canvas(
            self.gui_map_frame, width=500, height=500
        )
        self.gui_map_canvas.pack(side=tkinter.LEFT)

        self.gui_server_input = tkinter.Entry(self.gui_operation_frame)
        self.gui_server_input.insert(0, "address:port")
        self.gui_server_input.grid(
            column=0, columnspan=3, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_connect_button = tkinter.Button(
            self.gui_operation_frame, text="Connect",
            command=self.change_server_details
        )
        self.gui_connect_button.grid(
            column=3, row=0, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_key_input = tkinter.Entry(self.gui_operation_frame)
        self.gui_key_input.insert(0, "Server key")
        self.gui_key_input.grid(
            column=0, columnspan=4, row=1, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_player_select = tkinter.Listbox(
            self.gui_operation_frame, exportselection=False
        )
        self.gui_player_select.grid(
            column=0, row=2, columnspan=4, padx=2, pady=2, sticky='NSEW'
        )
        self.gui_operation_frame.grid_rowconfigure(1, weight=1)

        self.gui_ban_ip_input = tkinter.Entry(self.gui_operation_frame)
        self.gui_ban_ip_input.insert(0, "IP to ban")
        self.gui_ban_ip_input.grid(
            column=0, columnspan=2, row=3, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_connect_button = tkinter.Button(
            self.gui_operation_frame, text="Ban IP"
        )
        self.gui_connect_button.grid(
            column=2, row=3, padx=2, pady=2, sticky='NSEW'
        )

        self.gui_player_kick = tkinter.Button(
            self.gui_operation_frame, text="Kick"
        )
        self.gui_player_kick.grid(
            column=3, row=3, padx=2, pady=2, sticky='NSEW'
        )

        # Ensure applicable columns are the same width
        for i in range(4):
            self.gui_operation_frame.grid_columnconfigure(
                i, uniform="true", weight=1
            )
        self.gui_operation_frame.grid_rowconfigure(
            0, uniform="true", weight=1
        )
        self.gui_operation_frame.grid_rowconfigure(
            1, uniform="true", weight=1
        )
        self.gui_operation_frame.grid_rowconfigure(
            2, weight=100
        )
        self.gui_operation_frame.grid_rowconfigure(
            3, uniform="true", weight=1
        )

        self.ping_update()
        self.window.wait_window()

    def change_connected_status(self, new_status: bool) -> None:
        """
        Update whether the GUI is currently in an established connection
        with the multiplayer server. Will change the window icon, for example.
        """
        if new_status == self.connected:
            return
        if new_status:
            self.connected = True
            self.window.wm_iconbitmap(
                os.path.join("window_icons", "server_gui_con.ico")
            )
            self.window.wm_title("Server Management GUI - Connected")
        else:
            self.connected = False
            self.window.wm_iconbitmap(
                os.path.join("window_icons", "server_gui_discon.ico")
            )
            self.window.wm_title("Server Management GUI - Not Connected")

    def ping_update(self) -> None:
        """
        Sends a ping request to the current server, updating the GUI with new
        information.
        """
        try:
            if self.current_server is None or self.current_key is None:
                self.change_connected_status(False)
                return
            retries = 0
            ping_response = netcode.admin_ping(
                self.sock, self.current_server, self.current_key
            )
            # If currently marked as connected and over 10 consecutive pings
            # fail, mark as disconnected. If already marked as disconnected,
            # looping isn't required, and we should just wait for the next
            # scheduled ping.
            while retries < 10 and self.connected:
                ping_response = netcode.admin_ping(
                    self.sock, self.current_server, self.current_key
                )
                if ping_response is None:
                    retries += 1
                else:
                    break
            if ping_response is None:
                self.change_connected_status(False)
            else:
                self.change_connected_status(True)
                self.current_level, self.coop, self.players = ping_response
        finally:
            # Run this method again after 100ms if connected, 1000ms otherwise
            self.window.after(
                100 if self.connected else 1000, self.ping_update
            )

    def change_server_details(self) -> None:
        """
        Change the details of the server to connect to.
        """
        try:
            self.current_server = netcode.get_host_port(
                self.gui_server_input.get().strip()
            )
            self.current_key = base64.b64decode(
                self.gui_key_input.get().strip()
            )
        except Exception as e:
            print(e)
            self.current_server = None
            self.current_key = None


if __name__ == "__main__":
    _root = tkinter.Tk()
    _root.withdraw()
    ServerGuiApp(_root)
