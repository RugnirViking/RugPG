from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from UI import color
from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from Entities.entity import Actor

class BaseAI(Action):

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]

class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        if self.entity.name=="Player":
            print("hey")

        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance

        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()


class PlayerAI(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        #todo player stuff here
        pass


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack - even if its another hostile enemy
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y,).perform()


class FearedEnemy(BaseAI):
    """
    A feared enemy will run away from the source of its fear  for a given number of turns,
    then revert back to its previous AI. If an actor blocks the path away , it will attack -
    even if its another hostile enemy.
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int, fear_source: Actor
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining
        self.fear_source = fear_source

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} overcomes its fear."
            )
            self.entity.ai = self.previous_ai
        else:
            target = self.fear_source
            # loop though all tiles surrounding monster and find the furthest then move to it
            max_dist = 0
            direction_x, direction_y = (0, 0)
            for ix in range(3):
                for iy in range(3):
                    jx = self.entity.x + (ix-1)
                    jy = self.entity.y + (iy-1)

                    dx = target.x - jx
                    dy = target.y - jy
                    distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance
                    if distance>max_dist and self.engine.game_map.tiles["walkable"][jx, jy]:
                        max_dist = distance
                        direction_x, direction_y = (ix-1, iy-1)

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            if not direction_x == 0 and not direction_y == 0:
                return BumpAction(self.entity, direction_x, direction_y, ).perform()
            else:
                return WaitAction(self.entity).perform()

class CharmedEnemy(BaseAI):
    """
    A charmed enemy will attack nearby hostile enemies for a given number of turns,
    then revert back to its previous AI.
    """


    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int, charmer: Actor
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining
        self.charmer = charmer
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} breaks free from its master's control.", color.important
            )
            self.entity.ai = self.previous_ai
        else:
            consumer = self.entity
            target = None
            closest_distance = 18.0
            self.turns_remaining -= 1

            for actor in self.engine.game_map.actors:
                # Note we check whether the entity is visible
                # this implicitly means there is a line-of-sight to the entity
                if actor is not consumer and actor is not self.charmer and self.engine.game_map.visible[actor.x, actor.y]:
                    distance = consumer.distance(actor.x, actor.y)

                    if distance < closest_distance:
                        target = actor
                        closest_distance = distance
            if target:
                dx = target.x - self.entity.x
                dy = target.y - self.entity.y
                distance = max(abs(dx), abs(dy))  # Chebyshev distance. TODO: make this taxicab distance

                if self.engine.game_map.visible[self.entity.x, self.entity.y]:
                    if distance <= 1:
                        return MeleeAction(self.entity, dx, dy).perform()

                    self.path = self.get_path_to(target.x, target.y)

                if self.path:
                    dest_x, dest_y = self.path.pop(0)
                    return MovementAction(
                        self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
                    ).perform()

                return WaitAction(self.entity).perform()
            else:
                return WaitAction(self.entity).perform()

