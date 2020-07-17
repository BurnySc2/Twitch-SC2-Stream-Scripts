from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
from pathlib import Path
import json
from copy import deepcopy
from typing import List, Dict, Set, Union, Optional

twitch_irc_token_path = Path(__file__).parent / "config" / "twitch_irc_token.json"
main_config_path = Path(__file__).parent / "config" / "bot_config.json"
match_info_config_path = Path(__file__).parent / "match_info" / "config.json"
point_system_config_path = Path(__file__).parent / "match_info" / "config.json"
build_order_overlay_config_path = Path(__file__).parent / "build_order_overlay" / "config.json"
scene_switcher_config_path = Path(__file__).parent / "scene_switcher" / "config.json"


@dataclass()
class BaseClassSettings(DataClassJsonMixin):
    @classmethod
    def yes_or_no(cls, string: str) -> bool:
        """ Converts a string to boolean. """
        if string.strip().lower() in {"y", "yes", "true"}:
            return True
        return False

    @classmethod
    def config_path(cls) -> Path:
        """ Where the config can be found. Required for 'load_config()' """
        raise NotImplementedError(f"Missing config path for class f{cls.__name__}")

    @classmethod
    def load_config(cls) -> "BaseClassSettings":
        # If file is missing, just return new class instance
        if cls.config_path().is_file():
            with cls.config_path().open() as f:
                return cls.from_json(f.read())
        return cls()

    def save_config(self, old_object: "BaseClassSettings" = None):
        if old_object is not None and self == old_object:
            return
        with self.config_path().open("w") as f:
            f.write(self.to_json(indent=4))

    @property
    def helper_strings(self) -> Dict[str, str]:
        """ Information about the input type of the current value. See 'enter_config' function. """
        return {}

    @property
    def case_insensitive_values(self) -> Set[str]:
        """ Information about the case sensitivity of the config key. """
        return set()

    def enter_config(self):
        """ Lets the user manually re-fill all the values in this object. Converts input strings to int, float etc. automatically """
        for key, old_value in self.__dict__.items():
            if key not in self.helper_strings:
                continue

            helper_text = self.helper_strings[key]
            input_helper_text = f"{helper_text} (Previous value: {old_value})"

            if isinstance(old_value, list):
                while 1:
                    input_value = input(f"{input_helper_text} ")
                    if not input_value:
                        break
                    old_value.append(input_value)
            elif isinstance(old_value, (bool, int, float, str)):
                input_value = input(f"{input_helper_text} ")
                # No input given, save the old value
                if not input_value:
                    self.__dict__[key] = old_value
                    continue

                if isinstance(old_value, bool):
                    input_value = self.yes_or_no(input_value)
                elif isinstance(old_value, int):
                    input_value = int(input_value)
                elif isinstance(old_value, float):
                    input_value = float(input_value)
                elif isinstance(old_value, str):
                    input_value = input_value.strip()
                    if key not in self.case_insensitive_values:
                        input_value = input_value.lower()

                assert type(input_value) == type(old_value), f"{input_value} != {old_value}"
                self.__dict__[key] = input_value


@dataclass()
class MainConfig(BaseClassSettings):
    twitch_channel_name: str = "burnysc2"
    bot_name: str = "burnysc2bot"
    command_prefix: str = "!"
    match_info: bool = True
    point_system: bool = True
    build_order_overlay: bool = True
    scene_switcher: bool = True

    @classmethod
    def config_path(cls) -> Path:
        return main_config_path

    @property
    def case_insensitive_values(self) -> Set[str]:
        """ Information about the case sensitivity of the config key. """
        return {"twitch_channel_name", "bot_name"}

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "twitch_channel_name": "What's your twitch channel name?",
            "bot_name": "What's the account name of your twitch bot account?",
            "command_prefix": "Bot command prefix?",
            "match_info": "Enable match info? (y/n)",
            "point_system": "Enable custom channel point system? (y/n)",
            "build_order_overlay": "Enable build order overlay? (y/n)",
            "scene_switcher": "Enable scene switcher? (y/n)",
        }


@dataclass()
class TwitchIrcToken(BaseClassSettings):
    token: str = ""

    @classmethod
    def config_path(cls) -> Path:
        return twitch_irc_token_path

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "token": """
Log in to twitch (can be a new incognito window so you don't have to log out on your main browser window) with your bot account
Open 'https://twitchapps.com/tmi/' and hit 'connect'

Do NOT share this key with anyone - With this, they have access to chat with your bot account.

Copy your oauth / key into this field:
"""
        }


@dataclass()
class MatchInfoConfig(BaseClassSettings):
    accounts: List[str] = field(default_factory=lambda: [])
    # One of: US, EU, KR
    server: str = "eu"

    @classmethod
    def config_path(cls) -> Path:
        return match_info_config_path

    @property
    def case_insensitive_values(self) -> Set[str]:
        """ Information about the case sensitivity of the config key. """
        return {"server"}

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "accounts": "Add SC2 account name (case sensitive, the name that appears on the map loading screen)",
            "server": "What server are you playing on? (One of: 'us', 'eu', 'kr') ",
        }


@dataclass()
class PointSystemConfig(BaseClassSettings):
    give_points_interval: int = 300
    viewer_pointers_increment: int = 5
    active_chatter_time: int = 1800
    active_chatter_points_increment: int = 50

    @classmethod
    def config_path(cls) -> Path:
        return point_system_config_path

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "give_points_interval": "What's the interval (in seconds) that viewers should be awarded points automatically?",
            "viewer_pointers_increment": "How many points should viewers (lurkers) get awarded on each interval?",
            "active_chatter_time": "Viewers should be marked as active chatters for how long (in seconds) since their last message?",
            "active_chatter_points_increment": "How many points should active chatters get awarded on each interval?",
        }


@dataclass()
class BuildOrderOverlayConfig(BaseClassSettings):
    voting_time_duration: int = 30
    build_order_step_fade_animation_in_ms: int = 500

    @classmethod
    def config_path(cls) -> Path:
        return build_order_overlay_config_path

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "voting_time_duration": "How much time (in seconds) do viewers have to vote for the build order they want to see (if you have at least 2 build orders prepared in the matchup you are currently playing)?",
            "build_order_step_fade_animation_in_ms": "Build-order-step overlay fade animation time (in milliseconds)?",
        }


@dataclass()
class SceneSwitcherConfig(BaseClassSettings):
    host: str = "localhost"
    port: int = 4444
    password: str = ""
    enabled: bool = True
    game_scene: str = "SceneGame"
    menu_scene: str = "SceneLobby"
    replay_scene: str = "SC2Observer"

    @classmethod
    def config_path(cls) -> Path:
        return scene_switcher_config_path

    @property
    def helper_strings(self) -> Dict[str, str]:
        return {
            "game_scene": "What is your game scene name (which will be used when playing 1v1, teamgames, arcade)?",
            "menu_scene": "What is your menu scene name (which will be used when in menu)?",
            "replay_scene": "What is your observer / replay scene name (which will be used when observing a game or watching a replay)?",
        }


def main():
    print("Starting configuration progress.")
    print(f"Press enter to keep the old configured value.")
    set_up_twitch_irc_token()
    set_up_main_config()
    input("Setup complete. Press any key to close this window.")


def set_up_twitch_irc_token():
    """ Configures /config/twitch_irc_token.json """
    twitch_irc_token_config = TwitchIrcToken.load_config()
    old_twitch_irc_token_config = deepcopy(twitch_irc_token_config)
    # Re-fill all values (user input)
    twitch_irc_token_config.enter_config()
    twitch_irc_token_config.save_config(old_twitch_irc_token_config)


def set_up_main_config():
    """ Configures /config/bot_config.json if you want certain scripts to be disabled. """
    main_config = MainConfig.load_config()
    old_main_config = deepcopy(main_config)
    # Re-fill all values (user input)
    main_config.enter_config()
    main_config.save_config(old_main_config)

    if main_config.match_info:
        set_up_match_info()
    if main_config.point_system:
        set_up_point_system()
    if main_config.build_order_overlay:
        set_up_build_order_overlay()
    if main_config.scene_switcher:
        set_up_scene_switcher()


def set_up_match_info():
    """ Sets the account names and the server. """
    match_info_config = MatchInfoConfig.load_config()
    old_match_info_config = deepcopy(match_info_config)

    # Clear previous account names?
    clear_accounts = match_info_config.yes_or_no(
        input(f"Clear current list of accounts (y/n)? Current accounts: {match_info_config.accounts} ")
    )
    if clear_accounts:
        match_info_config.accounts.clear()

    # Re-fill all values (user input)
    match_info_config.enter_config()
    assert match_info_config.server in {"", "us", "eu", "kr"}
    match_info_config.save_config(old_match_info_config)


def set_up_point_system():
    """ Sets up the point system - how quickly people in the channel receive points. """
    point_system_config = PointSystemConfig.load_config()
    old_point_system_config = deepcopy(point_system_config)
    # Re-fill all values (user input)
    point_system_config.enter_config()
    point_system_config.save_config(old_point_system_config)


def set_up_build_order_overlay():
    """ Sets up the build overlay - how fast the transitions are. """
    build_order_overlay_config = BuildOrderOverlayConfig.load_config()
    old_build_order_overlay_config = deepcopy(build_order_overlay_config)
    # Re-fill all values (user input)
    build_order_overlay_config.enter_config()
    build_order_overlay_config.save_config(old_build_order_overlay_config)


def set_up_scene_switcher():
    """ Sets up the scene names for game, menu, replay (or observer). """
    scene_switcher_config = SceneSwitcherConfig.load_config()
    old_scene_switcher_config = deepcopy(scene_switcher_config)
    print(
        f"The IP is {scene_switcher_config.host} and the port {scene_switcher_config.port} for the OBS websocket plugin connection which is necessary for the bot to apply scene switches. The password is by default blank. Please go in the /scene_switcher/config.json and change it manually if you want to change that."
    )
    # Re-fill all values (user input)
    scene_switcher_config.enter_config()
    scene_switcher_config.save_config(old_scene_switcher_config)


if __name__ == "__main__":
    main()
