from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple

import asyncio
import datetime
import random
import websockets
import aiohttp
import time
import json
import os
import sys

from loguru import logger


# Communication with OBS Studio
from obswebsocket import obsws, requests as obsrequest
from obswebsocket.exceptions import ConnectionFailure
from websocket._exceptions import WebSocketConnectionClosedException

from plugin_base_class.base_class import BaseScript

if TYPE_CHECKING:
    from bot import TwitchChatBot
    from match_info.match_info import MatchInfo


class SceneSwitcher(BaseScript):
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot
        self.settings_path = os.path.join(os.path.dirname(__file__), "config.json")
        self.settings: dict = {}
        self.ws: obsws = obsws()
        self.last_set_scene = ""

    @property
    def enabled(self):
        return self.settings.get("enabled", False)

    @property
    def connected(self):
        if self.ws.ws is None:
            return False
        return self.ws.ws.connected

    def load_settings(self):
        """ Loads settings from local settings.json file """
        # Set the default settings. In case in a later version of this script the settings change, new default variables will be added automatically
        self.settings = {
            # Connection settings to OBS Studio websockets plugin
            "host": "localhost",
            "port": 4444,
            "password": "",
        }
        if os.path.isfile(self.settings_path):
            with open(self.settings_path) as f:
                logger.info(f"Scene switcher loaded settings.")
                self.settings.update(json.load(f))

    def connect(self):
        try:
            self.ws = obsws(self.settings["host"], self.settings["port"], self.settings["password"])
            self.ws.connect()
        except ConnectionFailure as e:
            pass

    # def get_obs_scenes(self) -> List[str]:
    #     """ Retrieves all created scene names from OBS Studio """
    #     if not self.connected:
    #         self.connect()
    #     if self.connected:
    #         scenes = self.ws.call(obsrequest.GetSceneList())
    #         scene_names: List[str] = [scene["name"] for scene in scenes.datain["scenes"]]
    #         return scene_names
    #     return []

    def switch_obs_scene(self, target_scene: str):
        if target_scene == self.last_set_scene:
            # Last set scene is identical to the current target scene, don't attempt to switch scene
            return

        self.last_set_scene = target_scene
        if not self.connected:
            self.connect()
            if self.connected:
                logger.info(f"Scene switcher connected to OBS websocket")
        if self.connected:
            try:
                self.ws.call(obsrequest.SetCurrentScene(target_scene))
            except (WebSocketConnectionClosedException, ConnectionFailure) as e:
                # OBS was closed
                logger.info(f"Error in scene switcher script: {e}")

    async def on_new_game(self, match_info: MatchInfo):
        logger.info("Scene switcher new game was called")
        logger.info(self.settings)
        game_scene: str = self.settings.get("game_scene", "")
        if game_scene:
            logger.info(f"New game: Switching scene to '{game_scene}'")
            self.switch_obs_scene(game_scene)

    async def on_game_ended(self, match_info: MatchInfo):
        logger.info("Scene switcher game ended was called")
        menu_scene: str = self.settings.get("menu_scene", "")
        if menu_scene:
            logger.info(f"Game ended: Switching scene to '{menu_scene}'")
            self.switch_obs_scene(menu_scene)

    # TODO when joining replay or pressing rewind, set replay scene


if __name__ == "__main__":
    a = SceneSwitcher()
    a.load_settings()
    while 1:
        a.switch_obs_scene("SceneGame")
        time.sleep(3)
        a.switch_obs_scene("SceneLobby")
        time.sleep(3)

    # a = SceneSwitcher()
    # a.load_settings()
    # scenes = a.get_obs_scenes()
    # logger.info(scenes)
