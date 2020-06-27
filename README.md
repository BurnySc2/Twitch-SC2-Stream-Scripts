# Twitch-SC2-Stream-Scripts

WORK IN PROGRESS

# What is this
This is a repository for my twitch stream scripts that I plan to publish and polish at one point. I will try to maintain and update them. There will be **no GUI** for these scripts because I don't want to put 90% of the work just for the GUI.

These scripts will be orientated around Python 3.7, StarCraft 2, OBS Studio and Twitch.

These scripts will use and interact with the Twitch-API, Twitch Chat, StarCraft 2 Client API, SC2Ladder.com API, StarCraft 2 replay parsers.
HTML files (for OBS as overlay) and twitch chat will be used as output.

# Setup
## Installation

- Install Python 3.7 or newer
- OBS Studio (or Streamlabs OBS if you don't care about the `scene switcher` script)
- Download all files in this repository and unzip
- In command line, run `pip install pipenv --user` to install `pipenv`
- In command line, navigate to this folder and run `pipenv install` to install the python requirements to run the bot (this may take a minute)
- For the `scene switcher` to work, you need to install the [OBS websocket plugin](https://github.com/Palakis/obs-websocket/releases)

## Configuration (Quick)

Run `python ./run_configuration.py` and follow the instructions.

## Configuration (Detailled)

1) Generate an oAuth-token, so that the bot can read chat messages (build order and betting system): Log into your **bot's twitch account** (or open a new window in incognito if you don't want to log out of your main account) and go to [twitchapps.com/tmi/](https://twitchapps.com/tmi/) to generate a token - **Do not show this token to anyone**

2) In the `config` folder, edit the following files with a text editor:
    - Edit `twitch_irc_token.json` with a text editor, paste the token (from step 1) so the file contents has to look like this:
        ```json
        {
          "token": "oauth:123my_completely_random_tokenabc"
        }
        ```
    - Edit `bot_config.json` and change the twitch channel and bot name accordingly. Set `bot_name` to the account the bot should write in chat to announce things (e.g. betting script), which can also be your main streaming account.
    - In same file you can enable or disable certain scripts
    
3) To configure the `match_info` overlay, open the `match_info` folder and edit the `config.json`
    - Fill the list of accounts with your SC2 account names (the name that appears on the loading screen)
    - Set the server to the server you are playing on (one of: "eu", "us", "kr" or `""` (=empty), the script will be much more accurate if you put a server)
    
4) To configure the `build order overlay`, go into the `build_order_overlay` folder and edit the `config.json`
    - `voting_time_duration` is the duration (in seconds) the players can vote for which build order the streamer should play (if more than 1 build order is active for the current ongoing matchup). If only one build order is active for this matchup, it will show. If no build order is active, the overlay will not show.
    - `build_order_step_fade_animation_in_ms` is the amount of time the animation will take to swap to the next step. Lower value results in faster animations.
    - Edit `build_orders.txt` to adjust the build orders that should appear on stream. 
        - `#` can be used as comments (will not show up)
        - After a line of `===` comes the build order title
        - After a line of `---` comes the build order configuration: here you can enable or disable it and set the matchup which the build order is for
        - The priority displays the order it shows up in viewer-voting (if a build order has a vote-tie, the build order with higher priority will be chosen)
        - After a line of `+++`, the build order items should be written down
        - Build order items should be in format `minute:seconds text`
        
5) To configure the `scene switcher`, go into the `scene_switcher` folder
    - Edit the `config.json`
        - Set the host IP and port if you changed the default OBS websocket plugin settings within OBS Studio, otherwise leave it as it is
        - Set your scenes. If your SC2 game scene is called `SceneGame`, then put `"game_scene": "SceneGame",` 
        - It can choose from 3 available scenes:
            - Game scene (when you are playing the game (1v1, teamgames, coop, arcade))
            - Replay scene (when you are observing a game, watching the replay or rewind after the game is over)
            - Menu scene (for all other SC2 locations)
            
6) Activating overlays in OBS:
    - Go into the `overlay_files` folder
    - Drag and drop the desired .html overlay files into OBS.
    - Resolution for the .html files should be set to the following (30 fps should suffice):
        - `match_info.html`: 200 width, 140 height
        - `build_order_vote.html`: 420 width, 400 height
        - `build_order_step.html`: 420 width, 300 to 350 height
        
## Running the bot

For the scripts the work, the bot needs to run in the background. It will output various (seemingly useless) information to the console and `bot.log` file.
- In command line, navigate to this folder and run `pipenv run bot.py` or `python -m pipenv run bot.py` to start the bot.
- It will print `bot.py READY | burnysc2bot` if it successfully started and connected to your twitch chat

# Script plugins and modules

This is a list of features that are working or might come into existance at one point:

- [ ] [SC2 Betting System](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/betting_system)

- [x] [SC2 Build Order Overlay](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/build_order_overlay)

- [ ] [SC2 Match history / Session Stats](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/match_history)

- [x] [SC2 Match Info Overlay](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/match_info)

- [ ] [Viewer Points Generator](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/points_generator)

- [x] [SC2 Scene Switcher](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/scene_switcher)

- [ ] [SC2 Twitch Title Updater](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/tree/master/title_updater)

# Bugs
If you run into bugs or issues or have questions, feel free to message me in Discord BuRny#8752 or [create a new issue on github](https://github.com/BurnySc2/Twitch-SC2-Stream-Scripts/issues/new).
