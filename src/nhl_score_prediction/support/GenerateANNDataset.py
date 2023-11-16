from collections import defaultdict
from json import dumps, loads
import os
from os import mkdir, remove
from os.path import exists, join as path_join
from shutil import rmtree
from nhl_core import NHLData
from nhl_score_prediction.poisson.poisson import (
    readStatisticsFile,
    getSchedule,
    parseSchedule,
    calculateAvgGoals,
    parseSeasonEvents
)
import pandas as pd


_staticBoxScoreData = {
    "teamId": ["team", "id"],
    "teamName": ["team", "name"],
    "triCode": ["team", "triCode"],
    "goals": ["teamStats", "teamSkaterStats", "goals"],
    "pim": ["teamStats", "teamSkaterStats", "pim"],
    "shots": ["teamStats", "teamSkaterStats", "shots"],
    "powerPlayPercentage": ["teamStats", "teamSkaterStats", "powerPlayPercentage"],
    "powerPlayGoals": ["teamStats", "teamSkaterStats", "powerPlayGoals"],
    "powerPlayOpportunities": ["teamStats", "teamSkaterStats", "powerPlayOpportunities"],
    "faceOffWinPercentage": ["teamStats", "teamSkaterStats", "faceOffWinPercentage"],
    "blocked": ["teamStats", "teamSkaterStats", "blocked"],
    "takeaways": ["teamStats", "teamSkaterStats", "takeaways"],
    "giveaways": ["teamStats", "teamSkaterStats", "giveaways"],
    "hits": ["teamStats", "teamSkaterStats", "hits"],
}


def _parseInternalData(boxScoreValue, dataList):
    subVar = boxScoreValue
    for i, listValue in enumerate(dataList):
        if listValue in subVar:
            subVar = subVar[listValue]
        else:
            break

        if i == len(dataList) - 1:
            return subVar

def _parseInternalBoxScoreTeams(teamDict):
    ret = {}

    for key, value in _staticBoxScoreData.items():
        ret[key] = _parseInternalData(teamDict, value)
    
    return ret


def parseBoxScore(boxscore):
    """Parse the box score. The box score will serve as a great starting point
    for the neural net dataset. The boxscore differs from year to year, but the
    main data points will be present.
    
    """
    homeTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["home"])
    awayTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["away"])

    return homeTeamData, awayTeamData


# Assume that the directory is in this same directory as this script
directory = '/home/barbacbd/personal/data/nhl_data/'

# Go through the list of files. Make sure that we have all players (these may
# require some corrections, see Corrections.py for more information). Retrieve
# all of the events from each game too; these will be added to the database. 
i = 1

basePath = "neural_net"

if exists(basePath):
    rmtree(basePath)
mkdir(basePath)


totalData = []
seasonSplitData = defaultdict(list)

seasonParsedEvents = {}

for root, dirs, files in os.walk(directory):

    # data to be written to a specific seasonal directory
    seasonalData = []

    for file in files:
        
        fname = path_join(root, file)

        # find the directory and parse the events for this data 
        splitPath = fname.split("/")
        year = int(splitPath[len(splitPath)-2])

        if year not in seasonParsedEvents:
            parsedHomeTeamEvents, _ = parseSeasonEvents(year)
            if None in (parsedHomeTeamEvents, ):
                # TODO: something needs to happen if there is no data ... break?
                print(f"failed to find data for {year}")
                seasonParsedEvents[year] = {}
            else:
                seasonParsedEvents[year] = parsedHomeTeamEvents

        parsedHomeTeamEvents = {}
        if year in seasonParsedEvents:
            parsedHomeTeamEvents = seasonParsedEvents[year]
        

        jsonData = None
        with open(fname) as jsonFile:
            jsonData = loads(jsonFile.read())

        if jsonData:

            localGameData = {}

            gameInfo = jsonData["gameData"]
            localGameData = {
                "gameId": gameInfo["game"]["pk"]
            }
            boxScore = jsonData["liveData"]["boxscore"]
            homeTeamData, awayTeamData = parseBoxScore(boxScore)
            
            homeTeamData.update({
                "gameId": gameInfo["game"]["pk"], 
                "teamType": "home",
                "winner": bool(homeTeamData["goals"] > awayTeamData["goals"])
            })
            awayTeamData.update({
                "gameId": gameInfo["game"]["pk"], 
                "teamType": "away",
                "winner": not homeTeamData["winner"]
            })

            if homeTeamData["teamId"] in parsedHomeTeamEvents:
                for game in parsedHomeTeamEvents[homeTeamData["teamId"]]:
                    if game.gameId == gameInfo["game"]["pk"]:
                        homeTeamData.update({
                            "attackStrength": game.homeAttackStrength, 
                            "defenseStrength": game.homeDefenseStrength,
                        })
                        awayTeamData.update({
                            "attackStrength": game.awayAttackStrength,
                            "defenseStrength": game.awayDefenseStrength,
                        })

            totalData.extend([homeTeamData, awayTeamData])
    

# generate the dataframe and add to a spreadsheet

# keys = set([x.keys() for x in totalData])
df = pd.DataFrame(totalData)

datasetFilename = "ANNDataset.xlsx"

if exists(datasetFilename):
    remove(datasetFilename)
df.to_excel(datasetFilename)