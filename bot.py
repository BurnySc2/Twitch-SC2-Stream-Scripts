
# https://twitchio.readthedocs.io/en/rewrite/twitchio.html
# https://github.com/TwitchIO/TwitchIO
from twitchio.ext import commands
from twitchio import Message

# https://websockets.readthedocs.io/en/stable/intro.html
import websockets

import asyncio
import time
import os
import json
from typing import Dict, List, Set, Union, Optional

from match_info.match_info import MatchInfo
from points_system.point_system import PointSystem
from plugin_base_class.base_class import BaseScript

import logging
logger = logging.getLogger(__name__)


"""
bot client properties and functions
coroutine: create_clip(token: str, broadcaster_id: Union[str, int])
coroutine: get_chatters(channel: str) {
    # each user is listed here in string form
    count: int
    broadcaster: List[str]
    all: List[str]
    admins: List[str]
    global_mods: List[str]
    moderators: List[str]
    staff: List[str]
    viewers: List[str]
    vips: List[str]
}

Message = {
    User object: author: {
        id: int, id of user
        is_mod: bool
        is_subscriber: int, 0 for false 1 for true
        is_turbo: int, 0 for false 1 for true
        display_name: str, e.g. "BurnySc2"
        name: str, e.g. "burnysc2"
    },
    Channel object: channel: {
        coroutine ban(user: str, resaon: str=""), bans user
        coroutine get_stream() -> dict, info about the stream
        coroutine send(content: str), sends text message to destination channel
        coroutine send_me(content: str), sends text message to destination channel with /me
        coroutine slow()
        coroutine slow_off()
        coroutine timeout(user: str, duration: int=600, reason: str=""), times user out
        coroutine unban(user: str), unbans user
    },
    content: str, content of the message
    _timestamp: int, timestamp of message
    timestamp: datetime, UTC datetime object with twitch timestamp
}
"""

class TwitchChatBot(commands.Bot):
    def __init__(self, irc_token):
        initial_channels = []
        # TODO: only allow one channel to be used
        self.main_channel = "burnysc2"
        super().__init__(irc_token=irc_token, client_id="...", nick="burnysc2bot", prefix="!", initial_channels=initial_channels + [self.main_channel])

        # Start websocket connection to be able to communicate with overlay HTML files
        self.websocket_connections = set()
        self.websocket_server = websockets.serve(self.on_websocket_connection, "127.0.0.1", 5678)

        # Start scripts
        enabled_scripts_path = os.path.join(os.path.dirname(__file__), "config", "enabled_scripts.json")
        with open(enabled_scripts_path) as f:
            enabled_scripts: Dict[str, bool] = json.load(f)

        self.running_scripts: List[BaseScript] = []

        # Start match_info script/plugin
        assert "match_info" in enabled_scripts
        if enabled_scripts["match_info"]:
            # Matchinfo script
            self.match_info = MatchInfo(self)
            self.match_info.load_config()
            self.running_scripts.append(self.match_info)

        # Start point_system script/plugin
        assert "point_system" in enabled_scripts
        if enabled_scripts["point_system"]:
            # Pointsystem script
            self.point_system = PointSystem(self)
            self.running_scripts.append(self.point_system)

    # Events don't need decorators when subclassed
    async def event_ready(self):
        """
        Function is called on bot start when it is connected to twitch channels and ready
        """
        print(f"Ready | {self.nick}")
        logger.warning(f"READY")

        # Create the websocket server - it sends messages to all connected websocket clients (I use them to interact with HTML overlays)
        await self.websocket_server

        for script in self.running_scripts:
            await script.on_ready()

        while 1:
            await asyncio.sleep(1)
            await self.on_tick()

    async def on_websocket_connection(self, websocket: websockets.WebSocketServer, path):
        """ The function that is used by the websockets library. New connections will be held here. """
        logger.warning(f"New websocket connection!")
        self.websocket_connections.add(websocket)
        # I don't know why, but need to keep this function alive
        # If the function returns, the connection closes
        while 1:
            await asyncio.sleep(1)
            # Check if the websocket client closed the connection
            if websocket.closed:
                return

    async def broadcast_json(self, json_string: str):
        """
        Send a json string to all connected websockets
        Remove websocket if sending was unsuccessful
        """
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send(json_string)
            except Exception as e:
                self.websocket_connections.discard(websocket)

    async def event_message(self, message: Message):
        """
        Function that is run every time the bot sees a new message from one of the connected channels
        """
        for script in self.running_scripts:
            await script.on_message(message)

        # Trigger internal commands
        await self.handle_commands(message)

    async def on_tick(self):
        """
        Function that is run every second
        This function is triggered by bot.event_ready()
        """
        for script in self.running_scripts:
            await script.on_tick()

    async def on_new_game(self, match_info: MatchInfo):
        """
        New game was detected. This is the earliest detection possible that has info about opponent (name, race), but not mmr available yet.
        This function is triggered by match_info script
        """
        # print("New game detected")
        for script in self.running_scripts:
            await script.on_new_game(match_info)

    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        """
        New game was detected. This is the earliest detection possible that has info about opponent (name, race, mmr)
        This function is triggered by match_info script
        """
        # print("New game detected, mmr ready")
        for script in self.running_scripts:
            await script.on_new_game_with_mmr(match_info)

    async def on_game_ended(self, match_info: MatchInfo):
        """
        The SC2 game has ended, either the streamer is now in menu, replay or loading screen. This is useful for the betting script to check when the betting is over.
        This function is triggered by match_info script
        """
        # print("Game end detected (either replay started (rewind), or streamer is now in menu)")
        for script in self.running_scripts:
            await script.on_game_ended(match_info)

    # Commands use a different decorator
    @commands.command(name="test")
    async def my_command(self, ctx):
        await ctx.send(f"Hello {ctx.author.name}!")

    # Commands use a different decorator
    @commands.command(name="test2")
    async def my_command(self, ctx):
        chatters = await self.get_chatters("burnysc2")
        await ctx.send(f"Hello {ctx.author.name}!")

if __name__ == '__main__':
    # Load token from config file
    token_file_path = os.path.join(os.path.dirname(__file__), "config", "twitch_irc_token.json")
    with open(token_file_path) as f:
        token_file_json = json.load(f)
        token = token_file_json["token"]

    # Start bot
    bot = TwitchChatBot(irc_token=token)
    bot.run()
