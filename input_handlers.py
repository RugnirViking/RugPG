from __future__ import annotations

import sys
import textwrap
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union, Iterable

import os
import tcod.event
from Entities import entity
from Entities.Components.rarities import Rarity, item_color
from UI import color
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction
)
import exceptions
from Entities.entity import Item, Entity, Actor

from Entities.Components.ai import ConfusedEnemy
from config import Config
from UI.skills_render import render_skills

import actions
if TYPE_CHECKING:
    from engine import Engine
    from Entities.entity import Item, Entity
    from Entities.Components.skill import Skill


MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_a: (-1, 0),
    tcod.event.K_s: (0, 1),
    tcod.event.K_w: (0, -1),
    tcod.event.K_d: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
    tcod.event.K_SPACE,
}
CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            elif self.engine.pending_popup:
                self.engine.pending_popup = False
                return PopupMessage(self, self.engine.popuptext, self.engine.popuptitle, self.engine.popup_textcolor)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class GameStartHandler(EventHandler):

    def __init__(self, engine: Engine):
        super().__init__(engine)

    def on_render(self, console: tcod.Console) -> None:
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8
        # Draw a frame with a custom banner title.
        console.draw_frame(3, 3, console.width - 6, console.height - 6, fg=color.white)
        console.print_box(
            3, 3, console.width - 6, 1, f"┤{self.engine.popuptitle}├", alignment=tcod.CENTER
        )
        console.print(
            console.width // 2,
            console.height // 8,
            self.engine.popuptext,
            fg=self.engine.popup_textcolor,
            bg=color.black,
            alignment=tcod.CENTER,
        )

        console.print(
            console.width // 2,
            console.height * 2 // 8,
            self.engine.story_message,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        # No valid key was pressed
        return MainGameEventHandler(self.engine)


class MainGameEventHandler(EventHandler):

    def __init__(self, engine: Engine):
        super().__init__(engine)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        # print(key)

        player = self.engine.player
        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT) or \
                (key == tcod.event.K_LESS and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT)):
            return actions.TakeStairsAction(player)

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            if not isinstance(player.ai, ConfusedEnemy):
                action = BumpAction(player, dx, dy)
            else:
                action = WaitAction(player)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_g:
            action = PickupAction(player)
        elif key == tcod.event.K_i and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return InventoryInspectHandler(self.engine)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_p:
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.K_SLASH or key == tcod.event.K_MINUS:
            return LookHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.K_j:
            return SkillListHandler(self.engine)
        if self.engine.config.values["AllowDebug"]:
            if key == tcod.event.K_o:
                player.ai = ConfusedEnemy(
                    entity=player, previous_ai=player.ai, turns_remaining=10,
                )
            elif key == tcod.event.K_l:
                self.engine.game_map.flood_reveal(player.x, player.y, True)
                return action
            elif key == tcod.event.K_k:
                return SingleRangedAttackHandler(
                    self.engine,
                    callback=lambda xy: actions.TeleportAction(player, xy),
                )

        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        key = event.sym
        if key == tcod.event.K_ESCAPE:
            self.on_quit()
        elif key == tcod.event.K_v:
            return HistoryViewer(self.engine)


CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}
CURSOR_X_KEYS = {
    tcod.event.K_LEFT: -1,
    tcod.event.K_RIGHT: 1,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str, title: str = "Information", text_color=color.white):
        self.parent = parent_handler
        self.text = text
        self.title = title
        self.text_color = text_color

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=self.text_color,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=15,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 4, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense}"
        )

        console.print(
            x=x + 1, y=y + 7, string=f"Equipment: "
        )
        n = 8
        if self.engine.player.equipment.weapon:
            console.print(
                x=x + 2, y=y + n, string=f"Right Hand: {self.engine.player.equipment.weapon.name}"
            )
            n += 1
        console.print(
            x=x + 2, y=y + n, string=f"Left Hand: "
        )
        console.print(
            x=x + 13, y=y + n, string=f"Torch", fg=color.red
        )
        n += 1
        if self.engine.player.equipment.armor:
            console.print(
                x=x + 2, y=y + n, string=f"Armour: {self.engine.player.equipment.armor.name}"
            )
            n += 1
        if self.engine.player.equipment.ring:
            console.print(
                x=x + 2, y=y + n, string=f"Ring: {self.engine.player.equipment.ring.name}"
            )
            n += 1


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 35:
            x = 35
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=45,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You have leveled up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+20 Max HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.power})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Agility (+1 defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


Entities_List = list[Entity]


class TileEntityListHandler(AskUserEventHandler):
    TITLE = "Tile Information"

    def __init__(self, engine: Engine, x: int, y: int, entities_in_tile: Entities_List):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        self.x = x
        self.y = y
        self.entities_in_tile = entities_in_tile
        self.entities_length = len(entities_in_tile)
        self.cursor = self.entities_length - 1

    def wrap(self, string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():  # Handle newlines in messages.
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, f"┤{self.TITLE}├", alignment=tcod.CENTER
        )

        y_offset = log_console.height - 2 - 1

        for cur_entity in reversed(self.entities_in_tile):
            for line in reversed(list(self.wrap(cur_entity.name, log_console.width - 2))):
                col = color.white
                if isinstance(cur_entity, Item):
                    if cur_entity.equippable:
                        col = color.status_effect_applied
                    elif cur_entity.consumable:
                        col = color.xp
                elif isinstance(cur_entity, Actor):
                    col = color.important

                log_console.print(x=1, y=1 + y_offset, string=line, fg=col)
                y_offset -= 1
                if y_offset < 0:
                    log_console.blit(console, 3, 3)
                    return  # No more space to print messages.

        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.entities_length - 1
            elif adjust > 0 and self.cursor == self.entities_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.entities_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.entities_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> EventHandler:
        """Return to main handler."""
        # show a list of items on the tile
        if not self.engine.game_map.in_bounds(x, y) or not self.engine.game_map.visible[x, y]:
            return MainGameEventHandler(self.engine)

        entities_in_tile = [entity_a for entity_a in self.engine.game_map.entities if
                            (entity_a.x == x and entity_a.y == y)]
        return TileEntityListHandler(self.engine, x, y, entities_in_tile)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
            self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class SkillTreeHandler(AskUserEventHandler):
    TITLE = "Skill Trees"

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        self.y_offset=0
        self.y_min=0
        self.y_max=50
        self.selected_skill_index=0

    def wrap(self, string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():  # Handle newlines in messages.
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        log_console = tcod.Console(console.width, console.height)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, f"┤{self.TITLE}├", alignment=tcod.CENTER
        )
        m_x, m_y = self.engine.mouse_location
        for skill in self.engine.skills_list:
            if m_x>=skill.x and m_x<skill.x+5:
                if m_y>=skill.y-self.y_offset+2 and m_y<skill.y-self.y_offset+7:
                    self.selected_skill_index=self.engine.skills_list.index(skill)
                    break

        render_skills(log_console,self.engine,self.y_offset+1,self.selected_skill_index)

        log_console.blit(console, 0, 0)
    def level_skill(self,skill):
        if skill.level_up(self.engine.player):
            self.engine.player.skill_points-=1

    def ev_mousebuttondown(
            self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        m_x, m_y = self.engine.mouse_location
        found_skill=None
        for skill in self.engine.skills_list:
            if m_x>=skill.x and m_x<skill.x+5:
                if m_y>=skill.y-self.y_offset+2 and m_y<skill.y-self.y_offset+7:
                    self.selected_skill_index=self.engine.skills_list.index(skill)
                    found_skill=skill
                    break

        if event.button == 1 and found_skill is not None:
            self.level_skill(found_skill)
        else:
            return super().ev_mousebuttondown(event)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            self.y_offset = max(self.y_min, min(self.y_offset + adjust, self.y_max))
        elif event.sym in CURSOR_X_KEYS:
            adjust = CURSOR_X_KEYS[event.sym]
            self.selected_skill_index = max(0, min(self.selected_skill_index + adjust, len(self.engine.skills_list)-1))
        elif event.sym in CONFIRM_KEYS:
            self.level_skill(self.engine.skills_list[self.selected_skill_index])
        elif event.sym==tcod.event.K_SPACE:
            str=""
            for skill in self.engine.player.skills:
                str+=f" ({skill.level}) {skill.name},"
            print(str)
        elif event.sym==tcod.event.K_ESCAPE:
            return super().ev_keydown(event)



class SkillListHandler(AskUserEventHandler):
    """This handler lets the user select a skill.

    What happens then depends on the subclass.
    """

    TITLE = "Skills Menu"

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_skills = len(self.engine.player.skills)

        height = number_of_skills + 3

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4
        num=0
        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_skills > 0:
            for i, skill in enumerate(self.engine.player.active_skills):
                item_key = chr(ord("a") + i)

                item_string = f"{skill.name}"

                console.print(x+1,y+i+1,f"({item_key}) ",color.white)
                console.print(x + 5, y + i + 1, item_string, fg=color.white)
                num=i+1
        else:
            console.print(x + 1, y + 1, "(Empty)")
            num=0
        console.print(x + 1, y + num+2, f"(z) Skill Trees")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 24:
            try:
                selected_skill = player.active_skills[index]
            except IndexError:
                self.engine.message_log.add_message("No item in that skill slot", color.invalid)
                return None
            return self.on_skill_selected(selected_skill)
        if index==25:
            return SkillTreeHandler(self.engine)

        return super().ev_keydown(event)
    def on_skill_selected(self, skill: Skill) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        action = skill.activate(self.engine)
        return action


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)

                is_equipped = self.engine.player.equipment.item_is_equipped(item)
                item_string = f"{item.name}"

                col = item_color(item.rarity)
                if is_equipped:
                    item_string = f"{item_string} (E)"
                    console.print(x+1,y+i+1,f"({item_key}) ",col)
                    console.print(x + 5, y + i + 1, item_string, color.equipped)
                else:
                    console.print(x+1,y+i+1,f"({item_key}) ",col)
                    console.print(x + 5, y + i + 1, item_string, fg=color.white)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("No item in that inventory slot", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None


class ItemInspectHandler(AskUserEventHandler):
    def __init__(self, engine: Engine, item: Item):
        super().__init__(engine)
        self.item = item
        self.TITLE = self.item.name.upper()

    def wrap(self, string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():  # Handle newlines in messages.
            yield from textwrap.wrap(
                line, width, expand_tabs=True,
            )

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, f"┤{self.TITLE}├", alignment=tcod.CENTER
        )

        y_offset = log_console.height // 8
        col = item_color(self.item.rarity)
        rarity_name = "a"
        if self.item.rarity == Rarity.UNCOMMON:
            rarity_name = "an uncommon"
            col = color.item_uncommon
        elif self.item.rarity == Rarity.RARE:
            rarity_name = "a rare"
            col = color.item_rare
        elif self.item.rarity == Rarity.EPIC:
            rarity_name = "an epic"
            col = color.item_epic
        elif self.item.rarity == Rarity.LEGENDARY:
            rarity_name = "the legendary"
            col = color.item_legendary
        elif self.item.rarity == Rarity.COMMON:
            col = color.item_common
        elif self.item.rarity == Rarity.JUNK:
            col = color.item_junk
        line = f"This is {rarity_name} {self.item.name}"
        log_console.print(x=5, y=1 + y_offset, string=line, fg=col)
        log_console.print(x=log_console.width // 2, y=2 + y_offset, string="Properties:", fg=col, alignment=tcod.CENTER)
        n = 0
        if self.item.equippable:
            log_console.print(x=5, y=3 + n + y_offset, string="Equippable", fg=color.item_description)
            n += 1
        if self.item.consumable:
            log_console.print(x=5, y=3 + n + y_offset, string="Consumable", fg=color.item_description)
            n += 1

        log_console.print(x=log_console.width // 2, y=4 + n + y_offset, string="Description:", fg=col,
                          alignment=tcod.CENTER)
        for line in list(self.wrap(self.item.description, 60)):
            log_console.print(x=5, y=5 + n + y_offset, string=line, fg=color.item_description)
            n += 1
        log_console.blit(console, 3, 3)


class InventoryInspectHandler(InventoryEventHandler):
    """Handle inspecting an inventory item."""

    TITLE = "Select an item to inspect"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        return ItemInspectHandler(self.engine, item)


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)


class OptionsMenuHandler(BaseEventHandler):
    MAX_INDEX = 4

    def __init__(self, parent: BaseEventHandler, config: Config):
        self.parent = parent
        self.config = config
        self.selected_index = 0
        self.controls = {
            "Master Volume": ["pct", self.config.values["MasterVolume"]],
            "Music Volume": ["pct", self.config.values["MusicVolume"]],
            "Sound Effects Volume": ["pct", self.config.values["GameVolume"]],
            "Allow Debug Commands": ["bool", self.config.values["AllowDebug"]],
        }
        self.keys = ["Master Volume",
                     "Music Volume",
                     "Sound Effects Volume",
                     "Allow Debug Commands",
                     ]

    def on_render(self, console: tcod.Console) -> None:
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8
        # Draw a frame with a custom banner title.
        console.draw_frame(3, 3, console.width - 6, console.height - 6, fg=color.white)
        console.print_box(
            3, 3, console.width - 6, 1, f"┤Options├", alignment=tcod.CENTER
        )

        control_count = 0
        for key in self.controls:
            self.render_control(console, self.controls[key][0], key, control_count,
                                control_count == self.selected_index)
            control_count += 1

    @property
    def selected_index(self):
        return self._selected_index

    @selected_index.setter
    def selected_index(self, value):
        self._selected_index = value
        if self._selected_index > self.MAX_INDEX - 1:
            self._selected_index = self._selected_index - self.MAX_INDEX

        if self._selected_index < 0:
            self._selected_index = self._selected_index + self.MAX_INDEX

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            self.selected_index = self.selected_index + dy
            if dx:
                self.control_input(dx)
        elif key == tcod.event.K_ESCAPE:
            self.save_values()
            return self.parent

        # No valid key was pressed

    def render_control(self, console: tcod.Console,
                       control_type: str,
                       key: str,
                       control_count: int,
                       selected: bool = False):
        col = color.options_control
        if selected:
            col = color.options_control_selected
        if control_type == "pct":
            console.print(
                8,
                (console.height // 8) + control_count * 2,
                f"{key}: ",
                fg=col,
                bg=color.black,
                alignment=tcod.LEFT,
            )
            console.print(
                8 + len(key) + 2,
                (console.height // 8) + control_count * 2,
                f"{str(int(self.controls[key][1] * 100))}%",
                fg=col,
                bg=color.black,
                alignment=tcod.LEFT,
            )
        elif control_type == "bool":
            console.print(
                8,
                (console.height // 8) + control_count * 2,
                f"{key}: {str(self.controls[key][1])}",
                fg=col,
                bg=color.black,
                alignment=tcod.LEFT,
            )

    def control_input(self, dy):
        index = self.selected_index
        key = self.keys[index]
        type = self.controls[key][0]
        cur_val = self.controls[key][1]
        if type == "pct":
            self.controls[key][1] = min(max(0, cur_val + dy * 0.05), 1)
        if type == "bool":
            self.controls[key][1] = not cur_val

    def save_values(self):
        self.config.load_controls_values(self.controls)
