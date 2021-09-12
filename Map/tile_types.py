from typing import Tuple

import numpy as np  # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
    ]
)


def new_tile(
    *,  # Enforce the use of keywords, so that parameter order doesn't matter.
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("+"), (50, 35, 75), (0, 0, 0)),
    light=(ord("+"), (150, 150, 150), (0, 0, 0)),
)
snow = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (50, 35, 75), (0, 0, 0)),
    light=(ord("."), (255, 255, 255), (140, 140, 150)),
)
snow2 = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(","), (50, 35, 75), (0, 0, 0)),
    light=(ord(","), (255, 255, 255), (150, 150, 160)),
)
snow3 = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("`"), (50, 35, 75), (0, 0, 0)),
    light=(ord("`"), (255, 255, 255), (160, 160, 170)),
)
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("="), (75, 0, 150), (37, 0, 75)),
    light=(ord("="), (255, 255, 255), (180, 180, 180)),
)
pillar = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("0"), (75, 0, 150), (37, 0, 75)),
    light=(ord("0"), (255, 255, 255), (150, 150, 150)),
)
down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (50, 50, 120)),
    light=(ord(">"), (255, 255, 255), (55, 50, 45)),
)