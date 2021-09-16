from __future__ import annotations

import numpy as np

from Entities import entity_factories
from Map import tile_types, game_map
import Map.tile_types
import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING
import tcod
import cProfile
import time

if TYPE_CHECKING:
    from engine import Engine
    from Entities.entity import Entity
    from Map.game_map import GameMap

max_items_by_floor = [
    (1, 1),
    (4, 2),
]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],
    1: [(entity_factories.confusion_scroll, 10)],
    2: [(entity_factories.lightning_scroll, 10), (entity_factories.fireball_scroll, 10)],
    3: [(entity_factories.fear_scroll, 10)],
    4: [(entity_factories.charm_scroll, 5), (entity_factories.fireball_scroll, 25),
        (entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],
    5: [(entity_factories.fear_scroll, 25)],
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],
    7: [(entity_factories.charm_scroll, 20)],
    8: [(entity_factories.charm_scroll, 20, (entity_factories.scale_mail, 15), (entity_factories.red_shroud, 15))],
}

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    3: [(entity_factories.troll, 15)],
    5: [(entity_factories.troll, 30)],
    6: [(entity_factories.ice_golem, 10)],
    7: [(entity_factories.troll, 60)],
    9: [(entity_factories.ice_golem, 60)],
}


def get_max_value_for_floor(
        max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
        weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
        number_of_entities: int,
        floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    @property
    def inner2(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 2, self.x2 - 1), slice(self.y1 + 2, self.y2 - 1)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
                self.x1 <= other.x2
                and self.x2 >= other.x1
                and self.y1 <= other.y2
                and self.y2 >= other.y1
        )


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int, ) -> None:
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
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            spawn_entity.spawn(dungeon, x, y)


def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
) -> game_map.GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []
    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                if not dungeon.tiles[x, y][0]:
                    dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        # Finally, append the new room to the list.
        rooms.append(new_room)

    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.downstairs_location = center_of_last_room
    return dungeon


def generate_temple(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
) -> game_map.GameMap:
    """Generate a new temple map."""
    player = engine.player
    dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []
    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                if not dungeon.tiles[x, y][0]:
                    dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        # Add some temple-themed decoration
        n = random.random()
        if n < 0.15:
            # circle of candles
            for x, y in [[-2, -1], [-1, -2], [1, -2], [2, -1], [1, 2], [2, 1], [-1, 2], [-2, 1]]:
                n2 = random.random()
                if n2 > 0.5:
                    entity_factories.candles2.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])
                else:
                    entity_factories.candles.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])

        elif n < 0.3:
            # carpet3 + statues at each corner
            dungeon.tiles[new_room.inner2] = tile_types.carpet3
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)
        elif n < 0.45:
            n = random.randrange(0, 4)
            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0 and not dungeon.get_entity_at_location(x3, y3):
                            entity_factories.statue.spawn(dungeon, x3, y3)
                    else:
                        if y3%2==0 and not dungeon.get_entity_at_location(x3, y3):
                            entity_factories.statue.spawn(dungeon, x3, y3)
        elif n < 0.6:
            # carpet1
            dungeon.tiles[new_room.inner2] = tile_types.carpet1
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)

        elif n < 0.75:
            # carpet2
            dungeon.tiles[new_room.inner2] = tile_types.carpet2
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)

        elif n < 0.9:
            # carpet pattern
            dungeon.tiles[new_room.inner2] = tile_types.wood_planks
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)
            n = random.randrange(0,4)
            if n==0:
                entity_factories.lectern.spawn(dungeon, new_room.x1 + 1, new_room.center[1])
            elif n==1:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y1 + 1)
            elif n==2:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y2 - 1)
            else:
                entity_factories.lectern.spawn(dungeon, new_room.x2 - 1, new_room.center[1])

            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)
                    else:
                        if y3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)
            pass
        else:
            # chairs and lectern
            n = random.randrange(0,4)
            if n==0:
                entity_factories.lectern.spawn(dungeon, new_room.x1 + 1, new_room.center[1])
            elif n==1:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y1 + 1)
            elif n==2:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y2 - 1)
            else:
                entity_factories.lectern.spawn(dungeon, new_room.x2 - 1, new_room.center[1])

            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)
                    else:
                        if y3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)


        # Finally, append the new room to the list.
        rooms.append(new_room)
    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.downstairs_location = center_of_last_room

    return dungeon
def generate_barracks(
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        engine: Engine,
) -> game_map.GameMap:
    """Generate a new temple map."""
    player = engine.player
    dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []
    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                if not dungeon.tiles[x, y][0]:
                    dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        # Add some temple-themed decoration
        n = random.random()
        if n < 0.15:
            # circle of candles
            for x, y in [[-2, -1], [-1, -2], [1, -2], [2, -1], [1, 2], [2, 1], [-1, 2], [-2, 1]]:
                n2 = random.random()
                if n2 > 0.5:
                    entity_factories.chair.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])
                else:
                    entity_factories.chair.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])

            for x, y in [[-1, -1], [1, -1], [1, 1], [-1, 1]]:
                if not dungeon.get_entity_at_location(x + new_room.center[0], y + new_room.center[1]):
                    entity_factories.table.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])
            for x, y in [[-1, 0], [1, 0], [0, 1], [0, -1]]:
                if not dungeon.get_entity_at_location(x + new_room.center[0], y + new_room.center[1]):
                    entity_factories.cabinet.spawn(dungeon, x + new_room.center[0], y + new_room.center[1])

            if not dungeon.get_entity_at_location(x + new_room.center[0], y + new_room.center[1]):
                entity_factories.brazier.spawn(dungeon, new_room.center[0], new_room.center[1])
        elif n < 0.3:
            # carpet3 + statues at each corner
            dungeon.tiles[new_room.inner] = tile_types.wood_planks
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.statue.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)

            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0:
                            if x3%4==0 and not dungeon.get_entity_at_location(x3, y3):
                                entity_factories.shelf.spawn(dungeon, x3, y3)
                            else:
                                entity_factories.barrel.spawn(dungeon, x3, y3)

                    else:
                        if y3%2==0:
                            if y3%4==0 and not dungeon.get_entity_at_location(x3, y3):
                                entity_factories.shelf.spawn(dungeon, x3, y3)
                            else:
                                entity_factories.barrel.spawn(dungeon, x3, y3)
        elif n < 0.45:
            n = random.randrange(0, 4)
            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%4==0:
                            entity_factories.bed.spawn(dungeon, x3, y3)
                        elif (x3+1)%4==0:
                            entity_factories.cabinet.spawn(dungeon, x3, y3)

                    else:
                        if y3%4==0:
                            entity_factories.bed.spawn(dungeon, x3, y3)
                        elif (y3+1)%4==0:
                            entity_factories.cabinet.spawn(dungeon, x3, y3)
        elif n < 0.6:
            # carpet1
            dungeon.tiles[new_room.inner] = tile_types.wood_planks
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)



        elif n < 0.75:
            dungeon.tiles[new_room.inner] = tile_types.wood_planks
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x1 + 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x1 + 1, new_room.y2 - 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y1 + 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y1 + 1)
            if not dungeon.get_entity_at_location(new_room.x2 - 1, new_room.y2 - 1) and \
                    random.random() > 0.1: entity_factories.torch.spawn(dungeon, new_room.x2 - 1, new_room.y2 - 1)

        elif n < 0.9:
            dungeon.tiles[new_room.inner] = tile_types.wood_planks

            n = random.randrange(0, 4)
            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0:
                            if y3%2==0:
                                entity_factories.bed.spawn(dungeon, x3, y3)
                            else:
                                entity_factories.cabinet.spawn(dungeon, x3, y3)

                    else:
                        if y3%2==0:
                            if x3%2==0:
                                entity_factories.bed.spawn(dungeon, x3, y3)
                            else:
                                entity_factories.cabinet.spawn(dungeon, x3, y3)
            pass
        else:
            # chairs and lectern
            n = random.randrange(0,4)
            if n==0:
                entity_factories.lectern.spawn(dungeon, new_room.x1 + 1, new_room.center[1])
            elif n==1:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y1 + 1)
            elif n==2:
                entity_factories.lectern.spawn(dungeon, new_room.center[0], new_room.y2 - 1)
            else:
                entity_factories.lectern.spawn(dungeon, new_room.x2 - 1, new_room.center[1])

            for x3 in range(new_room.x1+2,new_room.x2-1):
                for y3 in range(new_room.y1+2,new_room.y2-1):
                    if n==0 or n==3:
                        if x3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)
                    else:
                        if y3%2==0:entity_factories.chair.spawn(dungeon, x3, y3)


        # Finally, append the new room to the list.
        rooms.append(new_room)
    dungeon.tiles[center_of_last_room] = tile_types.down_stairs
    dungeon.downstairs_location = center_of_last_room

    return dungeon

def generate_cave(
        map_width: int,
        map_height: int,
        engine: Engine,
) -> game_map.GameMap:
    """Generate a new dungeon map."""
    start = time.time()
    print("hello")

    player = engine.player
    dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])

    # start with a grid of randomised floor and walls
    for x in range(1, map_width - 1):
        for y in range(1, map_height - 1):
            val = random.randrange(0, 2)
            if val == 1:
                dungeon.tiles[x, y] = tile_types.floor

    for x in range(0, 1):
        dungeon = apply_cave_automata(map_width, map_height, engine, dungeon)

    for x in range(0, 1):
        dungeon = apply_erode_automata(map_width, map_height, engine, dungeon)

    for x in range(1, map_width - 1):
        for y in range(1, map_height - 1):
            neighbors = get_neighbors(x, y, dungeon)
            if neighbors == 0:
                player.place(x, y, dungeon)
                dungeon.tiles[x - 1, y] = tile_types.down_stairs

                dungeon.downstairs_location = (x - 1, y)
                end = time.time()
                print("end:", end - start)
                return dungeon


def get_neighbors(
        x: int,
        y: int,
        dungeon: game_map.GameMap,
) -> int:
    neighbors = 0
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if i == 0 and j == 0:
                pass
            else:
                if dungeon.tiles[x + i, y + j] == tile_types.wall:
                    neighbors = neighbors + 1

    return neighbors


def apply_cave_automata(
        map_width: int,
        map_height: int,
        engine: Engine,
        dungeon: game_map.GameMap,
) -> game_map.GameMap:
    player = engine.player
    new_dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])
    # apply
    for x in range(1, map_width - 1):
        for y in range(1, map_height - 1):
            neighbors = get_neighbors(x, y, dungeon)
            if dungeon.tiles[x, y] == tile_types.wall:
                if neighbors < 3:
                    new_dungeon.tiles[x, y] = tile_types.floor
                else:
                    new_dungeon.tiles[x, y] = tile_types.wall
            else:
                if neighbors > 5:
                    new_dungeon.tiles[x, y] = tile_types.wall
                else:
                    new_dungeon.tiles[x, y] = tile_types.floor

    return new_dungeon


def apply_erode_automata(
        map_width: int,
        map_height: int,
        engine: Engine,
        dungeon: game_map.GameMap,
) -> game_map.GameMap:
    player = engine.player
    new_dungeon = game_map.GameMap(engine, map_width, map_height, entities=[player])
    # apply
    for x in range(1, map_width - 1):
        for y in range(1, map_height - 1):
            neighbors = get_neighbors(x, y, dungeon)
            if dungeon.tiles[x, y] == tile_types.wall:
                if neighbors < 5:
                    new_dungeon.tiles[x, y] = tile_types.floor
                else:
                    new_dungeon.tiles[x, y] = tile_types.wall
            else:
                if neighbors > 4:
                    new_dungeon.tiles[x, y] = tile_types.wall
                else:
                    new_dungeon.tiles[x, y] = tile_types.floor

    return new_dungeon
