from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from Entities.Components.status_effects import StatusEffect, FrostShockStatus, MawSiphonStatus
from UI import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from Entities.entity import Actor, Entity, Item
    from Entities.Components.skill import Skill


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")

                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        raise exceptions.Impossible("There is nothing here to pick up.")


class ItemAction(Action):
    def __init__(
            self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)

class SkillAction(Action):
    def __init__(
            self, entity: Actor, skill: Skill, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.skill = skill
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        self.skill.perform(self.target_xy)


class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    def perform(self) -> None:
        pass


class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            if self.engine.game_world.current_floor == 1:
                self.engine.message_log.add_message(
                    "You climb down the stone steps, wondering what horrors await you below", color.descend
                )
            else:
                self.engine.message_log.add_message(
                    "You descend the staircase deeper into the frozen heart of the mountain.", color.descend
                )
        else:
            raise exceptions.Impossible("There are no stairs here.")


class ActionWithDirection(Action):

    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        raise NotImplementedError()

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")
        damage = 0
        if target.melee_neighbors() > 3:
            damage = self.entity.fighter.power
        elif target.melee_neighbors() > 1:
            damage = self.entity.fighter.power - target.fighter.defense / 2
        else:
            damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = ""
        if (target.name == "Player"):
            attack_desc = f"{self.entity.name.capitalize()} attacks you"
        else:
            attack_desc = f"{self.entity.name.capitalize()} attacks the {target.name.capitalize()}"

        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {int(damage)} hit points.", attack_color
            )
            target.fighter.melee_attack(int(damage), self.entity)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )
        for effect in self.entity.status_effects:
            effect.on_deal_damage(target,int(damage))


class MovementAction(ActionWithDirection):

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("You cannot escape the frozen evil that way.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    """
        Bump checks if an impassable entity is in the direction being bumped and attacks if there is and tries to
        move there if there isn't
    """

    def perform(self) -> None:
        if self.target_actor and self.target_actor.is_alive:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class FreezeSpellAction(ActionWithDirection):

    def perform(self) -> None:
        target = self.target_actor
        if not target and self.entity.name == "Player":
            raise exceptions.Impossible("Nothing to attack.")

        damage = 6 - target.fighter.defense

        attack_desc = ""
        target_desc = ""
        target_desc2 = ""
        target_desc3 = ""
        if (target.name == "Player"):
            attack_desc = f"{self.entity.name.capitalize()} casts Frost Shock at you"
            target_desc = "you"
            target_desc2 = "your"
            target_desc3 = "grow"
        else:
            attack_desc = f"{self.entity.name.capitalize()} casts Frost Shock at the {target.name.capitalize()}"
            target_desc = f"the {target.name.capitalize()}"
            target_desc2 = f"the {target.name.capitalize()}'s"
            target_desc3 = "grows"

        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {int(damage)} hit points and freezing {target_desc}. Ice spikes begin to "
                f"pierce {target_desc2} skin...",
                attack_color
            )
            target.fighter.take_damage(int(damage))
            status = FrostShockStatus("Frost Shock", 1, target, 10)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage. However, {target_desc} {target_desc3} colder and ice spikes "
                f"begin to pierce {target_desc2} skin...", attack_color
            )
            status = FrostShockStatus("Frost Shock", 1, target, 5)

class MawSpellAction(ActionWithDirection):
    def __init__(self,entity,dx,dy,magnitude):
        super().__init__(entity=entity,dx=dx,dy=dy)
        self.magnitude=magnitude

    def perform(self) -> None:
        target = self.target_actor
        if not target and self.entity.name == "Player":
            raise exceptions.Impossible("Nothing to attack.")

        damage = max(0,self.magnitude+3 - target.fighter.defense)

        attack_desc = ""
        target_desc = ""
        if (target.name == "Player"):
            attack_desc = f"{self.entity.name.capitalize()} bites your leg, injecting maw-venom"
            target_desc = "your"
        else:
            attack_desc = f"{self.entity.name.capitalize()}  bites the {target.name.capitalize()}, injecting maw-venom"
            target_desc = f"the {target.name.capitalize()}'s"

        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {int(damage)} hit points and {target_desc} energy starts to be siphoned",
                attack_color
            )
            target.fighter.take_damage(int(damage))
            status = MawSiphonStatus("Maw Siphon", self.magnitude, target, 10)
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} and {target_desc} energy starts to be siphoned", attack_color
            )
            status = MawSiphonStatus("Maw Siphon", self.magnitude, target, 10)

class TeleportAction(Action):
    def __init__(
            self, entity: Actor, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        self.entity.x = self.target_xy[0]
        self.entity.x = self.target_xy[1]
        self.entity.place(self.target_xy[0], self.target_xy[1], self.entity.gamemap)
