import os
from json import dumps, loads
from termcolor import colored
from collections import defaultdict
from nhl_core import NHLData
from nhl_time_to_goal.event import ShotEvents, Game
from nhl_time_to_goal.team import TeamStats


# Assume that the directory is in this same directory as this script
directories = ['nhl_data/2021', 'nhl_data/2022']

# year -> team_id -> event data
totalStats = defaultdict()
season = None
games = defaultdict()

for directory in directories:
    # Go through the list of files. Make sure that we have all players (these may
    # require some corrections, see Corrections.py for more information). Retrieve
    # all of the events from each game too; these will be added to the database. 
    for root, dirs, files in os.walk(directory):

        yearlyTeamStats = {}
        seasonalGames = {}

        for filename in files:
            
            fname = os.path.join(root, filename)        
            print(colored(f"processing: {fname}", 'green'))

            jsonData = None
            with open(fname) as jsonFile:
                jsonData = loads(jsonFile.read())

            if jsonData:
                
                gameInfo = jsonData["gameData"]

                gameId = gameInfo["game"]["pk"]
                _season = gameInfo["game"]["season"]
                if season is None or _season != season:
                    season = _season

                homeTeamId = gameInfo["teams"]["home"]["id"]
                awayTeamId = gameInfo["teams"]["away"]["id"]

                if homeTeamId not in yearlyTeamStats:
                    yearlyTeamStats[homeTeamId] = TeamStats(teamId=homeTeamId, teamName=gameInfo["teams"]["home"]["teamName"])
                
                if awayTeamId not in yearlyTeamStats:
                    yearlyTeamStats[awayTeamId] = TeamStats(teamId=awayTeamId, teamName=gameInfo["teams"]["away"]["teamName"])


                game = Game(gameId, homeTeamId=homeTeamId, awayTeamId=awayTeamId)
                
                for event in jsonData["liveData"]["plays"]["allPlays"]:
                    if event["result"]["event"] in ("Shot", "Goal",):

                        e = NHLData(event)

                        # The shooting team is the reported team in the event.
                        if event["team"]["id"] == homeTeamId:
                            game.addHomeTeamEvent(e)
                        elif event["team"]["id"] == awayTeamId:
                            game.addAwayTeamEvent(e)
                        else:
                            print(colored(f'failed to find away or home team matching {event["team"]["id"]}', 'yellow'))

                yearlyTeamStats[awayTeamId].addAwayEvent(game)
                yearlyTeamStats[homeTeamId].addHomeEvent(game)
                seasonalGames[game.gameId] = game

        # add the data to the seasonal data
        totalStats[season] = yearlyTeamStats
        games[season] = seasonalGames

convertedData = {}
for k, v in totalStats.items():
    convertedData[k] = {}
    for inner_k, inner_v in v.items():
        convertedData[k][inner_k] = inner_v.json()

# with open("NhlYearlyStatistics.json", "w") as jsonFile:
#     jsonFile.write(dumps(convertedData, indent=2))


convertedGames = {}
for k, v in games.items():
    convertedGames[k] = {}
    for inner_k, inner_v in v.items():
        convertedGames[k][inner_k] = inner_v.json
with open("NhlYearlyGames.json", "w") as jsonFile:
    jsonFile.write(dumps(convertedGames, indent=2))