from __future__ import annotations

import random
from typing import Tuple, TYPE_CHECKING

from UI import color

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from Map.game_map import GameMap


def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()


def render_bar(
        console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    console.draw_rect(x=0, y=45, width=20, height=1, ch=1, bg=color.bar_empty)

    if bar_width > 0:
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )


def render_dungeon_level(
        console: Console, dungeon_level: int, location: Tuple[int, int],type:str="dungeon"
) -> None:
    """
    Render the level the player is currently on, at the given location.
    """
    if type=="dungeon":
        x, y = location
        n=random.random()

        console.print(x=x, y=y, string=f"{dungeon_level}: Dungeon Vaults")
    elif type=="cave":
        x, y = location

        console.print(x=x, y=y, string=f"{dungeon_level}: Caverns")
    elif type=="barracks":
        x, y = location

        console.print(x=x, y=y, string=f"{dungeon_level}: Barracks")
    elif type=="quarters":
        x, y = location

        console.print(x=x, y=y, string=f"{dungeon_level}: Quarters")
    elif type=="temple":
        x, y = location

        console.print(x=x, y=y, string=f"{dungeon_level}: Temple Complex")



def render_names_at_mouse_location(
        console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, string=names_at_mouse_location)


def render_current_status_effects(
        console: Console, x: int, y: int, engine: Engine, width:int
) -> None:
    effects = engine.player.status_effects
    n = 0
    for effect in effects:
        console.draw_rect(
            x=x, y=y + n, width=width, height=1, ch=1, bg=effect.bg
        )
        if effect.duration==-1:
            console.print(x=x, y=y + n, string=f" {effect.name} ", fg=effect.fg)
        else:
            console.print(x=x, y=y + n, string=f" {effect.name} ({effect.duration})", fg=effect.fg)
        n = n + 1
