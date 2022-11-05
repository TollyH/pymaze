"""
Manages the client-side connections to the multiplayer server, both
broadcasting and requesting packets.
"""
import socket
from typing import List, Optional, Set, Tuple

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
    sock.settimeout(0.1)
    return sock


def ping_server(sock: socket.socket, addr: Tuple[str, int], player_key: bytes,
                coords: Tuple[float, float]
                ) -> Optional[
                        Tuple[int, int, int, int, List[net_data.Player]]
                     ]:
    """
    Tell the server where we currently are, and get a list of where all other
    players are. Also gets current hits remaining until death and the skin of
    our last known killer. Returns None if a response doesn't arrive in a
    timely manner.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    sock.sendto(server.PING.to_bytes(1, "big") + player_key + coords_b, addr)
    try:
        player_list_bytes = sock.recvfrom(16384)[0]
        hits_remaining = player_list_bytes[0]
        last_killer_skin = player_list_bytes[1]
        kills = int.from_bytes(player_list_bytes[2:4], "big")
        deaths = int.from_bytes(player_list_bytes[4:6], "big")
        player_byte_size = net_data.Player.byte_size
        return hits_remaining, last_killer_skin, kills, deaths, [
            net_data.Player.from_bytes(player_list_bytes[
                    i * player_byte_size + 6:(i + 1) * player_byte_size + 6
            ]) for i in range((len(player_list_bytes) - 2) // player_byte_size)
        ]
    except (socket.timeout, OSError):
        return None


def ping_server_coop(sock: socket.socket, addr: Tuple[str, int],
                     player_key: bytes, coords: Tuple[float, float],
                     ) -> Optional[Tuple[
                            List[net_data.Player], Set[Tuple[int, int]]
                          ]]:
    """
    Tell the server where we currently are, and get a list of where all
    other players are and what items they've picked up.
    Returns None if a response doesn't arrive in a timely manner.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    sock.sendto(server.PING.to_bytes(1, "big") + player_key + coords_b, addr)
    try:
        player_list_bytes = sock.recvfrom(16384)[0]
        player_byte_size = net_data.Player.byte_size
        player_count = player_list_bytes[0]
        offset = player_byte_size * player_count + 1
        coords_size = net_data.Coords.byte_size
        return [
            net_data.Player.from_bytes(player_list_bytes[
                    i * player_byte_size + 1:(i + 1) * player_byte_size + 1
            ]) for i in range(player_count)
        ], {
            net_data.Coords.from_bytes(player_list_bytes[
                    i * coords_size + offset:(i + 1) * coords_size + offset
            ]).to_int_tuple() for i in range(
                (len(player_list_bytes) - offset) // coords_size
            )
        }
    except (socket.timeout, OSError):
        return None


def join_server(sock: socket.socket, addr: Tuple[str, int], name: str
                ) -> Optional[Tuple[bytes, int, bool]]:
    """
    Join a server at the specified address. Returns the private player key
    assigned to us by the server, the level the server is using, and whether
    the match is co-op or not.
    """
    # Player key is all 0 here as we don't have one yet, but all requests still
    # need to have one.
    sock.sendto(
        server.JOIN.to_bytes(1, "big") + b'\x00' * 32
        + bytes.rjust(name.encode('ascii', 'ignore')[:24], 24, b'\x00'), addr
    )
    try:
        received_bytes = sock.recvfrom(34)[0]
        return (
            received_bytes[:32], received_bytes[32], bool(received_bytes[33])
        )
    except (socket.timeout, OSError):
        return None


def fire_gun(sock: socket.socket, addr: Tuple[str, int], player_key: bytes,
             coords: Tuple[float, float], facing: Tuple[float, float]
             ) -> Optional[int]:
    """
    Tell the server to fire a gunshot from the specified location in the
    specified facing direction. Returns SHOT_DENIED, SHOT_MISSED,
    SHOT_HIT_NO_KILL, SHOT_KILLED, or None if server does not respond.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    facing_b = bytes(net_data.Coords(*facing))
    sock.sendto(
        server.FIRE.to_bytes(1, "big") + player_key + coords_b + facing_b, addr
    )
    try:
        return sock.recvfrom(1)[0][0]
    except (socket.timeout, OSError):
        return None


def respawn(sock: socket.socket, addr: Tuple[str, int], player_key: bytes
            ) -> None:
    """
    Tell the server to reset our hits and position. This will only work if you
    are already dead.
    """
    sock.sendto(server.RESPAWN.to_bytes(1, "big") + player_key, addr)


def leave_server(sock: socket.socket, addr: Tuple[str, int], player_key: bytes
                 ) -> None:
    """
    Tell the server we are leaving the game. Our player key will become
    immediately unusable after this.
    """
    sock.sendto(server.LEAVE.to_bytes(1, "big") + player_key, addr)
