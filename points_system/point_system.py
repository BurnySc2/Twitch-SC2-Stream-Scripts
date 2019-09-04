from __future__ import annotations
from typing import TYPE_CHECKING

from twitchio import Message

# https://pypi.org/project/tinydb/
# https://tinydb.readthedocs.io/en/latest/usage.html#data-access-and-modification
from tinydb import TinyDB, Query
from tinydb.operations import add

import json
import os
import datetime
import time
import logging
from typing import List

logger = logging.getLogger(__name__)

from plugin_base_class.base_class import BaseScript


if TYPE_CHECKING:
    from bot import TwitchChatBot


class PointSystem(BaseScript):
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot

        # Launch database
        database_path = os.path.join(os.path.dirname(__file__), "db.json")
        self.db = TinyDB(database_path)

        # Load config file
        # Give points every X minutes
        config_file_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_file_path) as f:
            config_json = json.load(f)
            self.give_points_interval = config_json["give_points_interval"]
            self.viewer_pointers_increment = config_json["viewer_pointers_increment"]
            self.active_chatter_points_increment = config_json["active_chatter_points_increment"]
            self.active_chatter_time = config_json["active_chatter_time"]

        # Keep track on when the points were last updated
        self.timestamp_last_points_given: float = time.time()

    def add_new_user(self, user: str, points: int = 0, last_message: float = 0):
        self.db.insert({"name": user, "points": points, "last_message": last_message})

    def update_last_message(self, user: str):
        """
        Update when the last message of the user was sent.
        """
        User = Query()
        result: List[dict] = self.db.search(User.name == user)
        assert len(result) < 2
        if not result:
            self.add_new_user(user=user, last_message=time.time())
        else:
            self.db.update({"last_message": time.time()}, User.name == user)

    def add_points(self, user: str, amount: int):
        """
        Increment points of a user.
        """
        User = Query()

        # Find current users with that username in database
        result: List[dict] = self.db.search(User.name == user)

        assert (
            len(result) < 2
        ), f"More than one entry got returned when trying to find {user} in points_database: {result}"

        # Entry with that username does not exist
        if not result:
            self.add_new_user(user=user, points=amount)

        else:
            # Entry with that username was found, will be returned as list

            # Add points to all results (which should be only one result)
            current_points = result[0]["points"]
            # Update entry
            self.db.update({"points": current_points + amount}, User.name == user)

    def remove_points(self, user: str, amount: int):
        self.add_points(user, -amount)

    async def give_points_to_all_chatters(self):
        User = Query()
        chatters = await self.bot.get_chatters(self.bot.main_channel)

        for chatter in chatters.all:
            # All chatters are displayed as display name, so this doesnt work for asian characters?
            chatter_name = chatter.lower()

            # Find results from database
            result: List[dict] = self.db.search(User.name == chatter_name)
            assert (
                len(result) < 2
            ), f"More than one entry got returned when trying to find {chatter_name} in points_database: {result}"

            # Current chatter / viewer has not written any message as he is not in the database
            if not result:
                self.add_new_user(chatter_name, self.viewer_pointers_increment)

            else:
                # Get when the user last wrote a message, UTC timestamp
                time_last_message = result[0]["last_message"]
                user_is_active_chatter = time.time() - time_last_message < self.active_chatter_time
                # Get the current points of the viewer
                current_points = result[0]["points"]

                if user_is_active_chatter:
                    # User is active chatter, add more points
                    self.db.update(
                        {"points": current_points + self.active_chatter_points_increment}, User.name == chatter_name
                    )

                else:
                    # User is inactive chatter, add low amount of points
                    self.db.update(
                        {"points": current_points + self.viewer_pointers_increment}, User.name == chatter_name
                    )

    async def on_message(self, message: Message):
        self.update_last_message(message.author.name)

    async def on_tick(self):
        if time.time() - self.timestamp_last_points_given > self.give_points_interval:
            await self.give_points_to_all_chatters()
            self.timestamp_last_points_given = time.time()


if __name__ == "__main__":
    ps = PointSystem()
    ps.add_points("burnysc2", 1)
    ps.update_last_message("burnysc2")
