"""
Contains the definition for ServerGuiApp, a GUI for managing running PyMaze
server instances.
"""
import os
import tkinter
from typing import Optional, Tuple

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

        self.window = tkinter.Toplevel(root)
        self.window.wm_title("Server Management GUI - Not Connected")
        self.window.wm_iconbitmap(
            os.path.join("window_icons", "server_gui_discon.ico")
        )

        self.window.wait_window()


if __name__ == "__main__":
    _root = tkinter.Tk()
    _root.withdraw()
    ServerGuiApp(_root)
