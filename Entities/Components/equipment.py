from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from Entities.Components.base_component import BaseComponent
from Entities.Components.equippable import Equippable
from Entities.equipment_types import EquipmentType

if TYPE_CHECKING:
    from Entities.entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None, ring: Optional[Item] = None):
        self.ring = ring
        self.weapon = weapon
        self.armor = armor

    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.defense_bonus
        return bonus

    @property
    def hp_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.hp_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.hp_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.hp_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.power_bonus
        return bonus

    @property
    def energy_charge_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.energy_charge_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.energy_charge_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.energy_charge_bonus

        return bonus

    @property
    def max_energy_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.max_energy_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.max_energy_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.max_energy_bonus

        return bonus

    @property
    def resist_poison_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.resist_poison_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.resist_poison_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.resist_poison_bonus

        return bonus

    @property
    def resist_magic_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.resist_magic_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.resist_magic_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.resist_magic_bonus

        return bonus

    @property
    def resist_curse_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.resist_curse_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.resist_curse_bonus

        if self.ring is not None and self.ring.equippable is not None:
            bonus += self.ring.equippable.resist_curse_bonus

        return bonus
    def item_is_equipped(self, item: Item) -> bool:
        return self.weapon == item or self.armor == item or self.ring == item

    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    def equip_to_slot(self, slot: str, item: Equippable, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        item.equippable.equip(self.parent)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)
        if add_message:
            self.unequip_message(current_item.name)

        current_item.equippable.unequip(self.parent)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        elif(
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.ARMOR
        ):
            slot = "armor"
        else:
            slot = "ring"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)