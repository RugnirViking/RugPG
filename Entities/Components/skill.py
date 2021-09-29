import copy
import random
from typing import Tuple, Optional, List, TYPE_CHECKING

import tcod

import actions
from Entities.Components.ai import StunnedEnemy
from Entities.Components.fighter import Reason
from Entities.Components.status_effects import BlockStatusEffect, IntOrBool
from Entities.entity import Actor, Entity
from UI import color
import actions
import engine
from exceptions import Impossible
from input_handlers import SingleRangedAttackHandler, MainGameEventHandler

from engine import Engine

class Base_Skill():
    def __init__(self,
                 name: str,
                 cost: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List["Base_Skill"] = None,
                 action: actions.Action = None):

        if prerequisites is None:
            prerequisites=[]
        self.prerequisites = prerequisites
        self.unlocked_color = unlocked_color
        self.color = color
        self.y = y
        self.x = x
        self.char_string = char_string
        self.name = name
        self.cost = cost
        self.action = action
        self.reason=Reason.NONE
        self.level=0
    @property
    def enabled(self) -> bool:
        return self.level>0

    def unlockable(self, entity: Actor) -> bool:
        for req_skill in self.prerequisites:
            if not any(x.name == req_skill.name for x in entity.skills):
                return False
        return True



class Skill(Base_Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill]=None,
                 action: actions.Action = None,
                 entity: Optional[Actor]=None):
        super().__init__(name, cost, char_string, x, y, color, unlocked_color,prerequisites, action)
        self.max_level = max_level
        self.entity=entity
        self.active_skill=False
        self.reason=Reason.NONE

    def level_up(self,entity: Actor):
        if entity.skill_points<1:
            return False
        if not self.unlockable(entity):
            return False

        if not any(x.name == self.name for x in entity.skills):
            clone = copy.deepcopy(self)
            entity.skills.append(clone)

        for skill in entity.skills:
            if skill.name==self.name and self.unlockable(entity) and skill.level<self.max_level:
                skill.level=skill.level+1
            elif skill.name==self.name:
                return False
        return True

    def tick(self):
        raise NotImplementedError()

    def on_damaged(self, enemy: Actor,amount:int=0)->int:
        pass

    def on_deal_damage(self, target: Actor, amount:int=0):
        pass

    def on_heal(self,amount):
        pass

    def on_gain_energy(self, amount_recovered):
        pass

    def remove(self):
        raise NotImplementedError()

    def entity_name(self) -> str:
        entity_name="The "+self.entity.name
        if self.entity.name=="Player":
            entity_name="You"
        return entity_name

    def render_description(self,x,y,width,height,console: tcod.Console,engine: engine.Engine):
        n=1
        console.print(x,y,"Requirements:",fg=color.selected_skill)
        for req_skill in self.prerequisites:
            if (engine.player.skill_with_name(req_skill.name)):
                console.print(x,y+n,f" - {req_skill.name}",fg=color.requirement_yes)
            else:
                console.print(x,y+n,f" - {req_skill.name}",fg=color.requirement_no)
            n=n+1
        if n==1:
            console.print(x,y+n," - none :) - ",fg=color.requirement_yes)
            n=2
        return n

    def activate(self,engine):
        pass

    def perform(self,xy_coord):
        pass

class Skill_Mana(Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill]=None,
                 action: actions.Action = None,
                 entity: Optional[Actor]=None):
        super().__init__(name, cost, max_level, char_string, x, y, color, unlocked_color,prerequisites, action,entity)
        self.active_skill=False

    def level_up(self,entity: Actor):
        up=super().level_up(entity)
        if up:
            skill=entity.skill_with_name(self.name)
            if skill.level==1:
                entity.fighter.base_max_energy+=10
            return True
        else:
            return False

    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)
        console.print_box(x, y-1, width, height,
                          f"Passive Skill",alignment=tcod.CENTER,fg=color.passive_skill)
        if self.level==0:
            console.print_box(x,y+n,width,height,f"Tap into the magic forces that flow through the frigid air under the dread mountain (Increases max energy by 10)")

class Skill_Charge(Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill]=None,
                 action: actions.Action = None,
                 entity: Optional[Actor]=None):
        super().__init__(name, cost, max_level, char_string, x, y, color, unlocked_color,prerequisites, action,entity)
        self.active_skill=True


    def activate(self,engine):
        self.engine=engine
        if not self.engine.player.fighter.energy>=self.cost:
            self.engine.message_log.add_message(
                "You don't have enough energy to do that", color.needs_target
            )
            return
        engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            engine,
            callback=lambda xy: actions.SkillAction(self.entity, self, xy),
        )

    def perform(self,xy_coord):
        actor = self.engine.game_map.get_actor_at_location(xy_coord[0],xy_coord[1])

        if not self.engine.game_map.visible[xy_coord]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not actor:
            raise Impossible("You must select an enemy to target.")
        if actor is self.engine.player:
            raise Impossible("You can't charge at yourself, silly...")
        player_skill=self.engine.player.skill_with_name(self.name)
        spaces = 3
        stun=1
        if player_skill.level>=1:
            stun=1
        if player_skill.level>=2:
            stun=2
            spaces=3
        if player_skill.level>=3:
            spaces=4
            stun=2
        if player_skill.level>=4:
            spaces=5
            stun=3
        if player_skill.level==player_skill.max_level:
            spaces=7

        max_distance = spaces
        stun = stun
        dx = xy_coord[0] - self.engine.player.x
        dy = xy_coord[1] - self.engine.player.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance
        if distance>max_distance+1:
            raise Impossible(f"That enemy is too far away ({max_distance} range)")
        else:
            path = self.engine.player.ai.get_path_to(xy_coord[0],xy_coord[1])
            dest_x, dest_y = path.pop(distance-2)

            self.engine.message_log.add_message(
                f"You charge at the {actor.name}, knocking into it violently and stunning it for {stun} turns!", color.skill_text
            )
            actor.ai=StunnedEnemy(actor,actor.ai,stun)
            self.engine.player.fighter.energy-=self.cost
            return actions.MovementAction(
                self.engine.player, dest_x - self.engine.player.x, dest_y - self.engine.player.y,
            ).perform()



    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)
        console.print_box(x, y-1, width, height,
                          f"Active Skill",alignment=tcod.CENTER,fg=color.skill_points)
        spaces = 3
        next_spaces=3
        stun=1
        next_stun=1
        if self.level>=1:
            stun=1
            next_stun=2
        if self.level>=2:
            stun=2
            spaces=3
            next_spaces = 4
        if self.level>=3:
            spaces=4
            next_spaces = 5
            stun=2
            next_stun=3
        if self.level>=4:
            spaces=5
            next_spaces = 7
            stun=3
        if self.level==self.max_level:
            spaces=7
            next_spaces = 7
        if spaces==next_spaces and stun==next_stun:
            console.print_box(x,y+n,width,height,f"Rush {spaces} spaces towards an opponent with a burst of energy, surprising them and "
                                f"stunning them for {stun} turns")
        elif spaces==next_spaces:
            console.print_box(x,y+n,width,height,f"Rush {spaces} spaces towards an opponent with a burst of energy, surprising them and "
                                f"stunning them for {stun}({next_stun}) turns")
        elif stun==next_stun:
            console.print_box(x,y+n,width,height,f"Rush {spaces}({next_spaces}) spaces towards an opponent with a burst of energy, surprising them and "
                                f"stunning them for {stun} turns")
        else:
            console.print_box(x,y+n,width,height,f"Rush {spaces}({next_spaces}) spaces towards an opponent with a burst of energy, surprising them and "
                                f"stunning them for {stun}({next_stun}) turns")




class Skill_Block(Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill]=None,
                 action: actions.Action = None,
                 entity: Optional[Actor]=None):
        super().__init__(name, cost, max_level, char_string, x, y, color, unlocked_color,prerequisites, action,entity)
        self.active_skill=True

    def activate(self,engine):
        self.engine=engine
        player_skill=engine.player.skill_with_name(self.name)
        if engine.player.fighter.energy>=self.cost:
            engine.player.fighter.energy-=self.cost
        else:
            engine.message_log.add_message(
                "You don't have enough energy to do that", color.needs_target
            )
            return
        turns=2
        magnitude=0.25
        if player_skill.level==2:
            turns=3
            magnitude=0.35
        if player_skill.level==3:
            turns=4
            magnitude=0.45
        if player_skill.level==4:
            turns=4
            magnitude=0.55
        if player_skill.level==5:
            turns=5
            magnitude=0.75
        has_status=engine.player.status_with_name("Blocking")
        if has_status:
            has_status.duration=turns
            has_status.magnitude=magnitude
            return actions.WaitAction(engine.player)
        else:
            engine.message_log.add_message(
                "You raise your guard and focus on taking less damage", color.skill_text
            )
            BlockStatusEffect("Blocking",magnitude,engine.player,turns+1,color.block_status_bg,color.block_status_fg,False)
            return actions.WaitAction(engine.player)

    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)
        console.print_box(x, y-1, width, height,
                          f"Active Skill",alignment=tcod.CENTER,fg=color.skill_points)
        if self.level==0:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 2 turns by 25%")
        if self.level==1:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 2(3) turns by 25%(35%)")
        if self.level==2:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 3 turns by 35%(45%)")
        if self.level==3:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 3(4) turns by 45%(55%)")
        if self.level==4:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 4(5) turns by 55%(75%)")
        if self.level==5:
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 5 turns by 75%")

class Skill_Dodge(Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill]=None,
                 action: actions.Action = None,
                 entity: Optional[Actor]=None):
        super().__init__(name, cost, max_level, char_string, x, y, color, unlocked_color,prerequisites, action,entity)
        self.active_skill=False
        self.chance=0
        self.reason=Reason.DODGED

    def level_up(self,entity: Actor):
        up=super().level_up(entity)
        if up:
            skill=entity.skill_with_name(self.name)
            if skill.level==1:
                skill.chance=0.1
            if skill.level==2:
                skill.chance=0.15
            if skill.level==3:
                skill.chance=0.25
            if skill.level==4:
                skill.chance=0.3
            if skill.level==5:
                skill.chance=0.45
            return True
        else:
            return False

    def dodge(self,entity: Entity,engine: Engine) -> bool:
        tiles = [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
        random.shuffle(tiles) # check tiles in random order to dodge in random direction
        for tile in tiles:
            x=tile[0]
            y=tile[1]
            passable_tile = entity.gamemap.tiles["walkable"][entity.x+x, entity.y+y]
            no_entity_in_tile = engine.game_map.get_blocking_entity_at_location(entity.x+x, entity.y+y) is None
            print("dodgeTry",passable_tile,no_entity_in_tile,x,y,entity.x+x, entity.y+y,passable_tile and no_entity_in_tile)
            if passable_tile and no_entity_in_tile:
                entity.move(x,y)
                print("yesdodge")
                return True
        print("nododge")
        return False


    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)
        console.print_box(x, y-1, width, height,
                          f"Passive Skill",alignment=tcod.CENTER,fg=color.passive_skill)
        if self.level==0:
            console.print_box(x,y+n,width,height,f"Start to move a little quicker, allowing you to dodge incoming attacks 10% of the time")
        if self.level==1:
            console.print_box(x,y+n,width,height,f"Start to move a little quicker, allowing you to dodge incoming attacks 10%(15%) of the time")
        if self.level==2:
            console.print_box(x,y+n,width,height,f"Move quicker, allowing you to dodge incoming attacks 15%(25%) of the time")
        if self.level==3:
            console.print_box(x,y+n,width,height,f"Move much faster, allowing you to dodge incoming attacks 25%(30%) of the time")
        if self.level==4:
            console.print_box(x,y+n,width,height,f"Move with lightning speed, allowing you to dodge incoming attacks 30%(45%) of the time")
        if self.level==5:
            console.print_box(x,y+n,width,height,f"Move with legendary speed, allowing you to dodge incoming attacks 45% of the time")

    def on_damaged(self, enemy: Actor,amount:int=0)->int:
        n = random.random()
        if n<self.chance:
            return -1
        else:
            return amount

class Skill_Jump(Skill):
    def __init__(self,
                 name: str,
                 cost: int,
                 max_level: int,
                 char_string,
                 x: int,
                 y: int,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 unlocked_color: Tuple[int, int, int] = (255, 255, 255),
                 prerequisites: List[Base_Skill] = None,
                 action: actions.Action = None,
                 entity: Optional[Actor] = None):
        super().__init__(name, cost, max_level, char_string, x, y, color, unlocked_color, prerequisites, action, entity)
        self.active_skill=True
        self.distance=0

    def activate(self,engine):
        self.engine=engine
        player_skill=self.engine.player.skill_with_name(self.name)
        if self.engine.player.fighter.energy>=player_skill.cost:
            engine.message_log.add_message(
                "Select a target location.", color.needs_target
            )
        else:
            self.engine.message_log.add_message(
                "You don't have enough energy to do that", color.needs_target
            )
            return
        return SingleRangedAttackHandler(
            engine,
            callback=lambda xy: actions.SkillAction(self.entity, self, xy),
        )

    def perform(self,xy_coord):

        if not self.engine.player.fighter.energy>=self.cost:
            raise Impossible("You don't have enough energy to do that.")
        if not self.engine.game_map.visible[xy_coord]:
            raise Impossible("You cannot target an area that you cannot see.")
        if xy_coord[0] == self.engine.player.x and xy_coord[1]==self.engine.player.y:
            raise Impossible("You can't jump to the tile you are in!")
        if self.engine.game_map.get_blocking_entity_at_location(*xy_coord):
            raise Impossible("That tile is blocked")
        player_skill=self.engine.player.skill_with_name(self.name)
        self.engine.player.fighter.energy-=player_skill.cost

        max_distance = player_skill.distance
        dx = xy_coord[0] - self.engine.player.x
        dy = xy_coord[1] - self.engine.player.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance
        if distance>max_distance:
            raise Impossible(f"That tile is too far away ({max_distance} range)")
        else:
            path = self.engine.player.ai.get_path_to(xy_coord[0],xy_coord[1])
            dest_x, dest_y = path.pop(distance-1)
            self.engine.player.fighter.energy-=self.cost

            return actions.MovementAction(
                self.engine.player, dest_x - self.engine.player.x, dest_y - self.engine.player.y,
            ).perform()

    def level_up(self,entity: Actor):
        up=super().level_up(entity)
        if up:
            skill=entity.skill_with_name(self.name)
            if skill.level==1:
                skill.distance=2
            if skill.level==2:
                skill.distance=3
            if skill.level==3:
                skill.cost=4
            if skill.level==4:
                skill.cost=3
            if skill.level==5:
                skill.cost=2
                skill.distance=4
            return True
        else:
            return False

    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)

        console.print_box(x, y-1, width, height,
                          f"Active Skill",alignment=tcod.CENTER,fg=color.skill_points)
        if self.level == 0:
            console.print_box(x, y+n, width, height,
                              f"With a leap, jump to any tile up to 2 spaces away in one go. Cost {self.cost}")
        if self.level == 1:
            console.print_box(x, y+n, width, height,
                              f"With a bounding leap, jump to any tile up to 2(3) spaces away in one go. Cost {self.cost}")
        if self.level == 2:
            console.print_box(x, y+n, width, height,
                              f"With a bounding leap, jump to any tile up to 3 spaces away in one go. Cost {self.cost}({self.cost-1})")
        if self.level == 3:
            console.print_box(x, y+n, width, height,
                              f"With a nimble leap, jump to any tile up to 3 spaces away in one go. Cost {self.cost}({self.cost-1})")
        if self.level == 4:
            console.print_box(x, y+n, width, height,
                              f"With an effortless leap, jump to any tile up to 3(4) spaces away in one go. Cost {self.cost}({self.cost-1})")
        if self.level == 5:
            console.print_box(x, y+n, width, height,
                              f"With a heroic leap, jump to any tile up to 4 spaces away in one go. Cost {self.cost}!")

skill_mana = Skill_Mana(
    name="Mana",
    cost=0,
    max_level=1,
    char_string="\\|/:-@-:/|\\",
    x=10,
    y=0,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
)
skill_charge = Skill_Charge(
    name="Charge",
    cost=5,
    max_level=5,
    char_string=">T<: ↑ : @ ",
    x=10,
    y=7,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_mana],
)
skill_block = Skill_Block(
    name="Block",
    cost=5,
    max_level=5,
    char_string="┌-┐:|Θ|:\_/",
    x=5,
    y=14,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_charge],
)
skill_dodge = Skill_Dodge(
    name="Dodge",
    cost=0,
    max_level=5,
    char_string="░┌┘:┌┘░:┘░░",
    x=15,
    y=14,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_charge],
)

skill_jump = Skill_Jump(
    name="Jump",
    cost=5,
    max_level=5,
    char_string=" @ :┌ ┐:▓ ▓",
    x=10,
    y=21,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_block,skill_dodge],
)
SKILLS_LIST = [skill_mana,
               skill_charge,
               skill_block,
               skill_dodge,
               skill_jump,
               ]

VS_CONNECTORS_LIST = [(12,6),(12,7)]

FS_CONNECTORS_LIST = [(9,13),(8,14),
                      (15,21),(16,20)]

BS_CONNECTORS_LIST = [(15,13),(16,14),
                      (9,21),(8,20)]