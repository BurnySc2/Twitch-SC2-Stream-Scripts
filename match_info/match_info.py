from __future__ import annotations
from typing import TYPE_CHECKING, Dict

import asyncio
import websockets
import aiohttp
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin

from typing import List, Dict, Optional

from loguru import logger

from plugin_base_class.base_class import BaseScript

if TYPE_CHECKING:
    from bot import TwitchChatBot


@dataclass()
class MatchInfoConfig(DataClassJsonMixin):
    accounts: List[str] = field(default_factory=lambda: [])
    # One of: US, EU, KR
    server: str = "eu"


@dataclass()
class PlayerInfo:
    realm: int
    # One of EU, US, KR
    region: str
    # One of "Grandmaster", "Master", "Diamond"
    rank: str
    # "BuRny"
    username: str
    # Full battle tag id, Burny#2396
    bnet_id: str
    # One of "Terran" "Protoss" "Zerg" "Random"
    race: str
    mmr: int
    wins: int
    losses: int
    clan: Optional[str]
    profile_id: int
    alias: Optional[str]

    @staticmethod
    def from_sc2_unmasked(data: dict) -> PlayerInfo:
        pass

    @staticmethod
    def from_sc2_ladder(data: dict) -> PlayerInfo:
        """
        Input example:
        [
          {
            "realm": "1",
            "region": "EU",
            "rank": "Master",
            "username": "BuRny",
            "bnet_id": "Burny#2396",
            "race": "Terran",
            "mmr": 4948,
            "wins": 1,
            "losses": 0,
            "clan": "Zelos",
            "profile_id": 727565,
            "alias": "BuRny"
          },
        ]
        """
        logger.info(data)
        return PlayerInfo(
            realm=data["realm"],
            region=data["region"],
            rank=data["rank"],
            username=data["username"],
            bnet_id=data["bnet_id"],
            race=data["race"],
            mmr=data["mmr"],
            wins=data["wins"],
            losses=data["losses"],
            clan=data["clan"],
            profile_id=data["profile_id"],
            alias=data["alias"],
        )


class MatchInfo(BaseScript):
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot

        self.p1name = ""
        # One of: Terran, Protoss, Zerg, Random
        self.p1race = ""
        self.p1mmr = ""
        self.p1mmr_string = ""

        self.p2name = ""
        # One of: Terran, Protoss, Zerg, Random
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

        self.valid_game = False
        self.new_game_started = False
        # TODO detect when entering main menu to clear opponent mmr race name
        self.end_of_game_detected = False
        self.rewind_detected = False
        self.replay_detected = False
        self.resume_from_replay_detected = False

        # One of: menu, game, replay, ""
        self.game_location = "menu"
        self.past_game_location = ""

        self.gaming_pc_address = "localhost"

        self.race_dict = {"r": "Random", "t": "Terran", "p": "Protoss", "z": "Zerg"}
        self.server_dict = {"": "", "us": "Americas", "eu": "Europe", "kr": "Asia"}

        self._session: aiohttp.ClientSession = None
        self.users = set()

        # FROM CONFIG FILE:
        config_file_path = Path(__file__).parent / "config.json"
        with config_file_path.open() as f:
            self.config: MatchInfoConfig = MatchInfoConfig.from_json(f.read())
            assert self.config.server in {"", "eu", "us", "kr"}, f"Current value is: {self.config.server}"
        # Enable if you want to test if script is working vs AI
        self.DEBUG_MODE = True

    @property
    def session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    def reset_values(self):
        self.p1race = ""
        self.p1mmr = ""
        self.p1mmr_string = ""

        self.p2name = ""
        self.p2race = ""
        self.p2mmr = ""
        self.p2mmr_string = ""
        self.p2stream = ""

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
            logger.debug("Error, SC2 is not running.")
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
            logger.debug("Error, SC2 is not running.")
            return {}

    def detect_new_game_started(self):
        # Need to detect when a new game started, and when one ended (streamer in menu, replay, not resume from replay)
        self.past_game_location = self.game_location

        self.valid_game = False
        self.new_game_started = False
        self.end_of_game_detected = False
        self.rewind_detected = False
        self.replay_detected = False
        self.resume_from_replay_detected = False

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

        # logger.info(self.game_data)
        # logger.info(self.ui_data)

        # Check if new game was started
        past_loc_was_menu = self.past_game_location == "menu"
        new_loc_is_game = self.game_location == "game"

        if past_loc_was_menu and new_loc_is_game:
            self.new_game_started = True
            # Validate game afterwards
            self.valid_game = True

        # Check if game has ended, if the previous location was game, and new location is replay or menu
        past_loc_was_game = self.past_game_location == "game"
        new_loc_is_menu = self.game_location == "menu"
        past_loc_was_replay = self.past_game_location == "replay"
        if (past_loc_was_game or past_loc_was_replay) and new_loc_is_menu:
            self.end_of_game_detected = True

        # Check if rewind was used: previous location was game and current location is replay
        new_loc_is_replay = self.game_location == "replay"
        if past_loc_was_game and new_loc_is_replay:
            self.rewind_detected = True

        # Check if streamer joined replay: previous location was menu and current location is replay
        if past_loc_was_menu and new_loc_is_replay:
            self.replay_detected = True

        # Check if streamer resumed from replay: previous location was replay and current location is game
        if past_loc_was_replay and new_loc_is_game:
            self.resume_from_replay_detected = True

    def validate_data(self):
        # Invalid when:
        # Player number is unequal to two
        # Game is a replay
        # When one of the players is computer
        # When both players have the same name
        # When player name was not found in accounts array
        if len(self.game_data["players"]) != 2:
            logger.info("Invalid game because number of players is not equal to 2")
            self.valid_game = False
            return

        if self.game_data["isReplay"]:
            logger.info("Invalid game because this is a replay, not a live game")
            self.valid_game = False
            return

        # Enable play vs AI if debug mode is on
        if not self.DEBUG_MODE and any(player["type"] == "computer" for player in self.game_data["players"]):
            logger.info("Invalid game because it has at least one AI in it")
            self.valid_game = False
            return

        player1_name = self.game_data["players"][0]["name"]
        player2_name = self.game_data["players"][1]["name"]
        if player1_name == player2_name:
            logger.info("Invalid game because player 1 name is equal to player 2 name")
            self.valid_game = False
            return

        # if (
        #     not self.DEBUG_MODE
        #     and len([True for player_data in self.game_data["players"] if player_data["type"] != "user"]) == 0
        # ):
        #     self.valid_game = False
        #     return

        # Set p1name and p2name variables
        player1_race = self.game_data["players"][0]["race"]
        player2_race = self.game_data["players"][1]["race"]
        self.p1name = player1_name
        self.p2name = player2_name
        # Convert "p" to "Protoss" etc
        self.p1race = self.race_dict[player1_race[0].lower()[0]]
        self.p2race = self.race_dict[player2_race[0].lower()[0]]

        # Invalidate if p1name or p2name is not in accounts
        streamer_found = False
        for name in self.config.accounts:
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
            logger.info(
                "Invalid game because streamer could not be found. player 1 or player 2 are not in the list of account names"
            )
            return

        # async def get_unmasked_response(self, name, race, server) -> List[PlayerInfo]:
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

    #     url = f"http://sc2unmasked.com/API/Player?name={name}&race={race}&server={server}"
    #     logger.info(f"Sc2unmasked url: {url}")
    #     async with self.session.get(url) as resp:
    #         assert resp.status == 200
    #         resp_json = await resp.json()
    #         return [PlayerInfo.from_sc2_unmasked(data) for data in resp_json]

    async def get_sc2_ladder_response(self, name, race, server) -> List[PlayerInfo]:
        """
        name: user name in loading scren
        race: one of "Terran", "Protoss", "Zerg", "Random"
        server: one of "US", "EU", "KR"
        """
        url = f"https://www.sc2ladder.herokuapp.com/api/player?name={name}&race={race}&region={server}"
        # url = f"https://www.sc2ladder.com/api/player?name={name}&race={race}&region={server}"
        logger.info(f"sc2ladder url: {url}")
        try:
            async with self.session.get(url) as resp:
                assert resp.status == 200
                resp_json = await resp.json()
                return [PlayerInfo.from_sc2_ladder(data) for data in resp_json]
        except aiohttp.ClientConnectorError:
            logger.info(f"Could not connect to www.sc2ladder.com")
            return []

    async def get_player1_mmr(self):
        # Set current time to sc2unmasked timezone
        self.time_now = time.time() + self.time_offset

        # player1 is now the streamer, so get the mmr of it first
        # Use configurated server if it was set, to get better results

        # Example url: http://sc2unmasked.com/API/Player?name=BuRny&race=T&server=eu
        # Example url: http://sc2ladder.com/API/player?name=BuRny&race=Terran&server=eu
        # let url = "http://sc2unmasked.com/API/Player?" + $.param({name: p1name, race: p1race.substring(0, 1), server: server});

        players = await self.get_sc2_ladder_response(self.p1name, self.p1race, self.config.server)
        logger.info("sc2ladder.com response:")
        for p in players:
            logger.info(p)

        if not players:
            logger.info("No results found for player 1")
            self.p1mmr = "???"
            self.p1mmr_string = "???"
            return

        streamer_info = players[0]
        self.p1mmr = str(streamer_info.mmr)
        self.p1mmr_string = self.p1mmr
        # TODO Append question mark if the mmr might be unreliable, e.g. multiple results, or wasnt played on that account for a while
        if len(players) > 1:
            self.p1mmr_string += "?"

    async def get_player2_mmr(self):
        players = await self.get_sc2_ladder_response(self.p2name, self.p2race, self.config.server)

        if not players:
            logger.info("No results found for player 2")
            self.p2mmr = "???"
            self.p2mmr_string = "???"
            return

        # TODO Filter opponents by age of last player (14 days)

        # Sort by mmr difference to player 1 mmr
        players_sorted = sorted(players, key=lambda u: abs(u.mmr - int(self.p1mmr)))

        most_recent = players_sorted[0]
        self.p2mmr = str(most_recent.mmr)
        self.p2mmr_string = self.p2mmr

        if len(players_sorted) > 1:
            self.p2mmr_string += "?"

        # TODO Find opponent stream if he has a stream and his stream is online and on twitch
        # if most_recent["is_online"] and most_recent["platform"] == "twitch.tv":
        #     self.p2stream = most_recent["stream_name"]

    async def prepare_payload(self) -> dict:
        """ Send payload to websocket. """
        payload = {
            "payload_type": "match_info",
            "p1name": self.p1name,
            "p2name": self.p2name,
            "p1race": self.p1race,
            "p2race": self.p2race,
            "p1mmr": self.p1mmr_string,
            "p2mmr": self.p2mmr_string,
            "p2stream": self.p2stream,
            "server": self.server_dict[self.config.server],
        }
        return payload

    async def on_tick(self):
        await self.update_variables()

    async def send_data_to_html(self):
        payload = await self.prepare_payload()
        # logger.info(f"Payload: {json.dumps(payload, indent=4)}")
        payload_string = json.dumps(payload)
        if self.bot is not None:
            await self.bot.websocket_broadcast_json(payload_string)

    async def update_variables(self):
        self.ui_data = await self.get_ui_data()
        self.game_data = await self.get_game_data()

        if self.ui_data == {} or self.game_data == {}:
            logger.debug("Early return, no connection to SC2 Client")
            return

        # Set game time for build order scripts
        self.game_time = self.game_data["displayTime"]

        self.detect_new_game_started()

        assert self.bot is not None
        # Send the data to all websockets again, to newly connected as well as old ones
        if self.p1mmr.isnumeric():
            await self.send_data_to_html()

        if self.new_game_started:
            logger.info("New game start detected")
            # Reset the data before checking and converting it, and then grabbing new mmr
            self.reset_values()

            # Call this function when the streamer enters the game (on loading screen, the api reports that the player is in game)
            await self.bot.on_new_game(self)

            # Validate API data: has to have only 2 players, both need to be users and both cannot have the exact same name
            self.validate_data()
            if self.valid_game:
                logger.info("Valid 1v1 game found")
                await self.bot.on_new_game_with_players(self)
                logger.info(f"Grabbing mmr of player1: {self.p1name} ({self.p1race})")
                await self.get_player1_mmr()
                logger.info(f"Grabbed mmr of player1: {self.p1mmr} | {self.p1mmr_string}")

                if self.p1mmr.isnumeric():
                    logger.info(f"Grabbing mmr of player2: {self.p2name} ({self.p2race})")
                    try:
                        await self.get_player2_mmr()
                        logger.info(f"Grabbed mmr of player2: {self.p2mmr} | {self.p2mmr_string}")
                    except aiohttp.ContentTypeError:
                        logger.exception("Could not grab mmr of player2, aiohttp error.")

                await self.bot.on_new_game_with_mmr(self)
                await self.send_data_to_html()

        elif self.end_of_game_detected:
            logger.info("End of game detected!")
            await self.bot.on_game_ended(self)

        elif self.rewind_detected:
            logger.info("Rewind to replay detected!")
            await self.bot.on_rewind(self)

        elif self.replay_detected:
            logger.info("A replay was entered from menu!")
            await self.bot.on_replay_entered(self)

        elif self.resume_from_replay_detected:
            logger.info("Game was resumed from replay!")
            await self.bot.on_game_resumed_from_replay(self)


def main():
    match_info = MatchInfo()
    logger.info("Script started")
    start_server = websockets.serve(match_info.websocket_server_loop, "127.0.0.1", 5678)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
