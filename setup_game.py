"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
import random
from typing import Optional

import pygame
import tcod
from pygame import mixer

from Entities import entity_factories
from Map.game_map import GameWorld
from UI import color
from config import Config
from engine import Engine
import input_handlers
from Map.procgen_dungeon import generate_dungeon


# Load the background image and remove the alpha channel.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


majorversion = 0
minorversion = 1
buildversion = 6

def new_game(config: Config) -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    surfacefile = "startmap.csv"
    starter_message = f"Hello and welcome, adventurer, to Winterfjell Deeps: RugPG V{majorversion}.{minorversion}.{buildversion}."

    story_message = f"Long have you lived in the shadow of the mountain named Winterfjell.\n\nAs a child, " \
                    f"you had always heard stories whispered of the horrors that\n\nbefell those who delved " \
                    f"under the dread mountain. That all changed when\n\nyour village began suffering kidnappings" \
                    f" and thefts - the icy darkness\n\nin the mountain is hungering for more. You know that if it " \
                    f"isn't\n\nstopped soon your loved ones will be taken too." \
                    f"\n\n\n\nThe frost is growing, and your only chance to stop it lies deep\n\nunder this icy " \
                    f"place. You grab your dagger and approach\n\nthe entrance to Winterfjell under cover of night\n\n\n\n" \
                    f"Warm winds at your back. Good luck."

    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player, config=config)

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )

    engine.game_world.load_surface(surfacefile)
    engine.update_fov()

    engine.message_log.add_message(
        starter_message, color.welcome_text
    )

    dagger = copy.deepcopy(entity_factories.dagger)
    leather_armor = copy.deepcopy(entity_factories.red_shroud)

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    engine.popup_message("Welcome",starter_message,color.welcome_text,False)
    engine.story_message = story_message
    return engine

def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    pygame.key.set_repeat(500, 20)
    mixer.init()

    engine.play_song("viking1.mp3")
    return engine

class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""
    def __init__(self):
        self.config=Config()

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        pygame.key.set_repeat(500, 20)
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 5,
            "WINTERFJELL DEEPS",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height // 2 - 4,
            f"RugPG V{majorversion}.{minorversion}.{buildversion}",
            fg=color.xp,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "By Rugnir",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play a new game", "[C] Continue last game", "[O] Options", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            return input_handlers.GameStartHandler(new_game(self.config))
        elif event.sym == tcod.event.K_o:
            return input_handlers.OptionsMenuHandler(self,self.config)

        return None