# work in progress

# Idea

Viewers could interact with the streamer by voting which build order he should play. This could be realized via twitch chat.

E.g. streamer lists a bunch of build orders for TvZ

1. Hellion into BC into mech
2. Hellion into bio push
3. 3CC into BC into mech
4. 2-1-1
   At game start, the script detects the matchup, then lists the possibilities to the viewers (via overay or chat). Then the viewers can vote in chat which build order they want to see.

It then could parse the given build order, update the HTML (overlay) accordingly and display what should be built next if streamer plays according to plan:

```
0:15 Depot
0:40 Barracks
0:45 Gas
...
```

Displayed as:

```
Build Order
Now:
    4:40 +2 Barracks
Next:
    5:15 +2 Ebays
```

# TODO

What if the matchup is against random? Either the script will skip the game or the mods / streamer will have to set the matchup as soon as the opponent is scouted.

## Advanced possible feature:

The overlay could also be displayed for the streamer in a transparent window, not sure if possible, maybe the streamer could just open the HTML as well in browser on 2nd monitor. Depends on how much work this is gonna be.
