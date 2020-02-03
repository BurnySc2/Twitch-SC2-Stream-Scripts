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
                # logger.info(f"Scene switcher loaded settings.")
                self.settings.update(json.load(f))
        else:
            logger.warning(f"No config file found for scene switcher script: {self.settings_path}")

    def connect(self):
        try:
            self.ws = obsws(self.settings["host"], self.settings["port"], self.settings["password"])
            self.ws.connect()
        except ConnectionFailure as e:
            logger.exception("Error trying to connect to obs")
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
        # Return on empty string
        if not target_scene:
            return

        if target_scene == self.last_set_scene:
            # Last set scene is identical to the current target scene, don't attempt to switch scene
            return

        self.last_set_scene = target_scene
        if not self.connected:
            self.connect()
            if self.connected:
                logger.info(f"Scene switcher connected to OBS websocket")
        if self.connected:
            logger.info(f"Switching scene to '{target_scene}'")
            try:
                self.ws.call(obsrequest.SetCurrentScene(target_scene))
            except (WebSocketConnectionClosedException, ConnectionFailure) as e:
                # OBS was closed
                # logger.exception(f"Error in scene switcher script: {e}")
                pass

    async def on_new_game(self, match_info: MatchInfo):
        self.switch_obs_scene(self.settings.get("game_scene", ""))

    async def on_game_resumed_from_replay(self, match_info: MatchInfo):
        self.switch_obs_scene(self.settings.get("game_scene", ""))

    async def on_rewind(self, match_info: MatchInfo):
        self.switch_obs_scene(self.settings.get("replay_scene", ""))

    async def on_replay_entered(self, match_info: MatchInfo):
        self.switch_obs_scene(self.settings.get("replay_scene", ""))

    async def on_game_ended(self, match_info: MatchInfo):
        self.switch_obs_scene(self.settings.get("menu_scene", ""))


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
