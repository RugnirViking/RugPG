#!/usr/bin/env python3
from __future__ import annotations
from typing import Any, TYPE_CHECKING
from skimage.morphology import flood_fill
import numpy as np
import time
import scipy.signal  # type: ignore
from numpy.typing import NDArray
import random

from Map import tile_types, game_map

if TYPE_CHECKING:
    from engine import Engine
    from Entities.entity import Entity
    from Map.game_map import GameMap

def convolve(tiles: NDArray[Any], wall_rule: int = 5) -> NDArray[np.bool_]:
    """Return the next step of the cave generation algorithm.

    `tiles` is the input array. (0: wall, 1: floor)

    If the 3x3 area around a tile (including itself) has `wall_rule` number of
    walls then the tile will become a wall.
    """
    # Use convolve2d, the 2nd input is a 3x3 ones array.
    neighbors: NDArray[Any] = scipy.signal.convolve2d(tiles == 0, [[1, 1, 1], [1, 1, 1], [1, 1, 1]], "same")

    next_tiles: NDArray[np.bool_] = neighbors < wall_rule  # Apply the wall rule.
    return next_tiles

def get_neighbors(
        x: int,
        y: int,
        dungeon,
):
    neighbors = 0
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if dungeon[x + i, y + j]:
                neighbors = neighbors + 1

    return neighbors


def generate_cave2(
        map_width: int,
        map_height: int,
        engine: Engine,
) -> game_map.GameMap:
    start = time.time()
    floor_count = 0
    rejected = 0
    valid = True

    while valid:
        WIDTH, HEIGHT = map_width, map_height
        INITIAL_CHANCE = 0.45  # Initial wall chance.
        CONVOLVE_STEPS = 4
        # 0: wall, 1: floor
        tiles: NDArray[np.bool_] = np.random.random((HEIGHT, WIDTH)) > INITIAL_CHANCE
        for _ in range(CONVOLVE_STEPS):
            tiles = convolve(tiles)
            tiles[[0, -1], :] = 0  # Ensure surrounding wall.
            tiles[:, [0, -1]] = 0

        n = 1
        # show(tiles)

        tiles2 = np.full((HEIGHT, WIDTH), fill_value=1, order="F")
        for x in range(0, WIDTH - 1):
            for y in range(0, HEIGHT - 1):
                if tiles[y, x]:
                    tiles2[y, x] = 0
        n = 2
        for x in range(1, WIDTH - 2):
            for y in range(1, HEIGHT - 2):
                if not tiles2[y, x]:
                    tiles2 = flood_fill(tiles2, (y, x), n)
                    n = n + 1
        # show(tiles)
        # show2(tiles2)
        a, b = np.unique(tiles2.flat, return_counts=True)
        a = np.delete(a, 0)
        b = np.delete(b, 0)
        # print(a)
        biggest_blob_index = b.argmax()
        biggest_blob_size = b[biggest_blob_index]
        floor_count = biggest_blob_size
        biggest_blob_num = b.argmax() + 2
        # print(biggest_blob_size)
        # print(b.argmax()+2)
        for x in range(1, WIDTH - 1):
            for y in range(1, HEIGHT - 1):
                if not tiles2[y, x] == 1:
                    if not tiles2[y, x] == biggest_blob_num:
                        tiles2[y, x] = 1
        # show2(tiles2)
        tiles = tiles2 == biggest_blob_num
        rejected = rejected + 1
        if floor_count > 1600:
            valid = False
        if floor_count > 1800:
            valid = True

    rejected = rejected - 1

    tiles2 = np.full((HEIGHT, WIDTH), fill_value=1, order="F")
    for x in range(0, WIDTH - 1):
        for y in range(0, HEIGHT - 1):
            if tiles[y, x]:
                tiles2[y, x] = 0
    valid = False
    playerx = 0
    playery = 0
    while not valid:
        playerx = random.randrange(1, WIDTH - 1)
        playery = random.randrange(1, HEIGHT - 1)
        num = get_neighbors(playery, playerx, tiles2)

        valid = num == 0
    tiles2[playery, playerx] = 3
    distance = 0
    stairsx = 0
    stairsy = 0
    valid = False
    while not valid:
        stairsx = random.randrange(1, WIDTH - 1)
        stairsy = random.randrange(1, HEIGHT - 1)
        num = get_neighbors(stairsy, stairsx, tiles2)
        dx = stairsx - playerx
        dy = stairsy - playery
        valid = num == 0
        if valid:
            distance = max(abs(dx), abs(dy))
            valid = distance > 10
    tiles2[stairsy, stairsx] = 4

    for x in range(0, WIDTH - 1):
        for y in range(0, HEIGHT - 1):
            CHANCE_LIGHT=0.4
            x=random.random()


    player = engine.player
    dungeon = game_map.GameMap(engine, WIDTH, HEIGHT, entities=[player])
    for x in range(0, WIDTH - 1):
        for y in range(0, HEIGHT - 1):
            num=tiles2[y, x]
            if num==0:
                dungeon.tiles[x,y]=tile_types.floor
            if num==3:
                player.place(x,y,dungeon)
                dungeon.tiles[x,y]=tile_types.floor
            if num==4:
                dungeon.tiles[x, y] = tile_types.down_stairs
                dungeon.downstairs_location = (x, y)

    print("rejected maps: ", rejected, " blob size: ", floor_count)
    end = time.time()
    print("end:", end - start)
    return dungeon