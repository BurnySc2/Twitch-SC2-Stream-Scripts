# work in progress

# What is this

This script uses the sc2 client API and twitch API to update the streamer's twitch title regularly.

It uses the matchup and opponent's name to display the name in the twitch title.

E.g.

```
"[EU] 1v1 Master Terran - now playing $matchup against '$opponent_name'"
```

This template text could be replaced by the script to

```
"[EU] 1v1 Master Terran - now playing TvZ against 'Saixy'"
```

and finally applied to the streamer's twitch title.
