# work in progress

# What is this
This script uses the SC2 client api and twitch chat to interact with viewers, enabling them to bet on the streamer or the opponent on who is going to win the sc2 match.

# TODO
If the game didn't last long enough (streamer or opponent nearly instantly leaving), the betting will be canceled and the viewers will be refunded.

If the betting script can't detect who the streamer is (streamer and opponent could have exactly the same name), the script will skip this game and not activate.

## Possible advanced feature
It could analyse the replay and check for the MMR difference, and pay out accordingly (e.g. when streamer beats opponent with much higher MMR than him, people who bet "win" should be paid out more since they gambled against the odds)
