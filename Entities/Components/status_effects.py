import random
from typing import Tuple, Optional

from Entities.entity import Actor
from UI import color


class StatusEffect:
    def __init__(self,
                 name: str,
                 magnitude: int,
                 entity: Optional[Actor],
                 duration: int=0,
                 bg: Tuple[int, int, int] = (155, 155, 155),
                 fg: Tuple[int, int, int] = (255, 255, 255),
                 poison: bool=False,
                 curse: bool=False,
                 magic: bool=False,
                 ):
        self.name=name
        self.magnitude=magnitude
        self.duration=duration
        self.entity=entity
        self.bg=bg
        self.fg=fg
        self.poison=poison
        self.magic=magic
        self.curse=curse
        if entity:
            self.apply(self.entity)

    def apply(self,entity: Actor):
        self.entity=entity
        self.entity.status_effects.append(self)
        if self.poison and entity.fighter.resist_poison>0:
            self.magnitude-=entity.fighter.resist_poison

        if self.curse and entity.fighter.resist_curse>0:
            self.magnitude-=entity.fighter.resist_curse

        if self.magic and entity.fighter.resist_magic>0:
            self.magnitude-=entity.fighter.resist_magic

        if self.magnitude<=0:
            self.duration=0
            self.expire(True)

    def tick(self):
        if not self.duration == -1:
            self.duration=max(self.duration-1,0)
            if self.duration==0:
                self.expire(False)

    def on_damaged(self, enemy: Actor,amount:int=0):
        pass

    def on_deal_damage(self, target: Actor, amount:int=0):
        pass

    def is_magical(self):
        return False

    def on_heal(self,amount):
        pass

    def expire(self,resisted=False):
        self.entity.status_effects.remove(self)

    def entity_name(self) -> str:
        entity_name="The "+self.entity.name
        if self.entity.name=="Player":
            entity_name="You"
        return entity_name

class FrostShockStatus(StatusEffect):
    def __init__(self,
                 name: str,
                 magnitude: float,
                 entity: Actor,
                 duration: int=0,
                 bg: Tuple[int, int, int] = (155, 155, 225),
                 magic:bool=True
                 ):
        super().__init__(name,magnitude,entity,duration,bg=bg,magic=magic)

    def tick(self):
        super().tick()
        if self.duration%2==0:
            if self.entity.fighter:
                self.entity.gamemap.engine.message_log.add_message(
                    f"{self.entity_name()} takes {self.magnitude} damage from unnatural cold",color.status_effect_applied
                )
                self.entity.fighter.take_damage(self.magnitude)

    def expire(self,resisted=False):
        super().expire(resisted)
        if resisted:
            self.entity.gamemap.engine.message_log.add_message(
                f"{self.entity_name()} resists the magical cold",color.status_effect_applied
            )
        else:
            self.entity.gamemap.engine.message_log.add_message(
                f"{self.entity_name()} shakes off the unnatural cold",color.status_effect_applied
            )

class AntivenomImmunityEffect(StatusEffect):
    def __init__(self,
                 name: str,
                 magnitude: float,
                 entity: Actor,
                 duration: int=0,
                 bg: Tuple[int, int, int] = (55, 125, 55),
                 fg: Tuple[int, int, int] = (155, 225, 155),
                 ):
        super().__init__(name,magnitude,entity,duration,bg=bg,fg=fg)

    def apply(self,entity: Actor):
        super().apply(entity)
        self.entity.fighter.poison_resist_base+=self.magnitude

    def expire(self,resisted=False):
        super().expire(resisted)
        self.entity.fighter.poison_resist_base-=self.magnitude

class VampirismStatusEffect(StatusEffect):
    def __init__(self,
                 name: str,
                 magnitude: float,
                 entity: Optional[Actor],
                 duration: int=0,
                 bg: Tuple[int, int, int] = (125, 55, 55),
                 fg: Tuple[int, int, int] = (0, 0, 0),
                 curse:bool=True
                 ):
        super().__init__(name,magnitude,entity,duration,bg=bg,fg=fg,curse=True)

    def on_deal_damage(self, target: Actor, amount:int=0):
        if not target.is_alive:
            self.entity.fighter.heal(self.magnitude)
            self.entity.gamemap.engine.message_log.add_message(
                f"{self.entity_name()} feel a rush of twisted power as you cut down the {target.name} healing you for {self.magnitude}",
                fg=color.health_recovered_effect
            )


class MawSiphonStatus(StatusEffect):
    def __init__(self,
                 name: str,
                 magnitude: float,
                 entity: Actor,
                 duration: int=0,
                 bg: Tuple[int, int, int] = (155, 0, 125),
                 fg: Tuple[int, int, int] = (0, 0, 0),
                 poison:bool=True
                 ):
        super().__init__(name,magnitude,entity,duration,bg=bg,fg=fg,poison=poison)

    def tick(self):
        super().tick()
        if self.duration%2==0 and self.duration>0:
            if self.entity.fighter:
                self.entity.gamemap.engine.message_log.add_message(
                    f"{self.magnitude} lifeforce is sucked out of {self.entity_name()} and into the maw",
                    color.status_effect_applied
                )
                self.entity.fighter.take_damage(self.magnitude)
                for actor in self.entity.gamemap.actors:
                    if (actor.name=="Mawrat" and self.entity.gamemap.visible[actor.x,actor.y] and actor.is_alive) or (actor.name=="Mawbeast" and self.entity.gamemap.visible[actor.x,actor.y] and actor.is_alive):

                        n=random.random()

                        if n<0.3:
                            self.entity.gamemap.engine.message_log.add_message(
                                f"The {actor.name} draws lifeforce from the maw... ({self.magnitude*4}hp gained)",
                                color.enemy_atk
                            )
                            actor.fighter.max_hp_base+=self.magnitude*2
                            actor.fighter.heal(self.magnitude*2)
                        elif n<0.6:
                            self.entity.gamemap.engine.message_log.add_message(
                                f"The {actor.name}'s defence is empowered by the maw... (+{self.magnitude} def)!",
                                color.enemy_atk
                            )
                            actor.fighter.base_defense+=self.magnitude
                        else:
                            self.entity.gamemap.engine.message_log.add_message(
                                f"The {actor.name}'s attacks are empowered by the maw... (+{self.magnitude} pow)!",
                                color.enemy_atk
                            )
                            actor.fighter.base_power+=self.magnitude


    def expire(self,resisted=False):
        super().expire(resisted)
        if resisted:
            self.entity.gamemap.engine.message_log.add_message(
                f"{self.entity_name()} resisted the maw-venom",color.status_effect_applied
            )
        else:
            self.entity.gamemap.engine.message_log.add_message(
                f"The maw-venom leaves {self.entity_name()}",color.status_effect_applied
            )