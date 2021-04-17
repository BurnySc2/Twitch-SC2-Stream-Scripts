# https://twitchio.readthedocs.io/en/rewrite/twitchio.html
# https://github.com/TwitchIO/TwitchIO
from twitchio.ext import commands
from twitchio.dataclasses import User as TwitchUser
from twitchio.dataclasses import Channel as TwitchChannel
from twitchio.dataclasses import Message as TwitchMessage
from twitchio.dataclasses import Context as TwitchContext
from twitchio.client import Chatters as TwitchChatters

# https://github.com/tsifrer/python-twitch-client
from twitch import TwitchClient

# https://websockets.readthedocs.io/en/stable/intro.html
import websockets

import asyncio
import json
import sys
from pathlib import Path

from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin

from typing import Dict, List, Set, Union, Optional

# https://github.com/Delgan/loguru
from loguru import logger

# Remove default loggers
logger.remove()
# Log to console
logger.add(sys.stdout, level="INFO")
# Log to file, max size 5mb
logger.add("bot.log", rotation="1 MB", retention="1 month", level="INFO")


from match_info.match_info import MatchInfo
from points_system.point_system import PointSystem
from build_order_overlay.build_order import BuildOrderOverlay
from scene_switcher.scene_switcher import SceneSwitcher
from plugin_base_class.base_class import BaseScript


@dataclass()
class MainConfig(DataClassJsonMixin):
    twitch_channel_name: str = "burnysc2"
    bot_name: str = "burnysc2bot"
    command_prefix: str = "!"
    match_info: bool = True
    point_system: bool = True
    build_order_overlay: bool = True
    scene_switcher: bool = True


class TwitchChatBot(commands.Bot):
    def __init__(self, irc_token):
        # Load config file
        bot_config_path = Path(__file__).parent / "config" / "bot_config.json"
        assert bot_config_path.is_file(), f"No config file for bot.py found: {bot_config_path}"
        with open(bot_config_path) as f:
            self.bot_config = MainConfig.from_json(f.read())
            # bot_config: Dict[str, Union[str, bool]] = json.load(f)

        # The main channel the bot is going to interact with
        self.initial_channels = [self.main_channel_name]
        bot_name = self.bot_config.bot_name
        command_prefix = self.bot_config.command_prefix
        super().__init__(
            # Irc token to be able to connect to chat
            irc_token=irc_token,
            # Client ID to use advanced twitch API features, TODO
            client_id="...",
            # The name of the bot, you need to create a second twitch account for this
            nick=bot_name,
            prefix=command_prefix,
            # The initial channels the bot is going to join, for now it will only be one channel
            initial_channels=self.initial_channels,
        )

        # Start websocket connection to be able to communicate with overlay HTML files
        self.websocket_connections = set()
        self.websocket_server = websockets.serve(self.on_websocket_connection, "127.0.0.1", 5678)

        # Start connection to twitch - required to check if a stream is live
        twitch_client_id_path = Path(__file__).parent / "config" / "twitch_client_id.json"
        assert twitch_client_id_path.is_file()
        with twitch_client_id_path.open() as f:
            twitch_client_id = json.load(f)["client_id"]
            self.twitch_client: TwitchClient = TwitchClient(client_id=twitch_client_id)

        # Start scripts - all class instances are kept inside this list
        self.running_scripts: List[BaseScript] = []

        # Start match_info script/plugin
        if self.bot_config.match_info:
            # Matchinfo script
            self.match_info = MatchInfo(self)
            self.running_scripts.append(self.match_info)

        # Start point_system script/plugin
        if self.bot_config.point_system:
            # Pointsystem script
            self.point_system = PointSystem(self)
            self.running_scripts.append(self.point_system)

        # Start build_order_overlay script/plugin
        if self.bot_config.build_order_overlay:
            self.build_order_overlay = BuildOrderOverlay(self)
            self.build_order_overlay.load_build_orders()
            self.running_scripts.append(self.build_order_overlay)

        # Start scene_switcher script/plugin
        if self.bot_config.scene_switcher:
            self.scene_switcher = SceneSwitcher(self)
            self.running_scripts.append(self.scene_switcher)

    @property
    def main_channel_name(self) -> str:
        return self.bot_config.twitch_channel_name.lower()

    @property
    def main_channel(self) -> TwitchChannel:
        return self.get_channel(self.main_channel_name)

    # Events don't need decorators when subclassed
    async def event_ready(self):
        """ Function is called on bot start when it is connected to twitch channels and ready """
        logger.info(f"bot.py READY | {self.nick} - Connected to channel {self.initial_channels}")

        # Create the websocket server - it sends messages to all connected websocket clients (I use them to interact with HTML overlays)
        await self.websocket_server

        for script in self.running_scripts:
            await script.on_ready()

        while 1:
            await asyncio.sleep(1)
            await self.on_tick()

    async def on_websocket_connection(self, websocket: websockets.WebSocketServer, path):
        """ The function that is used by the websockets library. New connections will be held here. """
        logger.info(f"New websocket connection from overlay file")
        self.websocket_connections.add(websocket)
        # I don't know why, but need to keep this function alive
        # If the function returns, the connection closes

        # Whenever there is a new websocket connection, scripts may need to hide or clear the default overlay
        for script in self.running_scripts:
            await script.on_new_websocket_connection()

        while 1:
            await asyncio.sleep(1)
            # Check if the websocket client closed the connection
            if websocket.closed:
                return

    async def websocket_broadcast_json(self, json_string: str):
        """
        Send a json string to all connected websockets
        Remove websocket if sending was unsuccessful
        """
        # logger.info(f"Sending websocket data: {json_string}")
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send(json_string)
            except Exception as e:
                # A websocket disconnected - this means an overlay html was closed, or OBS was closed
                # logger.exception("Error trying to broadcast json")
                self.websocket_connections.discard(websocket)

    async def event_message(self, message: TwitchMessage):
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
        New game was detected. This may be a 1v1 game, archon or teamgame or even arcade
        This function is triggered by match_info script
        Useful for scene switcher
        """
        # logger.info("New game detected")
        for script in self.running_scripts:
            await script.on_new_game(match_info)

    async def on_new_game_with_players(self, match_info: MatchInfo):
        """
        New game was detected where the streamer was found (must be 1v1 game). This is the earliest detection possible that has info about opponent (name, race), but not mmr available yet.
        This function is triggered by match_info script
        Useful for build order overlay
        """
        for script in self.running_scripts:
            await script.on_new_game_with_players(match_info)

    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        """
        New game was detected. This is the earliest detection possible that has info about opponent (name, race, mmr)
        This function is triggered by match_info script
        Useful for match info overlay
        """
        # logger.info("New game detected, mmr ready")
        for script in self.running_scripts:
            await script.on_new_game_with_mmr(match_info)

    async def on_game_ended(self, match_info: MatchInfo):
        """
        The SC2 game has ended, either the streamer is now in menu, replay or loading screen. This is useful for the betting script to check when the betting is over.
        This function is triggered by match_info script
        """
        # logger.info("Game end detected (either replay started (rewind), or streamer is now in menu)")
        for script in self.running_scripts:
            await script.on_game_ended(match_info)

    async def on_rewind(self, match_info: MatchInfo):
        for script in self.running_scripts:
            await script.on_rewind(match_info)

    async def on_replay_entered(self, match_info: MatchInfo):
        for script in self.running_scripts:
            await script.on_replay_entered(match_info)

    async def on_game_resumed_from_replay(self, match_info: MatchInfo):
        for script in self.running_scripts:
            await script.on_game_resumed_from_replay(match_info)

    # Commands use a different decorator
    @commands.command(name="test")
    async def my_command(self, ctx: TwitchContext):
        channel: TwitchChannel = ctx.channel
        user: TwitchUser = ctx.author
        message: TwitchMessage = ctx.message
        content: str = ctx.content
        """
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
        """
        chatters: TwitchChatters = await self.get_chatters(ctx.channel.name)
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command(name="test2")
    async def my_command2(self, ctx: TwitchContext):
        await ctx.send(f"Hello2 {ctx.author.name}!")


if __name__ == "__main__":
    # Load token from twitch irc token config file
    token_file_path = Path(__file__).parent / "config" / "twitch_irc_token.json"
    with open(token_file_path) as f:
        token_file_json = json.load(f)
        token = token_file_json["token"]

    # Start bot
    bot = TwitchChatBot(irc_token=token)
    bot.run()
