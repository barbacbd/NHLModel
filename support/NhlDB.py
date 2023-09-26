"""
The script will create and fill the sqlite data base for this project.

Create two tables including the players(goalies) and the events that include:
- Shots
- Missed Shots
- Blocked Shots
- Goals
"""
import os
from json import dumps, loads
from enum import Enum
import sqlite3
from termcolor import colored
from os.path import exists
from collections import defaultdict
from nhl_core import NHLData


# Assume that the directory is in this same directory as this script
directory = 'nhl_data/2022'
    
class EventType(Enum):
    SHOT = 'Shot'
    GOAL = 'Goal'
    BLOCKED_SHOT = 'Blocked Shot'
    MISSED_SHOT = 'Missed Shot'

def eventTypeToStr(eventType):
    for x in EventType:
        if x.value == eventType:
            return x.value

    return None


eventTypes = [x.value for x in EventType]


# year -> team_id -> event data
events = defaultdict(lambda: defaultdict(list))

# Go through the list of files. Make sure that we have all players (these may
# require some corrections, see Corrections.py for more information). Retrieve
# all of the events from each game too; these will be added to the database. 
for root, dirs, files in os.walk(directory):
    for filename in files:
        #if filename in readFiles:
        #    print(colored(f"Skipping {filename}", 'yellow'))
        #    continue
        
        fname = os.path.join(root, filename)        
        print(colored(f"processing: {fname}", 'green'))

        jsonData = None
        with open(fname) as jsonFile:
            jsonData = loads(jsonFile.read())

        if jsonData:
            
            gameInfo = jsonData["gameData"]


            gameId = gameInfo["game"]["pk"]
            season = gameInfo["game"]["season"]
            homeTeamId = gameInfo["teams"]["home"]["id"]
            awayTeamId = gameInfo["teams"]["away"]["id"]
            
            # this must be local or trades could mess with this simple logic 
            playersByTeam = defaultdict(list)
            for k, v in gameInfo["players"].items():
                playersByTeam[v["currentTeam"]["id"]].append(v["id"])
            
            # All events are unique, so these will all be added to the database
            for event in jsonData["liveData"]["plays"]["allPlays"]:
                if event["result"]["event"] in ("Shot", "Goal",):
                    e = NHLData(event)

                    for player in event["players"]:
                        playerId = int(player["player"]["id"])

                        if player["playerType"] == "Shooter":
                            if playerId in playersByTeam[homeTeamId]:
                                events[season][homeTeamId].append(e)
                            elif playerId in playersByTeam[awayTeamId]:
                                events[season][awayTeamId].append(e)

        break
    break


for k, v in events.items():
    print(f"{k}\n\n")

    for innerk, innerv in v.items():
        print(f"\t{innerk}\n\n")

        for event in innerv:
            print(dumps(event.json,indent=2))

