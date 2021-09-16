from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from Entities.Components.base_component import BaseComponent
from Entities.Components.inventory import Inventory
from Entities.Components.status_effects import StatusEffect, VampirismStatusEffect
from Entities.equipment_types import EquipmentType

if TYPE_CHECKING:
    from Entities.entity import Item, Actor


class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
        apply_effect: Optional[StatusEffect] = None
    ):
        self.equipment_type = equipment_type

        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus
        self.apply_effect = apply_effect
        self.entity: Optional[Actor] = None

    def equip(self, entity: Actor):
        self.entity = entity
        if self.apply_effect:
            self.apply_effect.apply(self.entity)
            self.entity.status_effects.append(self.apply_effect)

    def unequip(self, entity: Actor):
        if self.apply_effect:
            self.entity.status_effects.remove(self.apply_effect)
        self.entity = None


class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)


class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3, power_bonus=-1)


class ScaleMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3, power_bonus=1)


class RedShroud(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR,
                         defense_bonus=1,
                         power_bonus=0,
                         apply_effect=VampirismStatusEffect("Shroudthirst", 2, None, duration=-1))