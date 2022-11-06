"""
Receives and gives multiplayer packets to all connected players.
"""
import logging
import os
import socket
import sys
import time
from glob import glob
from typing import Any, Dict

import maze_levels
import net_data
import raycasting

# Request types
PING = 0
JOIN = 1
FIRE = 2
RESPAWN = 3
LEAVE = 4

# Shot responses
SHOT_DENIED = 0
SHOT_MISSED = 1
SHOT_HIT_NO_KILL = 2
SHOT_KILLED = 3

SHOTS_UNTIL_DEAD = 10
SHOT_TIMEOUT = 0.3  # Seconds
MONSTER_MOVEMENT_WAIT = 0.5

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("pymaze.server")


def maze_server(*, level_json_path: str = "maze_levels.json",
                port: int = 13375, level: int = 0, coop: bool = False) -> None:
    """
    Launches the server required for playing multiplayer games. Stores and
    provides player locations, health status, and does collision checking
    for gun fires.
    """
    # Change working directory to the directory where the script is located.
    # This prevents issues with required files not being found.
    os.chdir(os.path.dirname(__file__))
    levels = maze_levels.load_level_json(level_json_path)
    skin_count = len(glob(os.path.join("textures", "player", "*.png")))
    current_level = levels[level]
    if coop:
        # Monster starts immediately in co-op matches
        current_level.move_monster(True)
    last_monster_move = time.time()
    players: Dict[bytes, net_data.PrivatePlayer] = {}
    last_fire_time: Dict[bytes, float] = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    LOG.info("Listening on UDP port %s", port)
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            rq_type = data[0]
            player_key = data[1:33]
            if player_key not in players and rq_type != JOIN:
                LOG.warning("Invalid player key from %s", addr)
            if rq_type == PING:
                LOG.debug("Player pinged from %s", addr)
                if time.time() - last_monster_move >= MONSTER_MOVEMENT_WAIT:
                    last_monster_move = time.time()
                    current_level.move_monster(True)
                    for plr in players.values():
                        if plr.grid_pos == current_level.monster_coords:
                            plr.hits_remaining = 0
                if players[player_key].hits_remaining > 0:
                    players[player_key].pos = net_data.Coords.from_bytes(
                        data[33:41]
                    )
                    players[player_key].grid_pos = (
                        players[player_key].pos.x_pos.__trunc__(),
                        players[player_key].pos.y_pos.__trunc__()
                    )
                if not coop:
                    player_bytes = (
                        players[player_key].hits_remaining.to_bytes(1, "big")
                        + players[player_key].last_killer_skin.to_bytes(
                            1, "big"
                        )
                        + players[player_key].kills.to_bytes(2, "big")
                        + players[player_key].deaths.to_bytes(2, "big")
                    )
                else:
                    grid_pos = players[player_key].grid_pos
                    current_level.exit_keys.discard(grid_pos)
                    current_level.key_sensors.discard(grid_pos)
                    current_level.guns.discard(grid_pos)
                    if current_level.monster_coords is None:
                        monster_coords = (-1, -1)
                    else:
                        monster_coords = current_level.monster_coords
                    player_bytes = (
                        (not bool(
                            players[player_key].hits_remaining
                        )).to_bytes(1, "big") + bytes(
                            net_data.Coords(*monster_coords)
                        ) + (len(players) - 1).to_bytes(1, "big")
                    )
                for key, plr in players.items():
                    if key != player_key:
                        player_bytes += bytes(plr.strip_private_data())
                if coop:
                    for item in (current_level.exit_keys
                                 | current_level.key_sensors
                                 | current_level.guns):
                        player_bytes += bytes(net_data.Coords(*item))
                sock.sendto(player_bytes, addr)
            elif rq_type == JOIN:
                LOG.info("Player join from %s", addr)
                if len(players) < 255:
                    name = data[33:57].strip(b"\x00").decode("ascii", "ignore")
                    new_key = os.urandom(32)
                    players[new_key] = net_data.PrivatePlayer(
                        name, net_data.Coords(-1, -1), (-1, -1),
                        len(players) % skin_count, 0, 0,
                        1 if coop else SHOTS_UNTIL_DEAD
                    )
                    sock.sendto(
                        new_key + level.to_bytes(1, "big")
                        + coop.to_bytes(1, "big"), addr
                    )
                else:
                    LOG.warning(
                        "Rejected player join from %s as server is full", addr
                    )
            elif rq_type == FIRE:
                LOG.debug("Player fired gun from %s", addr)
                now = time.time()
                if (now - last_fire_time.get(player_key, 0) < SHOT_TIMEOUT
                        and not coop):
                    LOG.warning(
                        "Will not allow %s to shoot, firing too quickly", addr
                    )
                    sock.sendto(SHOT_DENIED.to_bytes(1, "big"), addr)
                else:
                    last_fire_time[player_key] = now
                    coords = net_data.Coords.from_bytes(data[33:41])
                    facing = net_data.Coords.from_bytes(data[41:49])
                    # Set these just for the raycasting function to work
                    current_level.player_coords = coords.to_tuple()
                    current_level.player_grid_coords = (
                        coords.x_pos.__trunc__(), coords.y_pos.__trunc__()
                    )
                    list_players = [] if coop else [
                        (k, x) for k, x in players.items()
                        if x.hits_remaining > 0 and k != player_key
                    ]
                    _, hit_sprites = raycasting.get_first_collision(
                        current_level, facing.to_tuple(), False,
                        [x[1] for x in list_players]
                    )
                    hit = False
                    for sprite in hit_sprites:
                        if sprite.type == raycasting.OTHER_PLAYER and not coop:
                            # Player was hit by gun
                            assert sprite.player_index is not None
                            hit_key, hit_player = list_players[
                                sprite.player_index
                            ]
                            if hit_player.hits_remaining > 0:
                                hit = True
                                hit_player.hits_remaining -= 1
                                if hit_player.hits_remaining <= 0:
                                    hit_player.last_killer_skin = players[
                                        player_key
                                    ].skin
                                    hit_player.deaths += 1
                                    players[player_key].kills += 1
                                    # Hide dead players in level
                                    hit_player.pos = net_data.Coords(-1, -1)
                                    sock.sendto(
                                        SHOT_KILLED.to_bytes(1, "big"), addr
                                    )
                                else:
                                    sock.sendto(
                                        SHOT_HIT_NO_KILL.to_bytes(1, "big"),
                                        addr
                                    )
                            break
                        elif sprite.type == raycasting.MONSTER and coop:
                            # Monster was hit by gun
                            hit = True
                            current_level.monster_coords = None
                            sock.sendto(SHOT_KILLED.to_bytes(1, "big"), addr)
                            break
                    if not hit:
                        sock.sendto(SHOT_MISSED.to_bytes(1, "big"), addr)
            elif rq_type == RESPAWN:
                LOG.debug("Player respawned from %s", addr)
                if players[player_key].hits_remaining <= 0:
                    players[player_key].hits_remaining = SHOTS_UNTIL_DEAD
                else:
                    LOG.warning(
                        "Will not respawn from %s as player isn't dead", addr
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
        if len(arg_pair) == 1:
            lower_key = arg_pair[0].lower()
            if lower_key in ("--coop", "-o"):
                kwargs["coop"] = True
                continue
        elif len(arg_pair) == 2:
            lower_key = arg_pair[0].lower()
            if lower_key in ("--level-json-path", "-p"):
                kwargs["level_json_path"] = arg_pair[1]
                continue
            if lower_key in ("--config-ini-path", "-c"):
                kwargs["config_ini_path"] = arg_pair[1]
                continue
            if lower_key in ("--port", "-t"):
                kwargs["port"] = int(arg_pair[1])
                continue
            if lower_key in ("--level", "-l"):
                kwargs["level"] = int(arg_pair[1])
                continue
        print(f"Unknown argument or missing value: '{arg}'")
        sys.exit(1)
    maze_server(**kwargs)
