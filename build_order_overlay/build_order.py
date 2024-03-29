from __future__ import annotations
from typing import TYPE_CHECKING

from twitchio import Message

import time
import json
from pathlib import Path

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin

from typing import Set, Dict, List

from plugin_base_class.base_class import BaseScript

if TYPE_CHECKING:
    from bot import TwitchChatBot
    from match_info.match_info import MatchInfo

from loguru import logger


@dataclass()
class BuildOrderOverlayConfig(DataClassJsonMixin):
    voting_time_duration: int = 30
    build_order_step_fade_animation_in_ms: int = 500
    announce_voted_build_order_in_chat: bool = True
    debug_allow_multiple_votes: bool = False


class BuildOrderOverlay(BaseScript):
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot

        self.build_orders = {
            # Terran
            "TvT": [],
            "TvZ": [],
            "TvP": [],
            # Zerg
            "ZvT": [],
            "ZvZ": [],
            "ZvP": [],
            # Protoss
            "PvT": [],
            "PvZ": [],
            "PvP": [],
        }

        # After how many seconds the overlay is fading out, when the end of BO was reached
        self.config_end_of_bo_fade_out_time = 10

        config_file_path = Path(__file__).parent / "config.json"
        with config_file_path.open() as f:
            self.config: BuildOrderOverlayConfig = BuildOrderOverlayConfig.from_json(f.read())
            # TODO: config_end_of_bo_fade_out_time

        # On tick function only works when a game is running
        self.game_is_running = False
        self.voting_is_running = False

        # On new game variables
        self.build_orders_current_matchup_enabled = []
        # Timestamp of when voting started, so it is shown properly on overlay
        self.voting_started_time = 0

        # All twitch usernames that have already voted in this poll, will reset on game start
        self.user_already_voted: Set[str] = set()
        # Votes dict, e.g. {0: 2, 1: 4}
        self.votes_dict: Dict[int, int] = {}
        self.votes_total_count: int = 0

        # When vote is over or build order was chosen
        """
        Example for chosen_bo: 
        {
            "title": "my_bo_name",
            "enabled": True,
            "matchup": "TvZ,
            "priority": 9,
            "bo": [["supply", "time", "description"], [...same as before]]
        }
        """
        self.chosen_bo = None
        self.current_matchup = ""  # One of: TvP, TvZ etc.
        # Ingame time from match_info
        self.in_game_time = 0
        # Timestamp of when the end of bo was found (ingame time), fade out 10 seconds after end of bo
        self.end_of_bo_found = False
        self.end_of_bo_found_time = 0

    def load_build_orders(self):
        """
        Load build orders from file build_orders.txt
        """
        # Reset build orders
        self.build_orders = {
            # Terran
            "TvT": [],
            "TvZ": [],
            "TvP": [],
            "TvR": [],
            # Zerg
            "ZvT": [],
            "ZvZ": [],
            "ZvP": [],
            "ZvR": [],
            # Protoss
            "PvT": [],
            "PvZ": [],
            "PvP": [],
            "PvR": [],
        }
        build_orders_file_path = Path(__file__).parent / "build_orders.txt"
        if not build_orders_file_path.is_file():
            logger.error(f"Could not find build orders file {build_orders_file_path}")
            return

        # Parse build orders file
        next_line_is: str = ""

        # Dict with info about BO title, matchup, if it is enabled, priority
        bo_dict = {}
        # The build order where each entry is [supply, time, step description]
        bo = []

        # Load the build order file and go through it line by line
        with open(build_orders_file_path) as f:
            for line_number, line in enumerate(f.readlines(), start=1):
                # Remove trailing \n
                line = line.strip()
                if line == "":
                    # Line is empty for readability
                    continue
                # Comment
                elif line.startswith("#"):
                    continue
                elif line.startswith("=="):
                    next_line_is = "title"
                    # Append to build orders if a build order was parsed before reset
                    if bo_dict and bo:
                        assert "matchup" in bo_dict, f"No matchup was given to build order {bo_dict['title']}"
                        matchup = bo_dict["matchup"]
                        assert matchup in self.build_orders, f"Build order matchup '{matchup}' is not valid"
                        # Put build order inside the dict
                        bo_dict["bo"] = bo.copy()
                        self.validate_build_order(bo_dict)
                        self.build_orders[matchup].append(bo_dict.copy())
                    # Reset everything
                    bo.clear()
                    bo_dict.clear()
                elif line.startswith("--"):
                    next_line_is = "setting"
                elif line.startswith("++"):
                    next_line_is = "part_of_bo"
                elif next_line_is == "title":
                    bo_dict["title"] = line

                elif next_line_is == "setting":
                    split_line = line.split(" ")
                    assert (
                        len(split_line) == 2
                    ), f"Build order configuration of build order {bo_dict['title']} is invalid in line number {line_number}"
                    first, second = split_line
                    # Store "enabled", "matchup", "priority"
                    bo_dict[first.lower()] = second

                elif next_line_is == "part_of_bo":
                    split_line = line.split(" ")
                    if ":" in split_line[0]:
                        # BO is of type "min:sec Step-description"
                        # Convert it to type "supply min:sec Step-description"
                        split_line.insert(0, "-1")
                    supply = split_line[0]
                    time = split_line[1]
                    description = " ".join(split_line[2:])
                    bo.append([supply, time, description])

            # Lazy assert, could alternatively also append to build orders here
            assert not bo and not bo_dict, f"File has to end with a line of (==) equal signs"

    def validate_build_order(self, bo_dict: dict):
        """ Validate build order dict, change 'enabled' to a boolean value and 'priority' to integer, check if entered matchup is correct. """
        assert "title" in bo_dict
        bo_title = bo_dict["title"]

        # Check if the enabled value is valid
        assert "enabled" in bo_dict
        enabled_string = bo_dict["enabled"]
        enabled_true_variations = {"true", "1", "y", "yes"}
        enabled_false_variations = {"false", "0", "n", "no"}
        if enabled_string.lower() in enabled_true_variations:
            bo_dict["enabled"] = True
        elif enabled_string.lower() in enabled_false_variations:
            bo_dict["enabled"] = False
        else:
            logger.exception(f"Build order '{bo_title}' does not have a valid 'Enabled' value: {enabled_string}")
            assert False

        # Check if matchup value is valid
        assert "matchup" in bo_dict
        valid_matchups = {matchup.lower() for matchup in self.build_orders.keys()}
        matchup_string = bo_dict["matchup"]
        if matchup_string.lower() in valid_matchups:
            pass
        else:
            logger.exception(f"Build order '{bo_title}' does not have a valid 'Matchup' value: {matchup_string}")
            assert False

        # Optional value
        if "priority" in bo_dict:
            priority_str = bo_dict["priority"]
            try:
                priority = int(priority_str)
                bo_dict["priority"] = priority
            except Exception as e:
                logger.exception(f"Build order '{bo_title}' does not have a valid 'Priority' value: {priority_str}")
                assert False

    def get_step_data_from_bo(self) -> List[str]:
        def convert_time_formatted_to_seconds(time_formatted: str) -> int:
            assert ":" in time_formatted, f"{time_formatted}"
            time_list = time_formatted.split(":")
            assert len(time_list) == 2
            mins, secs = map(int, time_list)
            return mins * 60 + secs

        step0_time = "???"
        step0_info = "???"
        step1_time = "0:00"
        step1_info = "Game Start"

        end_of_bo_found = True
        for index, step in enumerate(self.chosen_bo["bo"]):
            # logger.info(index, self.in_game_time, self.bot.match_info.game_time, step)
            time_str = step[1]
            time_from_bo = convert_time_formatted_to_seconds(time_str)
            step0_time = step1_time
            step0_info = step1_info
            step1_time = step[1]
            step1_info = step[2]
            if self.in_game_time < time_from_bo:
                end_of_bo_found = False
                break

        # End of build order was found, set the next step as current, and mark the end of build order
        if end_of_bo_found:
            self.end_of_bo_found = True
            self.end_of_bo_found_time = self.in_game_time
            step0_time = step1_time
            step0_info = step1_info
            step1_time = ""
            step1_info = "End of BO"

        return [step0_time, step0_info, step1_time, step1_info]

    async def build_order_send_websocket_data(self, websocket_type: str, current_matchup: str = ""):
        if websocket_type == "start_vote":
            # Clear, add_children, change percentage and total unique votes to 0 and time active to 0
            bos = [bo["title"] for bo in self.build_orders_current_matchup_enabled]
            payload = {
                "payload_type": "build_order_vote",
                "vote_type": "start_vote",
                "current_matchup": current_matchup,
                "bos": bos,
            }
            await self.bot.websocket_broadcast_json(json.dumps(payload))

        elif websocket_type == "update_vote":
            # Update vote percentages, total unique votes, and time active
            sorted_keys = sorted(self.votes_dict.keys())
            percentages = ["0%" for index in sorted_keys]
            if self.votes_total_count:
                percentages = [
                    str(round(self.votes_dict[index] / self.votes_total_count, 4) * 100) + "%" for index in sorted_keys
                ]
            payload = {
                "payload_type": "build_order_vote",
                "vote_type": "update_vote",
                "current_matchup": current_matchup,
                "percentages": percentages,
                "unique_votes": str(self.votes_total_count),
                "time_active": str(int(time.time() - self.voting_started_time)),
                "time_till_vote_ends": str(self.config.voting_time_duration),
            }
            await self.bot.websocket_broadcast_json(json.dumps(payload))

        elif websocket_type == "end_vote":
            # Hide overlay
            payload = {"payload_type": "build_order_vote", "vote_type": "end_vote"}
            await self.bot.websocket_broadcast_json(json.dumps(payload))

        elif websocket_type == "show_step":
            # Show overlay, change info
            payload = {
                "payload_type": "build_order_step",
                "step_type": "show_step",
                # Build order was verified, the dict has to have this attribute
                "title": self.chosen_bo["title"],
            }
            step_data_list = self.get_step_data_from_bo()
            step_data_dict = {
                "step0_time": step_data_list[0],
                "step0_info": step_data_list[1],
                "step1_time": step_data_list[2],
                "step1_info": step_data_list[3],
                "animation_time": self.config.build_order_step_fade_animation_in_ms,
            }
            payload.update(step_data_dict)
            await self.bot.websocket_broadcast_json(json.dumps(payload))

        elif websocket_type == "hide_step":
            # Show overlay, change info
            payload = {"payload_type": "build_order_step", "step_type": "hide_step"}
            await self.bot.websocket_broadcast_json(json.dumps(payload))

    async def on_new_websocket_connection(self):
        """
        Whenever a new overlay connection is made (e.g. scene switch, or overlay was just enabled
        """
        if self.voting_is_running:
            # Show voting poll
            await self.build_order_send_websocket_data("start_vote", self.current_matchup)
            # Update voting poll with the vote percentages
            await self.build_order_send_websocket_data("update_vote")
        else:
            # Hide voting overlay if vote is not running
            await self.build_order_send_websocket_data("end_vote")

        if self.game_is_running and self.chosen_bo:
            # Show build order step because streamer is in a game and a build order was picked (either by voting or because only one build order exists for this matchup
            await self.build_order_send_websocket_data("show_step")
        else:
            # Hide build order step because no build order was picked or no build order for this matchup exists
            await self.build_order_send_websocket_data("hide_step")

    async def on_new_game_with_players(self, match_info: MatchInfo):

        # Reload build orders file if it was changed
        # TODO: only reload if file was modified
        self.load_build_orders()

        # Reset values
        self.user_already_voted.clear()
        self.votes_dict.clear()
        self.votes_total_count = 0

        self.chosen_bo = None
        self.in_game_time = 0
        self.end_of_bo_found = False
        self.end_of_bo_found_time = 0
        self.game_is_running = True
        self.voting_started_time = time.time()

        self.current_matchup = f"{match_info.p1race[0].upper()}v{match_info.p2race[0].upper()}"
        if self.current_matchup not in self.build_orders:
            logger.warning(
                f"No build order found for matchup {self.current_matchup}. Could not display a build order on build order overlay."
            )
            return

        build_orders = self.build_orders[self.current_matchup]
        self.build_orders_current_matchup_enabled = [bo for bo in build_orders if bo["enabled"]]

        bo_count = len(self.build_orders_current_matchup_enabled)
        self.votes_dict = {i: 0 for i in range(bo_count)}

        # If only one build order is enabled in this matchup, then show build order directly instead of voting
        if bo_count > 1:
            # Enable voting
            logger.debug(f"More than one build order detected!")
            await self.build_order_send_websocket_data("start_vote", current_matchup=self.current_matchup)
            self.voting_is_running = True
            self.voting_started = time.time()

        elif bo_count == 1:
            # Show build order directly, no voting needed
            self.chosen_bo = self.build_orders_current_matchup_enabled[0]
            await self.build_order_send_websocket_data("show_step")

        elif bo_count == 0:
            # Don't show anything
            logger.warning(f"No build order for matchup {self.current_matchup} was entered. Returning.")

    async def on_message(self, message: Message):
        """
        When there is a new message and voting is running, parse the message and apply the vote to the voting overlay
        """
        if self.voting_is_running:
            message_stripped = message.content.strip()
            if message_stripped.isnumeric() and (
                message.author.name not in self.user_already_voted or self.config.debug_allow_multiple_votes
            ):
                vote_number = int(message_stripped) - 1
                if vote_number in self.votes_dict:
                    # Each user has 1 vote, dont let him vote more often
                    self.user_already_voted.add(message.author.name)
                    # Increment vote by 1
                    self.votes_dict[vote_number] += 1
                    # Increment total unique votes by 1
                    self.votes_total_count += 1
                    await self.build_order_send_websocket_data(websocket_type="update_vote")

    async def on_tick(self):
        # If time has passed (30 secs or so ingame time), hide voting, choose build order with most votes
        if self.voting_is_running:
            if self.bot.match_info.game_time > self.config.voting_time_duration:
                # The key lambda function generates a tuple e.g. (5, 9) which means this build got 5 votes and has priority 9, so if another build got (5, 8) equal amount of votes but lower priority, the first one should be chosen
                index_with_most_votes = max(
                    (index for index in self.votes_dict.keys()),
                    key=lambda i: (self.votes_dict[i], self.build_orders_current_matchup_enabled[i].get("priority", 0)),
                )
                self.chosen_bo = self.build_orders_current_matchup_enabled[index_with_most_votes]
                await self.build_order_send_websocket_data("end_vote")
                if self.config.announce_voted_build_order_in_chat:
                    if self.votes_total_count > 0:
                        await self.send_message(f"Chosen build order by vote: {self.chosen_bo['title']}")
                    # Should a build order be announced if nobody voted for it? Default BO will be selected
                    # else:
                    #     await self.send_message(f"Chosen build order by default: {self.chosen_bo['title']}")
                self.voting_is_running = False
            else:
                # Update the vote display time
                await self.build_order_send_websocket_data(websocket_type="update_vote")

        # If build order is chosen for this game, and game is running, update step display info
        if not self.end_of_bo_found and self.chosen_bo is not None and self.game_is_running:
            self.in_game_time = self.bot.match_info.game_time
            await self.build_order_send_websocket_data("show_step")

        # If the end of the build order was found, fade it out after a couple seconds delay
        elif self.end_of_bo_found and self.game_is_running:
            self.in_game_time = self.bot.match_info.game_time
            if self.in_game_time - self.config_end_of_bo_fade_out_time > self.end_of_bo_found_time:
                await self.build_order_send_websocket_data(websocket_type="hide_step")

    async def on_game_ended(self, match_info: MatchInfo):
        self.game_is_running = False
        self.voting_is_running = False
        await self.build_order_send_websocket_data("end_vote")
        await self.build_order_send_websocket_data("hide_step")


if __name__ == "__main__":
    bo_overlay = BuildOrderOverlay()
    bo_overlay.load_build_orders()
