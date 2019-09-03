
# https://twitchio.readthedocs.io/en/rewrite/twitchio.html
from twitchio.ext import commands
from twitchio import Message

import websockets

import asyncio
import time
import os
import json

from match_info.match_info import MatchInfo


import logging
logger = logging.getLogger(__name__)


"""
bot client properties and functions
coroutine: create_clip(token: str, broadcaster_id: Union[str, int])
coroutine: get_chatters(channel: str) {
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
        main_channel = "burnysc2"
        super().__init__(irc_token=irc_token, client_id="...", nick="burnysc2bot", prefix="!", initial_channels=initial_channels + [main_channel])

        # Start scripts

        # Matchinfo script
        self.match_info = MatchInfo(self)
        self.match_info.load_config()
        self.match_info_server = websockets.serve(self.match_info.websocket_server_loop, "127.0.0.1", 5678)

    # Events don't need decorators when subclassed
    async def event_ready(self):
        """
        Function is called on bot start when it is connected to twitch channels and ready
        """
        print(f"Ready | {self.nick}")

        # Create the match_info task non blocking, which loops over "self.match_info.websocket_server_loop"
        await self.match_info_server

        while 1:
            await self.on_tick()
            await asyncio.sleep(1)

    async def event_message(self, message: Message):
        """
        Function that is run every time the bot sees a new message from one of the connected channels
        """
        print(message.content)
        await self.handle_commands(message)

    async def on_tick(self):
        """
        Function that is run every second
        This function is triggered by bot.event_ready()
        """
        # print(f"Running tick")

    async def on_new_game(self, match_info: MatchInfo):
        """
        New game was detected. This is the earliest detection possible that has info about opponent (name, race), but not mmr available yet.
        This function is triggered by match_info script
        """
        print("New game detected")

    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        """
        New game was detected. This is the earliest detection possible that has info about opponent (name, race, mmr)
        This function is triggered by match_info script
        """
        print("New game detected, mmr ready")

    async def on_game_ended(self, match_info: MatchInfo):
        """
        The SC2 game has ended, either the streamer is now in menu, replay or loading screen. This is useful for the betting script to check when the betting is over.
        This function is triggered by match_info script
        """
        # TODO not working yet
        print("Game end detected (either replay started (rewind), or streamer is now in menu)")

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
