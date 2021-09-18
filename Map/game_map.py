
from __future__ import annotations
import numpy

import numpy as np  # type: ignore
import tcod
from tcod.console import Console
import csv
import colorsys
import random

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

from Entities import entity_factories
from Map import tile_types
from Entities.entity import Actor, Item
from Map.procgen_cave import generate_cave2
from Map.procgen_dungeon import generate_dungeon, generate_cave, generate_temple, generate_barracks

if TYPE_CHECKING:
    from engine import Engine
    from Entities.entity import Entity

def scale_lightness(rgb, scale_l):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(l, l * scale_l), s=s)


def scale_saturation(rgb, scale_s):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, l, min(s, s * scale_s))


def scale_lightness_saturation(rgb, scale_l, scale_s):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(l, l * scale_l), min(s, s * scale_s))


class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before

        self.seen = np.full(
            (self.width, self.height), fill_value=False, order="F"
        )
        self.downstairs_location = (0, 0)
        self.num = 0

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )


    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def get_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def remove_entities_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities.copy():
            if entity.x == location_x and entity.y == location_y:
                self.entities.remove(entity)

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console, playerx, playery) -> None:
        """
                Renders the map.

                If a tile is in the "visible" array, then draw it with the "light" colors.
                If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
                Otherwise, the default is "SHROUD".

                Worth remembering that this is called any time anything updates including mouse movement.
                However the seed for lighting flicker only gets reset when the bottom-right most visible
                tile's location changes (i.e the player moves)
                """
        tilestorender = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD
        )
        cost = numpy.ones((self.width, self.height), dtype=numpy.int8)
        dist = numpy.zeros((self.width, self.height), dtype=numpy.int8)
        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        """To add more light sources we can add more of the below line. For now its just the player. 
            We add a random offset to simulate flickering light"""
        for entity in entities_sorted_for_rendering:
            if entity.emits_light:
                dist[entity.x, entity.y] = -entity.light_level + random.uniform(-1.5, 1.5)

        for x in range(self.width):
            for y in range(self.height):
                cost[x, y] = 1 if self.tiles["transparent"][x][y] else 2

        """ Lighting baking """
        tcod.path.dijkstra2d(dist, cost, 2, diagonal=3)
        ## max_dist is like the intensity of the flame held by the character. Lower is brighter
        max_dist = 8
        lum = 0.5
        for j in range(tilestorender.shape[1]):
            for i in range(tilestorender.shape[0]):
                tile = tilestorender[i, j];
                if self.visible[i, j]:
                    """ For visible tiles we calculate the lighting """
                    fg_t = tile[1]
                    bg_t = tile[2]
                    distn = int(dist[i, j])

                    num = distn
                    # tile[0]=num+48
                    if distn > max_dist:
                        distn = max_dist
                    h, l, s = colorsys.rgb_to_hls(fg_t[0] / 255, fg_t[1] / 255, fg_t[2] / 255)
                    random.seed(i + j)
                    r, g, b = colorsys.hls_to_rgb(h, max(min(1, l - 1 * lum + (distn / -max_dist) * lum), 0), s)
                    if (distn > max_dist):
                        print("oh")
                    tile[1] = [r * 255, g * 255, b * 255]
                    h2, l2, s2 = colorsys.rgb_to_hls(bg_t[0] / 255, bg_t[1] / 255, bg_t[2] / 255)
                    r2, g2, b2 = colorsys.hls_to_rgb(h2, max(min(1, l2 - 1 * lum + (distn / -max_dist) * lum), 0), s2)
                    tile[2] = [r2 * 255, g2 * 255, b2 * 255]

                    # Colored lighting - red then half green for a nice orange hue
                    tile[2][0] = min(255,tile[2][0]*((distn / -16.0) * 0.4)*255.0)/8+tile[2][0]*7/8
                    tile[2][1] = min(255,tile[2][1]*((distn / -16.0) * 0.4)*255.0)/16+tile[2][1]*15/16

        console.tiles_rgb[0:self.width, 0:self.height] = tilestorender


        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, string=entity.char, fg=entity.color
                )

    def flood_reveal(self, x, y,first=False):


        for i in range(0,self.width):
            for j in range(0, self.height):
                if i>=0 and j>=0 and i<self.width and j<self.height:
                    neighboringfloor=0
                    for i2 in range(-1, 2):
                        for j2 in range(-1, 2):
                            if i+i2>-1 and j+j2>-1 and i+i2<self.width and j+j2<self.height:
                                if self.tiles[i+i2,j+j2]:
                                    if self.tiles[i+i2,j+j2][0]:
                                        neighboringfloor=neighboringfloor+1
                    if neighboringfloor>0:
                        self.visible[i, j] = True
                        self.explored[i, j] = True


class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor
        self.current_floor_type="dungeon"

    def generate_floor(self) -> None:

        self.current_floor += 1
        random.seed()
        n=random.random()

        if n<0.5:
            self.engine.game_map = generate_cave2(
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
            self.current_floor_type="cave"
        elif n<0.7:
            self.engine.game_map = generate_barracks(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
            self.current_floor_type="barracks"
        elif n<0.8:
            self.engine.game_map = generate_temple(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
            self.current_floor_type="temple"
        else:
            self.engine.game_map = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
            self.current_floor_type="dungeon"

    def load_surface(self,filename:str) -> None:
        player = self.engine.player
        dungeon = GameMap(self.engine, self.map_width, self.map_height, entities=[player])

        self.current_floor_type="special1"

        with open(filename, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            y=0
            x=0
            for row in spamreader:
                for tile in row:
                    if tile==".":
                        num=random.randrange(0,3)
                        if num==0:
                            dungeon.tiles[x, y] = tile_types.snow
                        elif num==1:
                            dungeon.tiles[x, y] = tile_types.snow2
                        else:
                            dungeon.tiles[x, y] = tile_types.snow3
                    if tile=="+":
                        dungeon.tiles[x, y] = tile_types.floor
                    if tile=="s":
                        dungeon.tiles[x, y] = tile_types.floor#spawn statue
                        entity_factories.statue.spawn(dungeon, x, y)
                    if tile=="c":
                        dungeon.tiles[x, y] = tile_types.snow#spawn snowdrift
                        entity_factories.snowdrift.spawn(dungeon, x, y)
                    if tile=="t":
                        dungeon.tiles[x, y] = tile_types.snow#spawn tree
                        entity_factories.tree.spawn(dungeon, x, y)
                    elif tile=="#":
                        dungeon.tiles[x, y] = tile_types.wall
                    elif tile=="0":
                        dungeon.tiles[x, y] = tile_types.pillar
                    elif tile==">":
                        dungeon.tiles[x, y] = tile_types.down_stairs
                        dungeon.downstairs_location = (x,y)
                    elif tile=="p":
                        dungeon.tiles[x, y] = tile_types.snow
                        player.place(*(x,y), dungeon)
                    x=x+1
                x=0
                y=y+1

        self.engine.game_map = dungeon
