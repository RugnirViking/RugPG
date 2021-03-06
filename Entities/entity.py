from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union, List

from Entities.Components.rarities import Rarity
from Entities.render_order import RenderOrder
from Map import tile_types
from UI import color
from engine import Engine

if TYPE_CHECKING:
    from Components.ai import BaseAI
    from Components.consumable import Consumable
    from Components.equipment import Equipment
    from Components.equippable import Equippable
    from Components.fighter import Fighter
    from Components.inventory import Inventory
    from Components.level import Level
    from Map.game_map import GameMap
    from Entities.Components.skill import Skill
    from Entities.Components import status_effects, rarities

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    parent: Union[GameMap, Inventory]  # parent can be either the gamemap or an inventory

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
            emits_light: bool = False,
            light_level: int = 0,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        self.emits_light = emits_light
        self.trigger=False
        self.light_level=light_level

        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy

    def on_press(self,engine:Engine):
        pass

class PlateEntity(Entity):


    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
            emits_light: bool = False,
            light_level: int = 0,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=blocks_movement,
            render_order=render_order,
            emits_light=emits_light,
            light_level=light_level,
        )
        self.trigger=True

    def on_press(self,engine:Engine):
        if not self.gamemap.door_open:
            for x in range(1, self.gamemap.width - 1):
                for y in range(1, self.gamemap.height - 1):
                    if self.gamemap.tiles[x,y] == tile_types.door:
                        self.gamemap.tiles[x, y] = tile_types.door_floor
            self.gamemap.door_open=True
            text="As you step onto the plate, the great stone door opens up revealing a lavish well-lit room"
            engine.popup_message(title="Reveal",message=text,side_offset=15,textcolor=color.boss)
            engine.message_log.add_message(text=text,fg=color.boss_subtle)


class DoorShutTriggerEntity(Entity):

    def __init__(
            self,
            parent: Optional[GameMap] = None,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            blocks_movement: bool = False,
            render_order: RenderOrder = RenderOrder.CORPSE,
            emits_light: bool = False,
            light_level: int = 0,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=blocks_movement,
            render_order=render_order,
            emits_light=emits_light,
            light_level=light_level,
        )
        self.trigger = True

    def on_press(self,engine:Engine):
        if self.gamemap.door_open:
            print("door shut")
            for x in range(1, self.gamemap.width - 1):
                for y in range(1, self.gamemap.height - 1):
                    if self.gamemap.tiles[x,y] == tile_types.door_floor:
                        self.gamemap.tiles[x, y] = tile_types.door
            self.gamemap.door_open=False
            text="A beast made from enchanted ice stands up with unnatural-seeming movements from a throne opposite you. The great stone door closes behind you. There's no way back now."
            engine.popup_message(title="Trapped",message=text,side_offset=15,textcolor=color.boss)
            engine.message_log.add_message(text=text,fg=color.boss_subtle)
            engine.hasBoss=True
            engine.play_song("viking2.mp3")

class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
            emits_light: bool = False,
            light_level: int = 0,
            skills:List[Skill] = None,
            skill_points:int=0,
            is_boss:bool=False,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
            emits_light=emits_light,
            light_level=light_level,
        )
        self.is_boss=is_boss

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.equipment: Equipment = equipment
        self.equipment.parent = self

        self.fighter = fighter
        self.fighter.parent = self

        self.inventory = inventory
        self.inventory.parent = self

        self.level = level
        self.level.parent = self
        self.status_effects: List[status_effects.StatusEffect] = []
        self.skills = skills

        if not skills:
            self.skills: List[Skill] = []

        self.skill_points=skill_points

    def skill_with_name(self,skill_name):
        for skill in self.skills:
            if skill.name==skill_name:
                return skill
        return False

    def status_with_name(self,status_name):
        for status in self.status_effects:
            if status.name==status_name:
                return status
        return False

    @property
    def active_skills(self) -> List[Skill]:
        """Returns True as long as this actor can perform actions."""
        sublist = []
        for o in self.skills:
            if o.active_skill:
                sublist.append(o)
        return sublist

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

    def melee_neighbors(self):
        num=0
        for x2 in [-1,0,1]:
            for y2 in [-1,0,1]:
                if x2==0 and y2==0:
                    pass
                else:
                    actor = self.gamemap.get_actor_at_location(self.x+x2,self.y+y2)
                    if actor:
                        num=num+1

        return num




class Item(Entity):  # TODO: make this into its own file
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            color: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
            description: str="",
            rarity: Rarity=Rarity.COMMON,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )
        self.description = description
        self.rarity=rarity
        self.consumable = consumable

        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable

        if self.equippable:
            self.equippable.parent = self
