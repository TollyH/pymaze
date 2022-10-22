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


@dataclass
class Player:
    """
    Represents publicly known information about a player: their position and
    skin.
    """
    pos: Coords
    grid_pos: Tuple[int, int]
    skin: int
    byte_size: ClassVar[int] = Coords.byte_size + 1

    def __bytes__(self) -> bytes:
        """
        Get the list of bytes ready to be transmitted over the network.
        """
        # Positions are sent as integers with 2 d.p of accuracy from the
        # original float.
        return bytes(self.pos) + self.skin.to_bytes(1, "big")

    @classmethod
    def from_bytes(cls, player_bytes: bytes) -> 'Player':
        """
        Get an instance of this class from bytes transmitted over the network.
        """
        coords = Coords.from_bytes(player_bytes[:8])
        return cls(
            coords, (coords.x_pos.__trunc__(), coords.y_pos.__trunc__()),
            int.from_bytes(player_bytes[8:9], "big")
        )


@dataclass
class PrivatePlayer(Player):
    """
    Extends Player, also containing private information known only to the
    server and the player themselves.
    """
    hits_remaining: int
    byte_size: ClassVar[int] = Player.byte_size + 1

    def __bytes__(self) -> bytes:
        """
        Get the list of bytes ready to be transmitted over the network.
        """
        return super().__bytes__() + self.hits_remaining.to_bytes(1, "big")

    @classmethod
    def from_bytes(cls, player_bytes: bytes) -> 'PrivatePlayer':
        """
        Get an instance of this class from bytes transmitted over the network.
        """
        coords = Coords.from_bytes(player_bytes[:8])
        return cls(
            coords, (coords.x_pos.__trunc__(), coords.y_pos.__trunc__()),
            int.from_bytes(player_bytes[8:9], "big"),
            int.from_bytes(player_bytes[9:10], "big")
        )

    def strip_private_data(self) -> Player:
        """
        Remove all private data from this class so that it is suitable to be
        sent to all players.
        """
        return Player(self.pos, self.grid_pos, self.skin)
