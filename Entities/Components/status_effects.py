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
                 ):
        self.name=name
        self.magnitude=magnitude
        self.duration=duration
        self.entity=entity
        if entity:
            self.apply(self.entity)
        self.bg=bg
        self.fg=fg

    def apply(self,entity: Actor):
        self.entity=entity

    def tick(self):
        if not self.duration == -1:
            self.duration=max(self.duration-1,0)
            if self.duration==0:
                self.expire()

    def on_damaged(self, enemy: Actor,amount:int=0):
        pass

    def on_deal_damage(self, target: Actor, amount:int=0):
        pass

    def is_magical(self):
        return False

    def on_heal(self,amount):
        pass

    def expire(self):
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
                 ):
        super().__init__(name,magnitude,entity,duration,bg)

    def tick(self):
        super().tick()
        if self.duration%2==0:
            if self.entity.fighter:
                self.entity.gamemap.engine.message_log.add_message(
                    f"{self.entity_name()} takes 1 damage from unnatural cold"
                )
                self.entity.fighter.take_damage(1)

    def expire(self):
        self.entity.gamemap.engine.message_log.add_message(
            f"{self.entity_name()} takes 1 damage from unnatural cold"
        )
        self.entity.status_effects.remove(self)

class VampirismStatusEffect(StatusEffect):
    def __init__(self,
                 name: str,
                 magnitude: float,
                 entity: Optional[Actor],
                 duration: int=0,
                 bg: Tuple[int, int, int] = (125, 55, 55),
                 fg: Tuple[int, int, int] = (0, 0, 0),
                 ):
        super().__init__(name,magnitude,entity,duration,bg,fg)

    def on_deal_damage(self, target: Actor, amount:int=0):
        if not target.is_alive:
            self.entity.fighter.heal(self.magnitude)
            self.entity.gamemap.engine.message_log.add_message(
                f"{self.entity_name()} feel a rush of twisted power as you cut down the {target.name} healing you for {self.magnitude}",
                fg=color.health_recovered_effect
            )


    def expire(self):
        self.entity.status_effects.remove(self)