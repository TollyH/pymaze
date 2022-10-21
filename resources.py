"""
Contains most of the resources used by the game, including textures and sound
effects.
"""
import os
from glob import glob
from typing import Any, Dict, List, Tuple, Union

import pygame

import raycasting
import screen_drawing
from maze_game import TEXTURE_WIDTH, TEXTURE_HEIGHT, EmptySound


# Change working directory to the directory where the script is located.
# This prevents issues with required files not being found.
os.chdir(os.path.dirname(__file__))

# Prevent discard variable from triggering type checkers
_: Any

try:
    placeholder_texture = pygame.image.load(
        os.path.join("textures", "placeholder.png")
    ).convert_alpha()
except FileNotFoundError:
    placeholder_texture = pygame.Surface((TEXTURE_WIDTH, TEXTURE_HEIGHT))

# Used to create the darker versions of each texture
_darkener = pygame.Surface((TEXTURE_WIDTH, TEXTURE_HEIGHT))
_darkener.fill(screen_drawing.BLACK)
_darkener.set_alpha(127)
# {texture_name: (light_texture, dark_texture)}
wall_textures: Dict[str, Tuple[pygame.Surface, pygame.Surface]] = {
    os.path.split(x)[-1].split(".")[0]:
        (pygame.image.load(x).convert(), pygame.image.load(x).convert())
    for x in glob(os.path.join("textures", "wall", "*.png"))
}
wall_textures["placeholder"] = (
    placeholder_texture, placeholder_texture.copy()
)
for _, (_, _surface_to_dark) in wall_textures.items():
    _surface_to_dark.blit(_darkener, (0, 0))

# {texture_name: texture}
decoration_textures: Dict[str, pygame.Surface] = {
    os.path.split(x)[-1].split(".")[0]:
        pygame.image.load(x).convert_alpha()
    for x in glob(
        os.path.join("textures", "sprite", "decoration", "*.png"))
}
decoration_textures["placeholder"] = placeholder_texture

# {degradation_stage: (light_texture, dark_texture)}
player_wall_textures: Dict[int, Tuple[pygame.Surface, pygame.Surface]] = {
    # Parse player wall texture surfaces to integer
    int(os.path.split(x)[-1].split(".")[0]):
        (pygame.image.load(x).convert(), pygame.image.load(x).convert())
    for x in glob(os.path.join("textures", "player_wall", "*.png"))
}
if len(player_wall_textures) == 0:
    player_wall_textures[0] = (
        placeholder_texture, placeholder_texture.copy()
    )
for _, (_, _surface_to_dark) in player_wall_textures.items():
    _surface_to_dark.blit(_darkener, (0, 0))

try:
    sky_texture = pygame.image.load(
        os.path.join("textures", "sky.png")
    ).convert_alpha()
except FileNotFoundError:
    sky_texture = placeholder_texture

# {raycasting.CONSTANT_VALUE: sprite_texture}
sprite_textures = {
    getattr(raycasting, os.path.split(x)[-1].split(".")[0].upper()):
        pygame.image.load(x).convert_alpha()
    for x in glob(os.path.join("textures", "sprite", "*.png"))
}

blank_icon = pygame.Surface((32, 32))
# {screen_drawing.CONSTANT_VALUE: icon_texture}
hud_icons = {
    getattr(screen_drawing, os.path.split(x)[-1].split(".")[0].upper()):
        pygame.transform.scale(
            pygame.image.load(x).convert_alpha(), (32, 32)
        )
    for x in glob(os.path.join('textures', 'hud_icons', '*.png'))
}

try:
    first_person_gun = pygame.transform.scale(
        pygame.image.load(
            os.path.join('textures', 'gun_fp.png')
        ).convert_alpha(),
        (TEXTURE_WIDTH, TEXTURE_HEIGHT)
    )
except FileNotFoundError:
    first_person_gun = pygame.Surface(
        (TEXTURE_WIDTH, TEXTURE_HEIGHT)
    )

try:
    jumpscare_monster_texture = pygame.transform.scale(
        pygame.image.load(
            os.path.join("textures", "death_monster.png")
        ).convert_alpha(),
        (TEXTURE_WIDTH, TEXTURE_HEIGHT)
    )
except FileNotFoundError:
    jumpscare_monster_texture = pygame.transform.scale(
        placeholder_texture,
        (TEXTURE_WIDTH, TEXTURE_HEIGHT)
    )

audio_error_occurred = False
try:
    monster_jumpscare_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(
        os.path.join("sounds", "monster_jumpscare.wav")
    )
    monster_spotted_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(
        os.path.join("sounds", "monster_spotted.wav")
    )
    # {min_distance_to_play: Sound}
    # Must be in ascending numerical order.
    breathing_sounds: Dict[int, Union[
        pygame.mixer.Sound, EmptySound
    ]] = {
        0: pygame.mixer.Sound(
            os.path.join("sounds", "player_breathe", "heavy.wav")
        ),
        5: pygame.mixer.Sound(
            os.path.join("sounds", "player_breathe", "medium.wav")
        ),
        10: pygame.mixer.Sound(
            os.path.join("sounds", "player_breathe", "light.wav")
        )
    }
    if len(breathing_sounds) == 0:
        raise FileNotFoundError("No breathing sounds found")
    footstep_sounds: List[Union[
        pygame.mixer.Sound, EmptySound
    ]] = [
        pygame.mixer.Sound(x)
        for x in glob(os.path.join("sounds", "footsteps", "*.wav"))
    ]
    if len(footstep_sounds) == 0:
        raise FileNotFoundError("No footstep sounds found")
    monster_roam_sounds: List[Union[
        pygame.mixer.Sound, EmptySound
    ]] = [
        pygame.mixer.Sound(x)
        for x in glob(os.path.join("sounds", "monster_roam", "*.wav"))
    ]
    if len(monster_roam_sounds) == 0:
        raise FileNotFoundError("No monster roam sounds found")
    key_pickup_sounds: List[Union[
        pygame.mixer.Sound, EmptySound
    ]] = [
        pygame.mixer.Sound(x)
        for x in glob(os.path.join("sounds", "key_pickup", "*.wav"))
    ]
    key_sensor_pickup_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "sensor_pickup.wav"))
    gun_pickup_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "gun_pickup.wav"))
    if len(key_pickup_sounds) == 0:
        raise FileNotFoundError("No key pickup sounds found")
    flag_place_sounds: List[Union[
        pygame.mixer.Sound, EmptySound
    ]] = [
        pygame.mixer.Sound(x)
        for x in glob(os.path.join("sounds", "flag_place", "*.wav"))
    ]
    if len(flag_place_sounds) == 0:
        raise FileNotFoundError("No flag place sounds found")
    wall_place_sounds: List[Union[
        pygame.mixer.Sound, EmptySound
    ]] = [
        pygame.mixer.Sound(x)
        for x in glob(os.path.join("sounds", "wall_place", "*.wav"))
    ]
    if len(wall_place_sounds) == 0:
        raise FileNotFoundError("No wall place sounds found")
    compass_open_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "compass_open.wav"))
    compass_close_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "compass_close.wav"))
    map_open_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "map_open.wav"))
    map_close_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "map_close.wav"))
    gunshot_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(os.path.join("sounds", "gunshot.wav"))
    # Constant ambient sound — loops infinitely
    pygame.mixer.music.load(os.path.join("sounds", "ambience.wav"))
    light_flicker_sound: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(
        os.path.join("sounds", "light_flicker.wav")
    )
    # Used for the victory scene animations
    victory_increment: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(
        os.path.join("sounds", "victory_increment.wav")
    )
    victory_next_block: Union[
        pygame.mixer.Sound, EmptySound
    ] = pygame.mixer.Sound(
        os.path.join("sounds", "victory_next_block.wav")
    )
except (FileNotFoundError, pygame.error):
    audio_error_occurred = True
    empty_sound = EmptySound()
    monster_jumpscare_sound = empty_sound
    monster_spotted_sound = empty_sound
    breathing_sounds = {0: empty_sound}
    footstep_sounds = [empty_sound]
    monster_roam_sounds = [empty_sound]
    key_pickup_sounds = [empty_sound]
    key_sensor_pickup_sound = empty_sound
    gun_pickup_sound = empty_sound
    flag_place_sounds = [empty_sound]
    wall_place_sounds = [empty_sound]
    compass_open_sound = empty_sound
    compass_close_sound = empty_sound
    map_open_sound = empty_sound
    map_close_sound = empty_sound
    gunshot_sound = empty_sound
    light_flicker_sound = empty_sound
    victory_increment = empty_sound
    victory_next_block = empty_sound
