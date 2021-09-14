from __future__ import annotations

import lzma
import pickle
import subprocess
import threading
import multiprocessing
import random
from typing import TYPE_CHECKING

import pygame
from pygame import mixer, time
from tcod.console import Console
from tcod.map import compute_fov
import exceptions
from UI import render_functions, color

from UI.message_log import MessageLog
from easing_functions import *

if TYPE_CHECKING:
    from Entities.entity import Actor
    from Map.game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.pending_popup = False
        self.popup_textcolor = None
        self.popuptitle = None
        self.popuptext = None
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.story_message = ""
        self.max_volume = 400
        self.current_volume = 0
        pygame.key.set_repeat(500, 20)
        mixer.init()

        self.play_song("viking1.mp3")
        # self.mixer.music.load('viking1.mp3')

        # self.mixer.music.play(-1)

    # play the song and fade in the song to the max_volume
    def play_song(self, song_file):
        print("Song starting: " + song_file)
        mixer.music.load(song_file)
        mixer.music.play(-1)
        # providing a name for the thread improves usefulness of error messages.
        loopThread = threading.Thread(target=self.fadeinthread, name='backgroundMusicThread')
        loopThread.daemon = True  # shut down music thread when the rest of the program exits
        loopThread.start()

    def fadeinthread(self):
        # gradually increase volume to max
        a = QuadEaseInOut(start=0, end=1, duration=400)
        while mixer.music.get_busy():
            if self.current_volume < self.max_volume:
                vol = a.ease(self.current_volume)  # 4 is a number between 0 and the duration you specified
                mixer.music.set_volume(self.current_volume / self.max_volume)
                self.current_volume += 1

            time.Clock().tick(1)

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)

    def save_log(self, filename: str) -> None:
        with open(filename, "wb") as f:
            for message in self.message_log.messages:
                f.write((message.full_text + "\n").encode())

    def handle_enemy_turns(self) -> None:
        """
            Handles enemy movement and attacking
        :return:
        """
        random.seed()
        for entity in set(self.game_map.actors):
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    # TODO: make enemy print when their action is impossible if config set to debug
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=12,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console, self.player.x, self.player.y)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)
        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    def popup_message(self, title="Info", message="<undefined popup>", textcolor=color.white, doPending=True):
        self.popuptitle = title
        self.popuptext = message
        self.popup_textcolor = textcolor
        if doPending:
            self.pending_popup = True
