"""
Contains the definition for ServerGuiApp, a GUI for managing running PyMaze
server instances.
"""
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
        else:
            self.connected = False
            self.window.wm_iconbitmap(
                os.path.join("window_icons", "server_gui_discon.ico")
            )

    def ping_update(self) -> None:
        """
        Sends a ping request to the current server, updating the GUI with new
        information.
        """
        if self.current_server is None or self.current_key is None:
            self.change_connected_status(False)
            return
        retries = 0
        ping_response = netcode.admin_ping(
            self.sock, self.current_server, self.current_key
        )
        # If currently marked as connected and over 100 consecutive pings fail,
        # mark as disconnected. If already marked as disconnected, looping
        # isn't required, and we should just wait for the next scheduled ping.
        while retries < 100 and self.connected:
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
        # Run this method again after 100ms
        self.window.after(100, self.ping_update)


if __name__ == "__main__":
    _root = tkinter.Tk()
    _root.withdraw()
    ServerGuiApp(_root)
