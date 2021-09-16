from __future__ import annotations

import random

from Entities.Components.ai import FearedEnemy
from Entities.Components.base_component import BaseComponent
from UI import color
from Entities.render_order import RenderOrder

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from Entities.entity import Actor


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int,will_chance: float=1.0):
        self.max_hp = hp
        self._hp = hp
        self.base_defense = base_defense
        self.base_power = base_power
        self.will_chance=will_chance

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def die(self) -> None:
        print("ded")
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die


        self.parent.char = "%"
        self.parent.color = (191, 0, 0)
        self.parent.blocks_movement = False
        self.parent.ai = None
        self.parent.name = f"remains of {self.parent.name}"
        self.parent.render_order = RenderOrder.CORPSE

        self.engine.message_log.add_message(death_message, death_message_color)
        self.engine.player.level.add_xp(self.parent.level.xp_given)
        
    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        for effect in self.parent.status_effects:
            effect.on_heal(amount_recovered)

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

    def melee_attack(self, damage, entity):
        self.take_damage(damage)

        for effect in self.parent.status_effects:
            effect.on_damaged(entity,damage)

        n=random.random()
        if self.hp<self.max_hp/3 and n>self.will_chance and self.parent.is_alive:
            self.engine.message_log.add_message(
                f"The {self.parent.name} loses its nerve in battle and runs for its life from the {entity.name}!",
                color.status_effect_applied,
            )
            self.parent.ai = FearedEnemy(
                entity=self.parent, previous_ai=self.parent.ai, turns_remaining=99, fear_source=entity,
            )