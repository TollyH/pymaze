"""
Manages the client-side connections to the multiplayer server, both
broadcasting and requesting packets.
"""
import socket
from typing import List, Tuple

import net_data
import server


def get_host_port(string: str) -> Tuple[str, int]:
    """
    Separates a string in the format 'host:port' to the host and port
    individually.
    """
    lst = string.split(':', 1)
    return lst[0], int(lst[1])


def create_client_socket() -> socket.socket:
    """
    Creates a socket for the client to use to connect to the server.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return sock


def ping_server(sock: socket.socket, addr: Tuple[str, int], player_key: bytes,
                coords: Tuple[float, float]) -> List[net_data.Player]:
    """
    Tell the server where we currently are, and get a list of where all other
    players are.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    sock.sendto(server.PING.to_bytes(1, "big") + player_key + coords_b, addr)
    player_list_bytes = sock.recvfrom(4096)[0]
    player_byte_size = net_data.Player.byte_size
    return [
        net_data.Player.from_bytes(player_list_bytes[
                i * player_byte_size + 1:(i + 1) * player_byte_size + 1
        ]) for i in range(player_list_bytes[0])
    ]


def join_server(sock: socket.socket, addr: Tuple[str, int]
                ) -> Tuple[bytes, int]:
    """
    Join a server at the specified address. Returns the private player key
    assigned to us by the server, as well as the level the server is using.
    """
    # Player key is all 0 here as we don't have one yet, but all requests still
    # need to have one.
    sock.sendto(server.JOIN.to_bytes(1, "big") + b'\x00' * 32, addr)
    received_bytes = sock.recvfrom(33)[0]
    return received_bytes[:32], received_bytes[32]


def fire_gun(sock: socket.socket, addr: Tuple[str, int], player_key: bytes,
             coords: Tuple[float, float], facing: Tuple[float, float]) -> None:
    """
    Tell the server to fire a gunshot from the specified location in the
    specified facing direction.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    facing_b = bytes(net_data.Coords(*facing))
    sock.sendto(
        server.FIRE.to_bytes(1, "big") + player_key + coords_b + facing_b, addr
    )


def respawn(sock: socket.socket, addr: Tuple[str, int], player_key: bytes
            ) -> None:
    """
    Tell the server to reset our hits and position. This will only work if you
    are already dead.
    """
    sock.sendto(server.RESPAWN.to_bytes(1, "big") + player_key, addr)


def get_status(sock: socket.socket, addr: Tuple[str, int], player_key: bytes
               ) -> int:
    """
    Gets the current hits remaining until death from the server.
    """
    sock.sendto(server.CHECK_DEAD.to_bytes(1, "big") + player_key, addr)
    return sock.recvfrom(1)[0][0]


def leave_server(sock: socket.socket, addr: Tuple[str, int], player_key: bytes
                 ) -> None:
    """
    Tell the server we are leaving the game. Our player key will become
    immediately unusable after this.
    """
    sock.sendto(server.LEAVE.to_bytes(1, "big") + player_key, addr)
