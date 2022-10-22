"""
Receives and gives multiplayer packets to all connected players,
"""
import logging
import os
import socket
import sys
from glob import glob
from typing import Any, Dict

import maze_levels
import net_data
import raycasting

# Request types
PING = b'\x00'
JOIN = b'\x01'
FIRE = b'\x02'
RESPAWN = b'\x03'
CHECK_DEAD = b'\x04'
LEAVE = b'\x05'

SHOTS_UNTIL_DEAD = 10

LOG = logging.getLogger("pymaze.server")
LOG.setLevel(logging.INFO)


def maze_server(*, level_json_path: str = "maze_levels.json",
                port: int = 13375, level: int = 0) -> None:
    """
    Launches the server required for playing multiplayer games. Stores and
    provides player locations, health status, and custom walls, and does
    collision checking for gun fires.
    """
    # Change working directory to the directory where the script is located.
    # This prevents issues with required files not being found.
    os.chdir(os.path.dirname(__file__))
    levels = maze_levels.load_level_json(level_json_path)
    skin_count = len(glob(os.path.join("textures", "player", "*.png")))
    current_level = levels[level]
    players: Dict[bytes, net_data.PrivatePlayer] = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    sock.bind(('0.0.0.0', port))
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            rq_type = data[0]
            player_key = data[1:33]
            if player_key not in players and rq_type != JOIN:
                LOG.warning("Invalid player key from %s", addr)
            if rq_type == PING:
                LOG.debug("Player pinged from %s", addr)
                players[player_key].pos = net_data.Coords.from_bytes(
                    data[33:41]
                )
                players[player_key].grid_pos = (
                    players[player_key].pos.x_pos.__trunc__(),
                    players[player_key].pos.y_pos.__trunc__()
                )
                player_bytes = len(players).to_bytes(1, "big")
                for key, plr in players.items():
                    if key != player_key:
                        player_bytes += bytes(plr.strip_private_data())
                sock.sendto(player_bytes, addr)
            elif rq_type == JOIN:
                LOG.info("Player join from %s", addr)
                if len(players) < 255:
                    new_key = os.urandom(32)
                    players[new_key] = net_data.PrivatePlayer(
                        net_data.Coords(
                            current_level.start_point[0] + 0.5,
                            current_level.start_point[1] + 0.5
                        ),
                        current_level.start_point,
                        len(players) % skin_count, SHOTS_UNTIL_DEAD
                    )
                    sock.sendto(new_key, addr)
                else:
                    LOG.warning(
                        "Rejected player join from %s as server is full", addr
                    )
            elif rq_type == FIRE:
                LOG.debug("Player fired gun from %s", addr)
                coords = net_data.Coords.from_bytes(data[33:41])
                facing = net_data.Coords.from_bytes(data[41:49])
                # Set these just for the raycasting function to work
                current_level.player_coords = coords.to_tuple()
                current_level.player_grid_coords = (
                    coords.x_pos.__trunc__(), coords.y_pos.__trunc__()
                )
                list_players = list(players.values())
                _, hit_sprites = raycasting.get_first_collision(
                    current_level, facing.to_tuple(), False,
                    list_players
                )
                for sprite in hit_sprites:
                    if sprite.type == raycasting.OTHER_PLAYER:
                        # Player was hit by gun
                        assert sprite.player_index is not None
                        list_players[sprite.player_index].hits_remaining -= 1
                        break
            elif rq_type == RESPAWN:
                LOG.debug("Player respawned from %s", addr)
                if players[player_key].hits_remaining <= 0:
                    players[player_key].hits_remaining = SHOTS_UNTIL_DEAD
                    players[player_key].pos = net_data.Coords(
                        *current_level.start_point
                    )
                else:
                    LOG.warning(
                        "Will not respawn from %s as player isn't dead", addr
                    )
            elif rq_type == CHECK_DEAD:
                LOG.debug("Player checked health from %s", addr)
                sock.sendto(
                    players[player_key].hits_remaining.to_bytes(1, "big"), addr
                )
            elif rq_type == LEAVE:
                LOG.info("Player left from %s", addr)
                del players[player_key]
            else:
                LOG.warning("Invalid request type from %s", addr)
        except Exception as e:
            LOG.error(e)


if __name__ == "__main__":
    kwargs: Dict[str, Any] = {}
    for arg in sys.argv[1:]:
        arg_pair = arg.split("=")
        if len(arg_pair) == 2:
            lower_key = arg_pair[0].lower()
            if lower_key in ("--level-json-path", "-p"):
                kwargs["level_json_path"] = arg_pair[1]
                continue
            if lower_key in ("--config-ini-path", "-c"):
                kwargs["config_ini_path"] = arg_pair[1]
                continue
            if lower_key in ("--port", "-t"):
                kwargs["port"] = arg_pair[1]
                continue
            if lower_key in ("--level", "-l"):
                kwargs["level"] = arg_pair[1]
                continue
        print(f"Unknown argument or missing value: '{arg}'")
        sys.exit(1)
    maze_server(**kwargs)