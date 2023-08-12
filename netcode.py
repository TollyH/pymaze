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
        if len(player_list_bytes) < 6:
            raise Exception("Invalid packet for ping. Ignoring.")
        hits_remaining = player_list_bytes[0]
        last_killer_skin = player_list_bytes[1]
        kills = int.from_bytes(player_list_bytes[2:4], "big")
        deaths = int.from_bytes(player_list_bytes[4:6], "big")
        player_byte_size = net_data.Player.byte_size
        return hits_remaining, last_killer_skin, kills, deaths, [
            net_data.Player.from_bytes(player_list_bytes[
                    i * player_byte_size + 6:(i + 1) * player_byte_size + 6
            ]) for i in range((len(player_list_bytes) - 6) // player_byte_size)
        ]
    except Exception as e:
        print(e)
        return None


def ping_server_coop(sock: socket.socket, addr: Tuple[str, int],
                     player_key: bytes, coords: Tuple[float, float],
                     ) -> Optional[Tuple[
                            bool, Optional[Tuple[int, int]],
                            List[net_data.Player], Set[Tuple[int, int]]
                          ]]:
    """
    Tell the server where we currently are, and get whether we're dead, where
    the monster is, and a list of where all other players are and what items
    they've picked up.
    Returns None if a response doesn't arrive in a timely manner.
    """
    # Positions are sent as integers with 2 d.p of accuracy from the original
    # float.
    coords_b = bytes(net_data.Coords(*coords))
    sock.sendto(server.PING.to_bytes(1, "big") + player_key + coords_b, addr)
    try:
        coords_size = net_data.Coords.byte_size
        player_list_bytes = sock.recvfrom(16384)[0]
        if len(player_list_bytes) < coords_size + 2:
            raise Exception("Invalid packet for ping. Ignoring.")
        killed = bool(player_list_bytes[0])
        monster_coords: Optional[Tuple[int, int]] = net_data.Coords.from_bytes(
            player_list_bytes[1:coords_size + 1]
        ).to_int_tuple()
        if monster_coords == (-1, -1):
            monster_coords = None
        player_size = net_data.Player.byte_size
        player_count = player_list_bytes[coords_size + 1]
        offset_1 = coords_size + 2
        offset_2 = player_size * player_count + offset_1
        return killed, monster_coords, [
            net_data.Player.from_bytes(player_list_bytes[
                    i * player_size + offset_1:(i + 1) * player_size + offset_1
            ]) for i in range(player_count)
        ], {
            net_data.Coords.from_bytes(player_list_bytes[
                    i * coords_size + offset_2:(i + 1) * coords_size + offset_2
            ]).to_int_tuple() for i in range(
                (len(player_list_bytes) - offset_2) // coords_size
            )
        }
    except Exception as e:
        print(e)
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
        + bytes.ljust(name.encode('ascii', 'ignore')[:24], 24, b'\x00'), addr
    )
    try:
        received_bytes = sock.recvfrom(34)[0]
        return (
            received_bytes[:32], received_bytes[32], bool(received_bytes[33])
        )
    except Exception as e:
        print(e)
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
        received_bytes = sock.recvfrom(1)[0]
        if len(received_bytes) != 1:
            raise Exception("Invalid packet for gunfire. Ignoring.")
        return received_bytes[0]
    except Exception as e:
        print(e)
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


def admin_ping(sock: socket.socket, addr: Tuple[str, int], admin_key: bytes
               ) -> Optional[Tuple[
                        int, bool, List[net_data.PrivatePlayer], List[bytes]
                    ]]:
    """
    Get the current level, co-op status, list of players, and list of player
    keys from the server.
    Requires a server's admin key, a regular player key will not work.
    """
    sock.sendto(server.ADMIN_PING.to_bytes(1, "big") + admin_key, addr)
    try:
        received_bytes = sock.recvfrom(16384)[0]
        if len(received_bytes) < 2:
            raise Exception("Invalid packet for admin ping. Ignoring.")
        player_size = net_data.PrivatePlayer.byte_size
        player_and_key_size = player_size + 32
        players = [
            net_data.PrivatePlayer.from_bytes(received_bytes[
                i * player_and_key_size + 2:(i + 1) * player_and_key_size + 2
            ]) for i in range((len(received_bytes) - 2) // player_and_key_size)
        ]
        player_keys = [
            received_bytes[
                i * player_and_key_size + player_size + 2:
                (i + 1) * player_and_key_size + 2
            ] for i in range((len(received_bytes) - 2) // player_and_key_size)
        ]
        return received_bytes[0], bool(received_bytes[1]), players, player_keys
    except Exception as e:
        print(e)
        return None


def admin_kick(sock: socket.socket, addr: Tuple[str, int], admin_key: bytes,
               player_key: bytes) -> None:
    """
    Removes a player from the server with the given player key.
    Also requires a server's admin key, a regular player key will not work.
    """
    sock.sendto(
        server.ADMIN_KICK.to_bytes(1, "big") + admin_key + player_key, addr
    )


def admin_ban_ip(sock: socket.socket, addr: Tuple[str, int], admin_key: bytes,
                 ip_addr: str) -> None:
    """
    Forbid a given IP address from interacting with the server.
    Requires a server's admin key, a regular player key will not work.
    IMPORTANT: If you ban your own IP, you will not be able to interact
    yourself until the server restarts! Bans are not permanent, they will reset
    if the server process is restarted.
    """
    sock.sendto(
        server.ADMIN_BAN_IP.to_bytes(1, "big") + admin_key + ip_addr.encode(),
        addr
    )


def admin_reset(sock: socket.socket, addr: Tuple[str, int], admin_key: bytes,
                new_level: int, coop: bool) -> None:
    """
    Reset the server, setting a new level and setting either coop or deathmatch
    mode.
    Requires a server's admin key, a regular player key will not work.
    WARNING: This will kick all players from the server!
    """
    sock.sendto(
        server.ADMIN_RESET.to_bytes(1, "big") + admin_key
        + new_level.to_bytes(1, "big") + coop.to_bytes(1, "big"), addr
    )


def admin_unban_ip(sock: socket.socket, addr: Tuple[str, int],
                   admin_key: bytes, ip_addr: str) -> None:
    """
    Remove a given IP address from the server's ban list.
    Requires a server's admin key, a regular player key will not work.
    """
    sock.sendto(
        server.ADMIN_UNBAN_IP.to_bytes(1, "big") + admin_key
        + ip_addr.encode(), addr
    )
