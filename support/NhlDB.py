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


# NOTE: this is temporary!!!!
# NOTE: For testing purposes only
class Game:
    def __init__(self, homeTeamId=None, awayTeamId=None):
        self.homeTeamId = homeTeamId
        self.awayTeamId = awayTeamId
        self.homeTeamEvents = []
        self.awayTeamEvents = []

    @property
    def valid(self):
        # technically it is possible to have no events saved, but the team Ids must be present
        return None not in (self.homeTeamId, self.awayTeamId)
    
    @property
    def json(self):
        return {
            "homeTeamId": self.homeTeamId,
            "awayTeamId": self.awayTeamId,
            "homeTeamEvents": len(self.homeTeamEvents),
            "awayTeamEvents": len(self.awayTeamEvents)
        }


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

yearlyEvents = defaultdict(list)

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

            game = Game(homeTeamId=homeTeamId, awayTeamId=awayTeamId)
            
            for event in jsonData["liveData"]["plays"]["allPlays"]:
                if event["result"]["event"] in ("Shot", "Goal",):

                    e = NHLData(event)

                    # The shooting team is the reported team in the event.
                    if event["team"]["id"] == homeTeamId:
                        game.homeTeamEvents.append(e)
                    elif event["team"]["id"] == awayTeamId:
                        game.awayTeamEvents.append(e)
                    else:
                        print(colored(f'failed to find away or home team matching {event["team"]["id"]}', 'yellow'))

            # add the game to the list for the year
            yearlyEvents[season].append(game)


# for k, v in yearlyEvents.items():
#     for game in v:
#         print(dumps(game.json, indent=2))

#         for he in game.homeTeamEvents:
#             print(dumps(he.json, indent=2))
#             break

#         for ae in game.awayTeamEvents:
#             print(dumps(ae.json, indent=2))
#             break
    
#         break
#     break
