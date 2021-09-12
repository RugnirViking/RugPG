#!/usr/bin/env python3
import copy
from typing import TYPE_CHECKING
import traceback

import tcod

from Entities import entity_factories
from UI import color
from engine import Engine
from Map.procgen_dungeon import generate_dungeon


if TYPE_CHECKING:
    from input_handlers import MainGameEventHandler, EventHandler

def main() -> None:
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30
    max_monsters_per_room = 2
    max_items_per_room = 2

    majorversion=0
    minorversion=1
    buildversion=5

    starter_message = f"Hello and welcome, adventurer, to RugPG V{majorversion}.{minorversion}.{buildversion}"


    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )
    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)
    entities = {player}

    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        max_items_per_room=max_items_per_room,
        engine=engine,
    )

    engine.update_fov()

    engine.message_log.add_message(
        starter_message, color.welcome_text
    )

    with tcod.context.new_terminal(
            screen_width,
            screen_height,
            tileset=tileset,
            title="RugPG",
            vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        while True:
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)

            try:
                for event in tcod.event.wait():
                    context.convert_event(event)
                    engine.event_handler.handle_events(event)
            except Exception:  # Handle exceptions in game.
                traceback.print_exc()  # Print error to stderr.
                # Then print the error to the message log.
                engine.message_log.add_message(traceback.format_exc(), color.error)


if __name__ == "__main__":
    main()