from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import datetime
import random
import websockets
import aiohttp
import time
import json
import os

import logging
logger = logging.getLogger(__name__)

# os.path.dirname(__file__)

if TYPE_CHECKING:
    from bot import TwitchChatBot


class MatchInfo:
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot

        self.p1name = ""
        self.p1race = ""
        self.p1mmr = ""
        self.p1mmr_string = ""

        self.p2name = ""
        self.p2race = ""
        self.p2mmr = ""
        self.p2mmr_string = ""
        self.p2stream = ""

        self.game_data = {}
        self.ui_data = {}

        self.time_now = 0
        self.time_offset = -60 * 60 * 7

        self.filter_age = 14 * 24 * 60 * 60 * 1000
        self.sort_by = "most recent"

        self.new_game_started = False
        # TODO detect when entering main menu to clear opponent mmr race name
        self.end_of_game_detected = False
        self.valid_game = False

        # One of: menu, game, replay, ""
        self.game_location = "menu"
        self.past_game_location = ""

        self.gaming_pc_address = "localhost"

        self.race_dict = {"r": "Random", "t": "Terran", "p": "Protoss", "z": "Zerg"}
        self.server_dict = {"": "", "us": "Americas", "eu": "Europe", "kr": "Asia"}

        self._session: aiohttp.ClientSession = None
        self.users = set()

        # FROM CONFIG FILE:
        self.user_names = ["BuRny"]
        self.server = "eu"
        self.DEBUG_MODE = True

    @property
    def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    def load_config(self):
        path = os.path.dirname(__file__)
        config_file_path = os.path.join(path, "config.json")
        with open(config_file_path) as f:
            settings = json.load(f)
            self.user_names = settings["accounts"]
            self.server = settings["server"]

    def reset_values(self):
        self.p1mmr = ""
        self.p1race = ""
        self.p1mmr = ""
        self.p1mmr_string = ""

        self.p2name = ""
        self.p2race = ""
        self.p2mmr = ""
        self.p2mmr_string = ""
        self.p2stream = ""

        self.new_game_started = False

    async def get_game_data(self):
        """
        Returns the json of the sc2 client API game data

        Example return value:
        {
          "isReplay": false,
          "displayTime": 4.0,
          "players": [
            {
              "id": 1,
              "name": "BuRny",
              "type": "user",
              "race": "Prot",
              "result": "Undecided"
            },
            {
              "id": 2,
              "name": "A.I. 1 (Very Easy)",
              "type": "computer",
              "race": "random",
              "result": "Undecided"
            }
          ]
        }
        """
        url = f"http://{self.gaming_pc_address}:6119/game"
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return {}
                assert resp.status == 200
                resp_json = await resp.json()
                return resp_json
        except aiohttp.ClientConnectorError:
            print("Error, SC2 is not running.")
            return {}

    async def get_ui_data(self):
        """
        Returns the json of the sc2 client API ui data
        One of the following:

        {
          "activeScreens": [

          ]
        }

        {
          "activeScreens": [
            "ScreenBackgroundSC2/ScreenBackgroundSC2",
            "ScreenNavigationSC2/ScreenNavigationSC2",
            "ScreenForegroundSC2/ScreenForegroundSC2",
            "ScreenScore/ScreenScore",
            "ScreenCustom/ScreenCustom"
          ]
        }

        {
        "activeScreens": [
            "ScreenBackgroundSC2/ScreenBackgroundSC2",
            "ScreenNavigationSC2/ScreenNavigationSC2",
            "ScreenForegroundSC2/ScreenForegroundSC2",
            "ScreenMultiplayer/ScreenMultiplayer"
          ]
        }
        """
        url = f"http://{self.gaming_pc_address}:6119/ui"
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return {}
                assert resp.status == 200
                resp_json = await resp.json()
                return resp_json
        except aiohttp.ClientConnectorError:
            print("Error, SC2 is not running.")
            return {}

    def detect_new_game_started(self):
        # Need to detect when a new game started, and when one ended (streamer in menu, replay, not resume from replay)
        self.past_game_location = self.game_location

        self.new_game_started = False
        self.valid_game = False
        self.end_of_game_detected = False

        # Check current location in sc2
        in_game_or_replay = self.ui_data["activeScreens"] == []
        in_replay = self.game_data["isReplay"]
        in_menu = self.ui_data["activeScreens"] != []

        # Determine current location
        if in_menu:
            self.game_location = "menu"
        elif in_game_or_replay and not in_replay:
            self.game_location = "game"
        elif in_game_or_replay and in_replay:
            self.game_location = "replay"

        # Check if new game was started
        past_loc_was_menu = self.past_game_location == "menu"
        new_loc_is_game = self.game_location == "game"
        print(f"Previous location was {self.past_game_location}")
        print(f"Current location is {self.game_location}")
        if past_loc_was_menu and new_loc_is_game:
            self.new_game_started = True
            # Validate game afterwards
            self.valid_game = True

        # Check if game has ended, if the previous location was game, and new location is replay or menu
        past_loc_was_game = self.past_game_location == "game"
        new_loc_is_not_game = self.game_location != "game"
        if past_loc_was_game and new_loc_is_not_game:
            self.end_of_game_detected = True

    def validate_data(self):
        # Invalid when:
        # Player number is unequal to two
        # When one of the players is computer
        # When both players have the same name
        # When player name was not found in user_names array
        if len(self.game_data["players"]) != 2:
            print("Invalid game because number of players is not equal to 2")
            self.valid_game = False
            return

        player1_name = self.game_data["players"][0]["name"]
        player2_name = self.game_data["players"][1]["name"]
        if player1_name == player2_name:
            print("Invalid game because player 1 name is equal to player 2 name")
            self.valid_game = False
            return

        if not self.DEBUG_MODE and any(
            True for player_data in self.game_data["players"] if player_data["type"] != "user"
        ):
            self.valid_game = False
            return

        # Set game time for build order scripts
        self.game_time = self.game_data["displayTime"]

        # Set p1name and p2name variables
        player1_race = self.game_data["players"][0]["race"]
        player2_race = self.game_data["players"][1]["race"]
        self.p1name = player1_name
        self.p2name = player2_name
        self.p1race = player1_race[0].lower()
        self.p2race = player2_race[0].lower()

        # Invalidate if p1name or p2name is not in user_names
        streamer_found = False
        for name in self.user_names:
            if player1_name == name:
                streamer_found = True
                break
            elif player2_name == name:
                streamer_found = True
                # Swap names and races if name was found in player2 name
                self.p1name, self.p2name = self.p2name, self.p1name
                self.p1race, self.p2race = self.p2race, self.p1race
                break
        if not streamer_found:
            self.valid_game = False
            print(
                "Invalid game because streamer could not be found. player 1 or player 2 are not in the list of account names"
            )
            return

    async def get_unmasked_response(self, name, race, server):
        url = f"http://sc2unmasked.com/API/Player?name={name}&race={race}&server={server}"
        print(f"Sc2unmasked url: {url}")
        async with self.session.get(url) as resp:
            assert resp.status == 200
            resp_json = await resp.json()
            return resp_json

    def convert_player_info_to_last_player(self, player_info: dict) -> int:
        """ Returns time in seconds """
        # TODO: can be None, needs to return 0 in that case?
        return int(player_info["last_played"][6:-2]) // 1000

    async def get_player1_mmr(self):
        """
        Not case sensitive, and finds displayname equal to burny:
        http://sc2unmasked.com/API/Player?q=burny
        Find matches equal to streamer name:
        http://sc2unmasked.com/API/Player?q=twitch.tv/burnysc2
        Case sensitive, finds exact matches, best for this probably:
        http://sc2unmasked.com/API/Player?name=BuRny

        Example response:
        {
          "players": [
            {
              "division": 216346,
              "server": "eu",
              "rank": 792,
              "race": "t",
              "lvl": "150",
              "portrait_name": "",
              "last_played": "\/Date(1559441390000)\/",
              "divName": "Zealot Rho",
              "tier": 1,
              "league": "master",
              "league_id": 2,
              "mmr": 5206,
              "points": 579,
              "ach_pts": 10220,
              "wins": 18,
              "losses": 21,
              "clan_tag": "Zelos",
              "acc_name": "BuRny",
              "ggtracker": null,
              "replaystats": "1162440",
              "overwatch": null,
              "acc_id": "727565/1",
              "game_link": "2/14004507099363540992",
              "display_name": "BuRny",
              "aligulac": 11945,
              "note": null,
              "description": null,
              "platform": "twitch.tv",
              "stream_name": "burnysc2",
              "game": "",
              "is_online": false,
              "title": "4v4 Teamgames",
              "preview_img": "https://static-cdn.jtvnw.net/previews-ttv/live_user_burnysc2-640x360.jpg",
              "last_online": "\/Date(1562559805020)\/",
              "viewers": 0,
              "mode": "SOLO"
            },
          ]
        }
        """
        # Set current time to sc2unmasked timezone
        self.time_now = time.time() + self.time_offset

        # player1 is now the streamer, so get the mmr of it first
        # Use configurated server if it was set, to get better results

        # Example url: http://sc2unmasked.com/API/Player?name=BuRny&race=T&server=eu
        # let url = "http://sc2unmasked.com/API/Player?" + $.param({name: p1name, race: p1race.substring(0, 1), server: server});

        unmasked_response = await self.get_unmasked_response(self.p1name, self.p1race, self.server)
        print("Sc2unmasked response:", json.dumps(unmasked_response, indent=4))

        players = unmasked_response["players"]
        if not players:
            print("No results found for player 1")
            self.p1mmr = "???"
            self.p1mmr_string = "???"
            return

        players_sorted = sorted(players, key=lambda u: -self.convert_player_info_to_last_player(u))

        one_hour = 60 * 60
        players_filtered = [
            player
            for player in players_sorted
            if self.time_now - self.convert_player_info_to_last_player(player) < one_hour
        ]

        streamer_info = players_sorted[0]
        self.p1mmr = str(streamer_info["mmr"])
        self.p1mmr_string = self.p1mmr
        # More than one player was found that was playing with same name and race in the last hour, so mmr might be uncertain
        more_than_one_player_match = len(players_filtered) > 1
        _24_hours = 60 * 60 * 24

        # Streamer didnt play in 24h so match and mmr might be inaccurate
        streamer_didnt_play_in_more_than_24h = (
            self.time_now - self.convert_player_info_to_last_player(streamer_info) > _24_hours
        )
        print(self.time_now)
        print(self.convert_player_info_to_last_player(streamer_info))
        print(
            f"Last game of streamer was {(self.time_now - self.convert_player_info_to_last_player(streamer_info)) / (60)} mins ago"
        )
        if more_than_one_player_match or streamer_didnt_play_in_more_than_24h:
            self.p1mmr_string += "?"

    async def get_player2_mmr(self):

        unmasked_response = await self.get_unmasked_response(self.p2name, self.p2race, self.server)
        # unmasked_response = await self.get_unmasked_response("saixy", "t", self.server)

        players = unmasked_response["players"]
        if not players:
            print("No results found for player 2")
            self.p2mmr = "???"
            self.p2mmr_string = "???"
            return

        # Filter opponents by age of last player (14 days)
        players_filtered = [
            player
            for player in players
            if self.time_now - self.convert_player_info_to_last_player(player) < self.filter_age
        ]

        # Sort by mmr difference to player 1 mmr
        players_sorted = sorted(players_filtered, key=lambda u: abs(u["mmr"] - int(self.p1mmr)))

        most_recent = players_sorted[0]
        self.p2mmr = str(most_recent["mmr"])
        self.p2mmr_string = self.p2mmr

        more_than_one_result_found = len(players_sorted) > 1
        if more_than_one_result_found:
            self.p2mmr_string += "?"

        # Find opponent stream if he has a stream and his stream is online and on twitch
        if most_recent["is_online"] and most_recent["platform"] == "twitch.tv":
            self.p2stream = most_recent["stream_name"]

    async def prepare_payload(self) -> dict:
        payload = {
            "p1name": self.p1name,
            "p2name": self.p2name,
            "p1race": self.race_dict[self.p1race],
            "p2race": self.race_dict[self.p2race],
            "p1mmr": self.p1mmr_string,
            "p2mmr": self.p2mmr_string,
            "p2stream": self.p2stream,
            "server": self.server_dict[self.server],
        }
        return payload

    async def send_data_to_html(self, websocket: websockets.WebSocketServer):
        payload = await self.prepare_payload()
        # print(f"Payload: {json.dumps(payload, indent=4)}")
        payload_string = json.dumps(payload)
        self.users.add(websocket)
        for user in self.users.copy():
            try:
                await user.send(payload_string)
            except Exception as e:
                # Connection error with websocket, close it
                self.users.discard(websocket)

    async def websocket_server_loop(self, websocket, path):
        """ Each new websocket connection will start this function, so when the websocket connection closes, this function has to return. """
        while 1:
            print("Updating variables")
            await self.update_variables(websocket)
            await asyncio.sleep(1)
            if websocket.closed:
                # Close websocket connection if connection was closed
                return

    async def update_variables(self, websocket=None):
        self.ui_data = await self.get_ui_data()
        self.game_data = await self.get_game_data()

        if self.ui_data == {} or self.game_data == {}:
            print("Early return, no connection to SC2 Client")
            return

        self.detect_new_game_started()
        if self.end_of_game_detected and self.bot is not None:
            print("End of game detected!")
            await self.bot.on_game_ended(self)

        if not self.new_game_started:
            # print(f"Early return - {time.time()}")
            # Send the data to all websockets again, to newly connected as well as old ones
            if self.p1mmr.isnumeric():
                await self.send_data_to_html(websocket)
            return

        # Reset the data before checking and converting it, and grabbing new mmr
        self.reset_values()

        print("New game start detected")
        # Validate API data: has to have only 2 players, both need to be users and both cannot have the exact same name
        self.validate_data()

        if self.valid_game:
            if self.bot is not None:
                await self.bot.on_new_game(self)

            print("Valid game found")
            print(f"Grabbing mmr of player1: {self.p1name} ({self.p1race})")
            await self.get_player1_mmr()
            print(f"Grabbed mmr of player1: {self.p1mmr} | {self.p1mmr_string}")

            if self.p1mmr.isnumeric():
                print(f"Grabbing mmr of player2: {self.p2name} ({self.p2race})")
                try:
                    await self.get_player2_mmr()
                    print(f"Grabbed mmr of player2: {self.p2mmr} | {self.p2mmr_string}")
                except aiohttp.ContentTypeError:
                    print("Could not grab mmr of player2, aiohttp error.")

            if self.bot is not None:
                await self.bot.on_new_game_with_mmr(self)
            await self.send_data_to_html(websocket)


def main():
    match_info = MatchInfo()
    match_info.load_config()
    print("Script started")
    start_server = websockets.serve(match_info.websocket_server_loop, "127.0.0.1", 5678)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
