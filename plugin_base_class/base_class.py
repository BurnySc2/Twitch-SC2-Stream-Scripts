from __future__ import annotations
from typing import TYPE_CHECKING

from twitchio.dataclasses import User as TwitchUser
from twitchio.dataclasses import Channel as TwitchChannel
from twitchio.dataclasses import Message as TwitchMessage
from twitchio.dataclasses import Context as TwitchContext


if TYPE_CHECKING:
    from match_info.match_info import MatchInfo


class BaseScript:
    """
    The following functions need to be implemented as they will be called by bot.py
    """

    async def on_ready(self):
        pass

    async def on_new_websocket_connection(self):
        pass

    async def on_message(self, message: TwitchMessage):
        pass

    async def on_tick(self):
        pass

    async def on_new_game(self, match_info: MatchInfo):
        """ Event: streamer loaded from menu to any game mode: 1v1, teamgame, arcade, coop, replay """
        pass

    async def on_new_game_with_players(self, match_info: MatchInfo):
        """ Event: streamer loaded from menu to 1v1: player names were found, but no MMR data is available yet """
        pass

    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        """ Event: streamer loaded from menu to 1v1 """
        pass

    async def on_rewind(self, match_info: MatchInfo):
        pass

    async def on_replay_entered(self, match_info: MatchInfo):
        pass

    async def on_game_resumed_from_replay(self, match_info: MatchInfo):
        pass

    async def on_game_ended(self, match_info: MatchInfo):
        pass

    async def send_message(self, message: str):
        channel: TwitchChannel = self.bot.main_channel
        await channel.send(message)
