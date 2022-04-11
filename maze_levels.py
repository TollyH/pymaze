"""
Contains the methods for loading and saving to the level JSON file.
"""
import json
from level import Level
from typing import List


def load_level_json(path: str) -> List[Level]:
    """
    Load and deserialize a level JSON file. The file must be a list of levels
    as created by the save_level_json function.
    """
    with open(path, encoding="utf8") as file:
        json_dicts = json.load(file)
    return [Level.from_json_dict(x) for x in json_dicts]


def save_level_json(path: str, levels: List[Level]) -> None:
    """
    Serialize and save a list of levels.
    """
    json_dicts = [x.to_json_dict() for x in levels]
    with open(path, 'w', encoding="utf8") as file:
        json.dump(json_dicts, file)
