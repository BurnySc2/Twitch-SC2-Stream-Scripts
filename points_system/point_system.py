from __future__ import annotations
from typing import TYPE_CHECKING

from twitchio import Message

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin
import atexit


from typing import List, Dict

from loguru import logger

from plugin_base_class.base_class import BaseScript


if TYPE_CHECKING:
    from bot import TwitchChatBot


@dataclass()
class PointSystemConfig(DataClassJsonMixin):
    give_points_interval: int = 300
    viewer_pointers_increment: int = 5
    active_chatter_time: int = 1800
    active_chatter_points_increment: int = 50


class PointSystem(BaseScript):
    def __init__(self, bot=None):
        self.bot: TwitchChatBot = bot

        self.database_path: Path = Path(__file__).parent / "db.json"
        # Launch database
        self.db = {}
        self.load_database()

        # When the dict was last updated, which means a new user was inserted, points were updated or subtracted
        self.db_last_updated: float = time.time()
        # When the dict was last written to file
        self.db_last_written: float = time.time()
        self.db_changes_pending: int = 0

        # Keep track on when the points were last updated for all users
        self.timestamp_last_points_given: float = time.time()

        # Check if stream is online
        self.stream_is_online: bool = False
        self.last_stream_is_online_check: float = time.time()
        self.stream_is_online_check_interval: int = 120
        self.name_to_id_dict: Dict[str, int] = {}

        # Load config file
        config_file_path = Path(__file__).parent / "config.json"
        with open(config_file_path) as f:
            self.config = PointSystemConfig.from_json(f.read())

        atexit.register(self.on_exit)

        logger.info(
            f"At the current configuration, chatters receive {60 * self.config.active_chatter_points_increment / self.config.give_points_interval}  points per minute while lurker-viewers receive {60 * self.config.viewer_pointers_increment / self.config.give_points_interval} points per minute"
        )

    def load_database(self):
        if self.database_path.absolute().is_file():
            with self.database_path.open() as f:
                data = json.load(f)
                self.db.update(data)
        else:
            logger.warning(f"Database file does not exist, creating a new one: {self.database_path.absolute()}")

    def save_database(self):
        with self.database_path.open("w") as f:
            json.dump(self.db, f, sort_keys=True, indent=2)
        self.db_changes_pending = 0
        self.db_last_written = time.time()

    def get_points_of_user(self, user: str):
        if user not in self.db:
            logger.info(f"User {user} was not found in points database")
        return self.db.get(user, {"points": 0})["points"]

    def add_new_user(self, user: str, points: int = 0, last_message: float = 0):
        assert user not in self.db
        self.db[user] = {"points": points, "last_message": last_message}
        self.db_last_updated = time.time()
        self.db_changes_pending += 1

    def update_last_message(self, user: str):
        """
        Update when the last message of the user was sent.
        """
        if user in self.db:
            self.db[user]["last_message"] = time.time()
            self.db_last_updated = time.time()
            self.db_changes_pending += 1
        else:
            logger.debug(f"Found a new face in chat: {user}")
            self.add_new_user(user, last_message=time.time())

    def add_points(self, user: str, amount: int):
        """ Increment points of a user. """
        self.db[user]["points"] = self.db[user]["points"] + amount
        if amount != 0:
            self.db_last_updated = time.time()
            self.db_changes_pending += 1

    def remove_points(self, user: str, amount: int):
        """ Remove points from a user """
        self.add_points(user, -amount)

    async def give_points_to_all_chatters(self):
        self.timestamp_last_points_given = time.time()

        viewers = await self.bot.get_chatters(self.bot.main_channel_name)

        for viewer in viewers.all:
            # All chatters are displayed as display name, so this doesnt work for asian characters?
            viewer_name = viewer.lower()

            # Viewer has not chatted yet, so add him to the database
            if viewer_name not in self.db:
                self.add_new_user(viewer_name, last_message=0)

            time_last_message = self.db[viewer_name]["last_message"]
            user_is_active_chatter = time.time() - time_last_message < self.config.active_chatter_time

            # If viewer has chatted in the last X minutes, give him more points than a lurker
            if user_is_active_chatter:
                self.add_points(viewer_name, amount=self.config.active_chatter_points_increment)
            else:
                self.add_points(viewer_name, amount=self.config.viewer_pointers_increment)
            self.db_last_updated = time.time()
            self.db_changes_pending += 1

    async def check_if_stream_is_live(self, channel_name: str) -> bool:
        # Get the ID of the streamer to be able to poll if the stream is live
        channel_name = channel_name.lower()
        channel_id = self.name_to_id_dict.get(channel_name, None)
        if channel_id is None:
            for channel_info in self.bot.twitch_client.users.translate_usernames_to_ids([channel_name]):
                # Cache name to id
                self.name_to_id_dict[channel_info.name] = channel_info.id
            channel_id = self.name_to_id_dict[channel_name]

        # Check if stream is live
        stream_data = self.bot.twitch_client.streams.get_stream_by_user(channel_id)
        if stream_data and stream_data.stream_type == "live":
            return True
        return False

    async def on_ready(self):
        """ Once the bot starts, check immediately if channel is live. """
        self.stream_is_online = await self.check_if_stream_is_live(self.bot.main_channel_name)
        logger.info(f"Point system initialized. Stream is live ({self.bot.main_channel_name}): {self.stream_is_online}")

    async def on_message(self, message: Message):
        # Update last time a user entered a message, so they get more points, instead of people who arent chatting and just watching
        self.update_last_message(message.author.name)

    def on_exit(self):
        """ Gets called when this instance is shut down - application exit """
        # Only write to database if the database was changed at all
        if self.db_last_updated > self.db_last_written:
            logger.warning(f"Bot was closed before data was written to database file")
            self.save_database()
            logger.warning(f"Data was successfully written to database file on bot shutdown.")

    async def on_tick(self):
        # Every X minutes, check if the stream is online and only if stream is online, give chatters / viewers points
        if time.time() - self.last_stream_is_online_check > self.stream_is_online_check_interval:
            stream_is_online: bool = await self.check_if_stream_is_live(self.bot.main_channel_name)
            if self.stream_is_online != stream_is_online:
                self.stream_is_online = stream_is_online
                logger.info(
                    f"Checked if stream {self.bot.main_channel_name} is live. Detected a change, stream is live: {stream_is_online}"
                )

        if self.stream_is_online:
            # Give points to chatters every X minutes
            if time.time() - self.timestamp_last_points_given > self.config.give_points_interval:
                await self.give_points_to_all_chatters()

            # Write current database to file (don't write after each change instantly to file)
            if (
                # Wait x seconds before writing the updated database entry to file
                (time.time() - self.db_last_updated > 30 or self.db_changes_pending > 5)
                # Only write to database if the database was changed at all
                and self.db_last_updated > self.db_last_written
                # At least one change is pending
                and self.db_changes_pending > 0
            ):
                self.save_database()


if __name__ == "__main__":
    ps = PointSystem()
    ps.add_points("burnysc2", 1)
    ps.update_last_message("burnysc2")
