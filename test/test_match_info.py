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
        self.websocket_broadcast_called = 0

    async def on_new_game(self, match_info: MatchInfo):
        self.new_game_called += 1

    async def on_new_game_with_mmr(self, match_info: MatchInfo):
        self.new_game_with_mmr_called += 1

    async def on_game_ended(self, match_info: MatchInfo):
        self.game_ended_called += 1

    async def on_rewind(self, match_info: MatchInfo):
        pass

    async def websocket_broadcast_json(self, payload: str):
        self.websocket_broadcast_called += 1


menu_game_data = {
    "isReplay": False,
    "displayTime": 4.0,
    "players": [
        {"id": 1, "name": "BuRny", "type": "user", "race": "Prot", "result": "Undecided"},
        {"id": 2, "name": "A.I. 1 (Very Easy)", "type": "computer", "race": "random", "result": "Undecided"},
    ],
}
menu_ui_data = {
    "activeScreens": [
        "ScreenBackgroundSC2/ScreenBackgroundSC2",
        "ScreenNavigationSC2/ScreenNavigationSC2",
        "ScreenForegroundSC2/ScreenForegroundSC2",
        "ScreenMultiplayer/ScreenMultiplayer",
    ]
}

game_game_data = {
    "isReplay": False,
    "displayTime": 4.0,
    "players": [
        {"id": 1, "name": "BuRny", "type": "user", "race": "Prot", "result": "Undecided"},
        {"id": 2, "name": "A.I. 1 (Very Easy)", "type": "computer", "race": "random", "result": "Undecided"},
    ],
}
game_ui_data = {"activeScreens": []}

replay_game_data = {
    "isReplay": True,
    "displayTime": 4.0,
    "players": [
        {"id": 1, "name": "BuRny", "type": "user", "race": "Prot", "result": "Undecided"},
        {"id": 2, "name": "A.I. 1 (Very Easy)", "type": "computer", "race": "random", "result": "Undecided"},
    ],
}
replay_ui_data = {"activeScreens": []}


@pytest.mark.asyncio
async def test_match_info_menu():
    fake_bot = FakeBot()
    match_info = MatchInfo(bot=fake_bot)

    # Emulate menu state
    async def get_ui_data():
        return menu_ui_data

    async def get_game_data():
        return menu_game_data

    match_info.get_ui_data = get_ui_data
    match_info.get_game_data = get_game_data

    # Try to detect if a new game was started
    await match_info.update_variables()

    # Check if variables changed properly
    assert match_info.game_location == "menu"
    assert match_info.bot.new_game_called == 0
    assert match_info.bot.new_game_with_mmr_called == 0
    assert match_info.bot.game_ended_called == 0
    assert match_info.bot.websocket_broadcast_called == 0
    assert match_info.new_game_started is False
    assert match_info.valid_game is False
    assert match_info.end_of_game_detected is False


@pytest.mark.asyncio
async def test_match_info_menu_to_game():
    fake_bot = FakeBot()
    match_info = MatchInfo(bot=fake_bot)
    match_info.DEBUG_MODE = True

    # Emulate menu state
    async def get_game_data():
        return game_game_data

    async def get_ui_data():
        return game_ui_data

    match_info.get_game_data = get_game_data
    match_info.get_ui_data = get_ui_data

    # Try to detect if a new game was started
    await match_info.update_variables()

    # Check that functions were called properly
    assert match_info.game_location == "game"
    assert match_info.bot.new_game_called == 1
    assert match_info.bot.new_game_with_mmr_called == 1
    assert match_info.bot.game_ended_called == 0
    # After the MMR was gathered, the info will be sent via websockets to the overlay
    assert match_info.bot.websocket_broadcast_called == 1
    assert match_info.new_game_started is True
    assert match_info.valid_game is True
    assert match_info.end_of_game_detected is False


@pytest.mark.asyncio
async def test_match_info_game_to_replay():
    fake_bot = FakeBot()
    match_info = MatchInfo(bot=fake_bot)
    match_info.DEBUG_MODE = True

    # Emulate menu state
    match_info.game_location = "game"

    async def get_game_data():
        return replay_game_data

    async def get_ui_data():
        return replay_ui_data

    match_info.get_game_data = get_game_data
    match_info.get_ui_data = get_ui_data

    # Try to detect if a new game was started
    await match_info.update_variables()

    # Check that functions were called properly
    assert match_info.game_location == "replay"
    assert match_info.bot.new_game_called == 0
    assert match_info.bot.new_game_with_mmr_called == 0
    assert match_info.bot.game_ended_called == 0
    assert match_info.bot.websocket_broadcast_called == 0
    assert match_info.new_game_started is False
    assert match_info.valid_game is False
    assert match_info.end_of_game_detected is False


@pytest.mark.asyncio
async def test_match_info_game_to_menu():
    fake_bot = FakeBot()
    match_info = MatchInfo(bot=fake_bot)
    match_info.DEBUG_MODE = True

    # Emulate game state
    match_info.game_location = "game"

    async def get_game_data():
        return menu_game_data

    async def get_ui_data():
        return menu_ui_data

    match_info.get_game_data = get_game_data
    match_info.get_ui_data = get_ui_data

    # Try to detect if a new game was started
    await match_info.update_variables()

    # Check that functions were called properly
    assert match_info.game_location == "menu"
    assert match_info.bot.new_game_called == 0
    assert match_info.bot.new_game_with_mmr_called == 0
    assert match_info.bot.game_ended_called == 1
    assert match_info.bot.websocket_broadcast_called == 0
    assert match_info.new_game_started is False
    assert match_info.valid_game is False
    assert match_info.end_of_game_detected is True
