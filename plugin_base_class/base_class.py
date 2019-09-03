from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from match_info.match_info import MatchInfo

class BaseScript:
    """
    The following functions need to be implemented as they will be called by bot.py
    """
    async def on_ready(self):
        pass
    async def on_tick(self):
        pass
    async def on_new_game(self, match_info: MatchInfo):
        pass
    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        pass
    async def on_game_ended(self, match_info: MatchInfo):
        pass