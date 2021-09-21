import copy
from typing import Tuple, Optional, List, TYPE_CHECKING

import tcod

import actions
from Entities.Components.ai import StunnedEnemy
from Entities.entity import Actor
from UI import color
import actions
import engine
from exceptions import Impossible
from input_handlers import SingleRangedAttackHandler
if TYPE_CHECKING:
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

    def level_up(self,entity: Actor):
        if not entity.skill_points>0:
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

    def on_damaged(self, enemy: Actor,amount:int=0):
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
        engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            engine,
            callback=lambda xy: actions.SkillAction(self.entity, self, xy),
        )

    def perform(self,xy_coord):
        actor = self.engine.game_map.get_actor_at_location(xy_coord[0],xy_coord[1])

        if not self.engine.player.fighter.energy>self.cost:
            raise Impossible("You don't have enough energy to do that.")
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
        if distance>max_distance:
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
            console.print_box(x,y+n,width,height,f"Focus on defence, reducing incoming damage for the next 5 turns by 45%(55%)")

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

    def render_description(self, x, y, width, height, console: tcod.Console, engine: engine.Engine):
        n=super().render_description(x,y,width,height,console,engine)
        console.print_box(x, y-1, width, height,
                          f"Passive Skill",alignment=tcod.CENTER,fg=color.passive_skill)
        if self.level==0:
            console.print_box(x,y+n,width,height,f"Start to move a little quicker, allowing you to dodge incoming attacks 10% of the time")
        if self.level==1:
            console.print_box(x,y+n,width,height,f"Start to move a little quicker, allowing you to dodge incoming attacks 10%(15%) of the time")
        if self.level==2:
            console.print_box(x,y+n,width,height,f"Move quicker, allowing you to dodge incoming attacks 15%(35%) of the time")
        if self.level==3:
            console.print_box(x,y+n,width,height,f"Move much faster, allowing you to dodge incoming attacks 25%(15%) of the time")
        if self.level==4:
            console.print_box(x,y+n,width,height,f"Move with lightning speed, allowing you to dodge incoming attacks 30%(45%) of the time")
        if self.level==5:
            console.print_box(x,y+n,width,height,f"Move with legendary speed, allowing you to dodge incoming attacks 45% of the time")


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
        engine.message_log.add_message(
            "Select a target location.", color.needs_target
        )
        return SingleRangedAttackHandler(
            engine,
            callback=lambda xy: actions.SkillAction(self.entity, self, xy),
        )

    def perform(self,xy_coord):

        if not self.engine.game_map.visible[xy_coord]:
            raise Impossible("You cannot target an area that you cannot see.")
        if xy_coord[0] == self.engine.player.x and xy_coord[1]==self.engine.player.y:
            raise Impossible("You can't jump to the tile you are in!")
        if self.engine.game_map.get_blocking_entity_at_location(*xy_coord):
            raise Impossible("That tile is blocked")
        player_skill=self.engine.player.skill_with_name(self.name)

        max_distance = player_skill.distance
        dx = xy_coord[0] - self.engine.player.x
        dy = xy_coord[1] - self.engine.player.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance
        if distance>max_distance:
            raise Impossible(f"That tile is too far away ({max_distance} range)")
        else:
            path = self.engine.player.ai.get_path_to(xy_coord[0],xy_coord[1])
            dest_x, dest_y = path.pop(distance-1)

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


skill_charge = Skill_Charge(
    name="Charge",
    cost=5,
    max_level=5,
    char_string=">T<: ↑ : @ ",
    x=10,
    y=0,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
)
skill_block = Skill_Block(
    name="Block",
    cost=5,
    max_level=5,
    char_string="┌-┐:|Θ|:\_/",
    x=5,
    y=7,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_charge],
)
skill_dodge = Skill_Dodge(
    name="Dodge",
    cost=5,
    max_level=5,
    char_string="░┌┘:┌┘░:┘░░",
    x=15,
    y=7,
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
    y=14,
    color=(100, 120, 180),
    unlocked_color=(170, 190, 250),
    prerequisites=[skill_block,skill_dodge],
)
SKILLS_LIST = [skill_charge,
               skill_block,
               skill_dodge,
               skill_jump,
               ]

FS_CONNECTORS_LIST = [(9,6),(8,7),
                      (15,14),(16,13)]

BS_CONNECTORS_LIST = [(15,6),(16,7),
                      (9,14),(8,13)]