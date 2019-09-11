import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from match_info.match_info import MatchInfo

import pytest


class FakeBot:
    def __init__(self):
        self.match_info: MatchInfo = None

        self.new_game_called = 0
        self.new_game_with_mmr_called = 0
        self.game_ended_called = 0

    async def on_new_game(self):
        self.new_game_called += 1

    async def on_new_game_with_mmr(self):
        self.new_game_with_mmr_called += 1

    async def on_game_ended(self):
        self.game_ended_called += 1


menu_game_data = {}
menu_ui_data = {}

game_game_data = {}
game_ui_data = {}

replay_game_data = {}
replay_ui_data = {}


@pytest.mark.asyncio
async def test_build_order():
    pass
