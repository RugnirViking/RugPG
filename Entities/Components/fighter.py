from __future__ import annotations

import random

from Entities.Components.ai import FearedEnemy
from Entities.Components.base_component import BaseComponent
from UI import color
from Entities.render_order import RenderOrder

from typing import TYPE_CHECKING, Tuple
from enum import auto, Enum

if TYPE_CHECKING:
    from Entities.entity import Actor


class Reason(Enum):
    NONE = auto()
    BLOCKED = auto()
    DODGED = auto()


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int,will_chance: float=1.0,base_energy: int=0,base_max_energy: int=0):
        self.base_energy = base_energy
        self.base_max_energy = base_max_energy
        self.magic_resist_base = 0
        self.curse_resist_base = 0
        self.poison_resist_base = 0
        self.max_hp_base = hp
        self._hp = hp
        self._energy = base_max_energy
        self.base_defense = base_defense
        self.base_power = base_power
        self.will_chance=will_chance
        self.tick_counter=0

    @property
    def max_hp(self) -> int:
        return self.max_hp_base + self.max_hp_bonus
    @property
    def max_energy(self) -> int:
        return self.base_max_energy + self.max_energy_bonus

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def energy(self) -> int:
        return self._energy

    @energy.setter
    def energy(self, value: int) -> None:
        self._energy = max(0, min(value, self.max_energy))

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def resist_poison(self) -> int:
        return self.poison_resist_base + self.resist_poison_bonus

    @property
    def resist_magic(self) -> int:
        return self.magic_resist_base + self.resist_magic_bonus

    @property
    def resist_curse(self) -> int:
        return self.magic_resist_base + self.resist_curse_bonus

    @property
    def max_energy_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.max_energy_bonus
        else:
            return 0
    @property
    def energy_charge_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.energy_charge_bonus
        else:
            return 0
    @property
    def resist_poison_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.resist_poison_bonus
        else:
            return 0
    @property
    def resist_magic_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.resist_magic_bonus
        else:
            return 0
    @property
    def resist_curse_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.resist_curse_bonus
        else:
            return 0
    @property
    def max_hp_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.hp_bonus
        else:
            return 0
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

        for skill in self.parent.skills:
            skill.on_heal(amount_recovered)

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        self.hp -= amount

    def melee_attack(self, damage, entity) -> Tuple[int,Reason]:
        reason=Reason.NONE
        for effect in self.parent.status_effects:
            new_damage=effect.on_damaged(entity,damage)
            if new_damage is not None:
                if new_damage>-1:
                    damage=new_damage
                    reason=effect.reason

        for skill in self.parent.skills:
            new_damage=skill.on_damaged(entity,damage)
            if new_damage:
                if new_damage>-1:
                    damage=new_damage
                else:
                    damage=0
                    reason=skill.reason

        self.take_damage(damage)

        n=random.random()
        if self.hp<self.max_hp/3 and n>self.will_chance and self.parent.is_alive:
            self.engine.message_log.add_message(
                f"The {self.parent.name} loses its nerve in battle and runs for its life from the {entity.name}!",
                color.status_effect_applied,
            )
            self.parent.ai = FearedEnemy(
                entity=self.parent, previous_ai=self.parent.ai, turns_remaining=99, fear_source=entity,
            )
        if not reason:
            reason=Reason.NONE
        return [damage,reason]

    def gain_energy(self, mana_amount):
        if self.energy == self.max_energy_bonus:
            return 0

        new_energy = self.energy + mana_amount

        if new_energy > self.max_energy_bonus:
            new_energy = self.max_energy_bonus

        amount_recovered = new_energy - self.energy

        self.energy = new_energy

        for effect in self.parent.status_effects:
            effect.on_gain_energy(amount_recovered)

        for skill in self.parent.skills:
            skill.on_gain_energy(amount_recovered)

        return amount_recovered

    def tick_energy(self):
        if self.energy<self.max_energy:
            if self.tick_counter < 10:
                self.tick_counter=self.tick_counter+1
            else:
                self.gain_energy(1)
                self.tick_counter=0

    def Dodge(self):
        result = False
        for skill in self.parent.skills:
            if skill.name=="Dodge" and skill.level>0:
                result = skill.dodge(self.parent,self.engine)
        return result