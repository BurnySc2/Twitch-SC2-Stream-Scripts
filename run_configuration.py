from pathlib import Path
import json
from copy import deepcopy

twitch_irc_token_path = Path(__file__).parent / "config" / "twitch_irc_token.json"
main_config_path = Path(__file__).parent / "config" / "bot_config.json"
match_info_config_path = Path(__file__).parent / "match_info" / "config.json"
point_system_config_path = Path(__file__).parent / "match_info" / "config.json"
build_order_overlay_config_path = Path(__file__).parent / "build_order_overlay" / "config.json"
scene_switcher_config_path = Path(__file__).parent / "scene_switcher" / "config.json"


def main():
    print("Starting configuration progress.")
    print(f"Press enter to keep the old configured value.")
    set_up_twitch_irc_token()
    set_up_main_config()
    input("Setup complete. Press any key to close this window.")


def set_up_twitch_irc_token():
    """ Configures /config/twitch_irc_token.json """
    settings = read_dict_from_file(twitch_irc_token_path)
    old_settings = settings.copy()

    new_key = input(
        """
Log in to twitch (can be a new incognito window so you don't have to log out on your main browser window) with your bot account
Open 'https://twitchapps.com/tmi/' and hit 'connect'

Do NOT share this key with anyone - With this, they have access to chat with your bot account.

Copy your oauth / key into this field: 
"""
    ).strip()
    if new_key:
        settings["token"] = new_key

    write_dict_to_file(settings, twitch_irc_token_path, old_dictionary=old_settings)


def set_up_main_config():
    """ Configures /config/bot_config.json """
    settings = read_dict_from_file(main_config_path)
    old_settings = settings.copy()

    settings_text = {
        "twitch_channel_name": "What's your twitch channel name?",
        "bot_name": "What's your bot name?",
        "command_prefix": "Bot command prefix?",
        "match_info": "Enable match info? (y/n)",
        "point_system": "Enable custom channel point system? (y/n)",
        "build_order_overlay": "Enable build order overlay? (y/n)",
        "scene_switcher": "Enable scene switcher? (y/n)",
    }

    for key, old_value in settings.items():
        new_value = input(f"{settings_text[key]} (Old value: {old_value}) ").strip()

        # User pressed enter without a value
        if not new_value:
            continue

        # Overwrite settings
        if isinstance(old_value, bool):
            settings[key] = yes_or_no(new_value)
        if isinstance(old_value, int) or isinstance(old_value, float):
            settings[key] = float(new_value)
        else:
            settings[key] = new_value

    # Write values to json
    write_dict_to_file(settings, main_config_path, old_dictionary=old_settings)

    if settings["match_info"]:
        set_up_match_info()
    if settings["point_system"]:
        set_up_point_system()
    if settings["build_order_overlay"]:
        set_up_build_order_overlay()
    if settings["scene_switcher"]:
        set_up_scene_switcher()


def set_up_match_info():
    """ Sets the account names and the server. """
    settings = read_dict_from_file(match_info_config_path)
    old_settings = deepcopy(settings)

    clear_accounts: bool = yes_or_no(
        input(f"Clear current list of accounts (y/n)? Current accounts: {settings['accounts']} ")
    )
    if clear_accounts:
        settings["accounts"].clear()

    while 1:
        account_name = input(
            "Your in-game account name? (case sensitive, the name that appears on the map loading screen) "
        ).strip()
        if not account_name:
            break
        settings["accounts"].append(account_name)

    print(f"Current account list updated to: {settings['accounts']}")

    server_name = input("What server are you playing on? ('us', 'eu' or 'kr') ").strip().lower()
    assert server_name in {"", "us", "eu", "kr"}
    settings["server"] = server_name

    # Write values to json
    write_dict_to_file(settings, match_info_config_path, old_dictionary=old_settings)


def set_up_point_system():
    settings = read_dict_from_file(point_system_config_path)
    old_settings = settings.copy()

    settings_text = {
        "give_points_interval": "What's the interval (in seconds) that viewers should be awarded points automatically?",
        "viewer_pointers_increment": "How many points should viewers (lurkers) get awarded on each interval?",
        "active_chatter_time": "Viewers should be marked as active chatters for how long (in seconds) since their last message?",
        "active_chatter_points_increment": "How many points should active chatters get awarded on each interval?",
    }

    for key, old_value in settings.items():
        new_value = input(f"{settings_text[key]} (Old value: {old_value}) ").strip()
        if new_value:
            settings[key] = int(new_value)

    # Write values to json
    write_dict_to_file(settings, point_system_config_path, old_dictionary=old_settings)


def set_up_build_order_overlay():
    settings = read_dict_from_file(build_order_overlay_config_path)
    old_settings = settings.copy()

    settings_text = {
        "voting_time_duration": "How much time (in seconds) do viewers have to vote for the build order they want to see (if you have at least 2 build orders prepared in the matchup you are currently playing)?",
        "build_order_step_fade_animation_in_ms": "Build-order-step overlay fade animation time (in milliseconds)?",
    }

    for key, old_value in settings.items():
        new_value = input(f"{settings_text[key]} (Old value: {old_value}) ").strip()
        if new_value:
            settings[key] = int(new_value)

    # Write values to json
    write_dict_to_file(settings, build_order_overlay_config_path, old_dictionary=old_settings)


def set_up_scene_switcher():
    settings = read_dict_from_file(scene_switcher_config_path)
    old_settings = settings.copy()

    print(
        f"The IP is {settings['host']} and the port {settings['port']} for the OBS websocket plugin connection which is necessary for the bot to apply scene switches. The password is by default blank. Please go in the /scene_switcher/config.json and change it manually if you want to change that."
    )

    settings_text = {
        "game_scene": "What is your game scene name (which will be used when playing 1v1, teamgames, arcade)?",
        "menu_scene": "What is your menu scene name (which will be used when in menu)?",
        "replay_scene": "What is your observer / replay scene name (which will be used when observing a game or watching a replay)?",
    }

    for key in settings_text:
        old_value = settings[key]
        new_value = input(f"{settings_text[key]} (Old value: {old_value}) ").strip()
        if new_value:
            settings[key] = new_value

    # Write values to json
    write_dict_to_file(settings, build_order_overlay_config_path, old_dictionary=old_settings)


def read_dict_from_file(file_path: Path) -> dict:
    with open(file_path) as f:
        return json.load(f)


def write_dict_to_file(dictionary: dict, file_path: Path, old_dictionary: dict = None):
    if old_dictionary is not None and dictionary == old_dictionary:
        return
    with open(file_path, "w") as f:
        json.dump(dictionary, f, indent=4)


def yes_or_no(string: str) -> bool:
    if string.strip().lower() in {"y", "yes", "true"}:
        return True
    return False


if __name__ == "__main__":
    main()
