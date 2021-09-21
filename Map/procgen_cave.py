#!/usr/bin/env python3
from __future__ import annotations
from typing import Any, TYPE_CHECKING, List
from skimage.morphology import flood_fill
import numpy as np
import time
import scipy.signal  # type: ignore
from numpy.typing import NDArray
import random

from Entities import entity_factories
from Map import tile_types, game_map
from Map.procgen_dungeon import get_max_value_for_floor, max_monsters_by_floor, max_items_by_floor, \
    get_entities_at_random, enemy_chances, item_chances

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
        MAX_TILES = 2000
        MIN_TILES = 1400
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
        if floor_count > MIN_TILES:
            valid = False
        if floor_count > MAX_TILES:
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

    player = engine.player
    dungeon = game_map.GameMap(engine, WIDTH, HEIGHT, entities=[player])
    for x in range(0, WIDTH - 1):
        for y in range(0, HEIGHT - 1):
            num=tiles2[y, x]
            if num==0:
                num_r=random.random()
                if num_r<0.3:
                    dungeon.tiles[x,y]=tile_types.cave_floor
                elif num_r<0.6:
                    dungeon.tiles[x,y]=tile_types.cave_floor2
                else:
                    dungeon.tiles[x,y]=tile_types.cave_floor3

            if num==3:
                player.place(x,y,dungeon)
                # TODO: up stairs
                dungeon.tiles[x,y]=tile_types.floor
            if num==4:
                dungeon.tiles[x, y] = tile_types.down_stairs
                dungeon.downstairs_location = (x, y)

    for x in range(1, WIDTH - 2):
        for y in range(1, HEIGHT - 2):
            CHANCE_LIGHT = 0.015
            CHANCE_SHRUB = 0.95
            n = random.random()
            dx = x - playerx
            dy = y - playery
            distance = max(abs(dx), abs(dy))
            if get_neighbors(y, x, tiles2) == 0 and distance>10 and dungeon.tiles[x,y][0]:
                if n < CHANCE_LIGHT and not dungeon.get_blocking_entity_at_location(x, y):
                    floor_number = engine.game_world.current_floor
                    n=random.random()
                    if n<0.3:
                        entity_factories.torch.spawn(dungeon, x, y)
                        for x2 in [-1,0,1]:
                            for y2 in [-1,0,1]:
                                n=random.random()
                                if x2==0 and y2==0:
                                    pass
                                elif n<0.3:
                                    if not dungeon.get_blocking_entity_at_location(x+x2, y+y2):
                                        entity_factories.bedroll.spawn(dungeon, x+x2, y+y2)


                    elif n<0.6:
                        entity_factories.table.spawn(dungeon, x, y)
                        for x2 in [-1,0,1]:
                            for y2 in [-1,0,1]:
                                n=random.random()
                                if x2==0 and y2==0:
                                    pass
                                elif n<0.3:
                                    if not dungeon.get_blocking_entity_at_location(x+x2, y+y2):
                                        entity_factories.chair.spawn(dungeon, x+x2, y+y2)
                                elif n<0.4:
                                    if not dungeon.get_blocking_entity_at_location(x+x2, y+y2):
                                        entity_factories.barrel.spawn(dungeon, x+x2, y+y2)
                    else:
                        entity_factories.statue.spawn(dungeon, x, y)


                    number_of_monsters = random.randint(
                        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
                    )
                    number_of_items = random.randint(
                        0, get_max_value_for_floor(max_items_by_floor, floor_number)
                    )

                    monsters: List[Entity] = get_entities_at_random(
                        enemy_chances, number_of_monsters, floor_number
                    )
                    items: List[Entity] = get_entities_at_random(
                        item_chances, number_of_items, floor_number
                    )

                    for spawn_entity in monsters + items:
                        x2 = random.randint(-1, 1)
                        y2 = random.randint(-1, 1)

                        if not any(entity.x == x + x2 and entity.y == y + y2 and entity.blocks_movement for entity in dungeon.entities):
                            spawn_entity.spawn(dungeon, x + x2, y + y2)
                elif n > CHANCE_SHRUB and not dungeon.get_blocking_entity_at_location(x, y) and dungeon.tiles[x,y][0]:
                    num_r=random.random()
                    if num_r<0.25:
                        entity_factories.cave_plant.spawn(dungeon, x, y)
                    elif num_r<0.5:
                        entity_factories.cave_plant2.spawn(dungeon, x, y)
                    elif num_r<0.75:
                        entity_factories.cave_plant4.spawn(dungeon, x, y)
                    else:
                        entity_factories.cave_plant3.spawn(dungeon, x, y)


    print("rejected maps: ", rejected, " blob size: ", floor_count)
    end = time.time()
    print("end:", end - start)
    return dungeon