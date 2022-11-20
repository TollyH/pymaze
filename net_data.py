"""
Holds dataclasses for information to be sent and received over the network.
"""
from dataclasses import dataclass
from typing import ClassVar, Tuple


@dataclass
class Coords:
    """
    Represents a set of coordinates.
    """
    x_pos: float
    y_pos: float
    byte_size: ClassVar[int] = 8

    def __bytes__(self) -> bytes:
        """
        Get the list of bytes ready to be transmitted over the network.
        """
        # Positions are sent as integers with 2 d.p of accuracy from the
        # original float.
        return (
            int(self.x_pos * 100).to_bytes(4, "big", signed=True)
            + int(self.y_pos * 100).to_bytes(4, "big", signed=True)
        )

    @classmethod
    def from_bytes(cls, coord_bytes: bytes) -> 'Coords':
        """
        Get an instance of this class from bytes transmitted over the network.
        """
        return cls(
            int.from_bytes(coord_bytes[:4], "big", signed=True) / 100,
            int.from_bytes(coord_bytes[4:8], "big", signed=True) / 100
        )

    def to_tuple(self) -> Tuple[float, float]:
        """
        Convert Coords back to a tuple of 2 floats.
        """
        return self.x_pos, self.y_pos

    def to_int_tuple(self) -> Tuple[int, int]:
        """
        Convert Coords back to a tuple of 2 integers.
        """
        return self.x_pos.__trunc__(), self.y_pos.__trunc__()


@dataclass
class Player:
    """
    Represents publicly known information about a player: their position and
    skin.
    """
    name: str
    pos: Coords
    grid_pos: Tuple[int, int]
    skin: int
    kills: int
    deaths: int
    byte_size: ClassVar[int] = Coords.byte_size + 29

    def __bytes__(self) -> bytes:
        """
        Get the list of bytes ready to be transmitted over the network.
        """
        # Positions are sent as integers with 2 d.p of accuracy from the
        # original float.
        return (
            bytes.rjust(self.name.encode('ascii', 'ignore')[:24], 24, b'\x00')
            + bytes(self.pos)
            + self.skin.to_bytes(1, "big")
            + self.kills.to_bytes(2, "big")
            + self.deaths.to_bytes(2, "big")
        )

    @classmethod
    def from_bytes(cls, player_bytes: bytes) -> 'Player':
        """
        Get an instance of this class from bytes transmitted over the network.
        """
        name = player_bytes[:24].strip(b'\x00').decode('ascii', 'ignore')
        coords = Coords.from_bytes(player_bytes[24:32])
        return cls(
            name, coords, (coords.x_pos.__trunc__(), coords.y_pos.__trunc__()),
            int.from_bytes(player_bytes[32:33], "big"),
            int.from_bytes(player_bytes[33:35], "big"),
            int.from_bytes(player_bytes[35:37], "big")
        )


@dataclass
class PrivatePlayer(Player):
    """
    Extends Player, also containing private information known only to the
    server and the player themselves.
    """
    hits_remaining: int
    last_killer_skin: int = 0
    byte_size: ClassVar[int] = Player.byte_size + 2

    def __bytes__(self) -> bytes:
        """
        Get the list of bytes ready to be transmitted over the network.
        """
        return (
                super().__bytes__()
                + self.hits_remaining.to_bytes(1, "big")
                + self.last_killer_skin.to_bytes(1, "big")
        )

    @classmethod
    def from_bytes(cls, player_bytes: bytes) -> 'PrivatePlayer':
        """
        Get an instance of this class from bytes transmitted over the network.
        """
        name = player_bytes[:24].strip(b'\x00').decode('ascii', 'ignore')
        coords = Coords.from_bytes(player_bytes[24:32])
        return cls(
            name, coords, (coords.x_pos.__trunc__(), coords.y_pos.__trunc__()),
            int.from_bytes(player_bytes[32:33], "big"),
            int.from_bytes(player_bytes[33:35], "big"),
            int.from_bytes(player_bytes[35:37], "big"),
            int.from_bytes(player_bytes[37:38], "big"),
            int.from_bytes(player_bytes[38:39], "big")
        )

    def strip_private_data(self) -> Player:
        """
        Remove all private data from this class so that it is suitable to be
        sent to all players.
        """
        return Player(
            self.name, self.pos, self.grid_pos, self.skin, self.kills,
            self.deaths
        )
