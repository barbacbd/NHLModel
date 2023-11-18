from collections import defaultdict
from json import loads
import os
from os import mkdir, remove
from os.path import exists, join as path_join
from shutil import rmtree
from nhl_score_prediction.poisson.poisson import parseSeasonEvents
import pandas as pd
import inquirer
from datetime import datetime


_staticBoxScoreTeamData = {
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


def _parseInternalTeamData(boxScoreValue, dataList):
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

    for key, value in _staticBoxScoreTeamData.items():
        ret[key] = _parseInternalTeamData(teamDict, value)
    
    return ret


def _parseInternalBoxScorePlayers(teamDict):

    numPlayers = 0
    numGoalies = 0

    # Setting all to None so that we can figure out where stats are missing later

    skaterDict = {
        "assists": None,
        "powerPlayAssists": None,
        "shortHandedAssists": None,
        "shortHandedGoals": None,
    }
    goalieDict = {
        "saves": None,
        "powerPlaySaves": None,
        "shortHandedSaves": None,
        "evenSaves": None,
        "shortHandedShotsAgainst": None,
        "evenShotsAgainst": None,
        "powerPlayShotsAgainst": None,
        "savePercentage": None,
        "powerPlaySavePercentage": None,
        "shortHandedSavePercentage": None,
        "evenStrengthSavePercentage": None
    }

    for _, value in teamDict["players"].items():
        if "skaterStats" in value["stats"]:
            for k, v in value["stats"]["skaterStats"].items():
                if k in skaterDict:
                    if skaterDict[k] is None:
                        skaterDict[k] = 0
                    skaterDict[k] += v
            
            numPlayers += 1

        elif "goalieStats" in value["stats"]:
            for k, v in value["stats"]["goalieStats"].items():
                if k in goalieDict:
                    if goalieDict[k] is None:
                        goalieDict[k] = 0
                    goalieDict[k] += v
            
            numGoalies += 1

    # print(f"skaters = {numPlayers}, goalies = {numGoalies}")

    if numGoalies > 0:
        # average the percentages
        for k, v in goalieDict.items():
            if "percent" in k.lower():
                if goalieDict[k] is not None:
                    goalieDict[k] = v / numGoalies

        skaterDict.update(goalieDict)
        skaterDict["numGoalies"] = numGoalies

    skaterDict.update({"numPlayers": numPlayers})


    return skaterDict


def parseBoxScore(boxscore):
    """Parse the box score. The box score will serve as a great starting point
    for the neural net dataset. The boxscore differs from year to year, but the
    main data points will be present.
    
    """
    homeTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["home"])
    awayTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["away"])

    homeTeamData.update(_parseInternalBoxScorePlayers(boxscore["teams"]["home"]))
    awayTeamData.update(_parseInternalBoxScorePlayers(boxscore["teams"]["away"]))

    return homeTeamData, awayTeamData


# Assume that the directory is in this same directory as this script
directory = '/home/barbacbd/personal/data/nhl_data/'

# Go through the list of files. Make sure that we have all players (these may
# require some corrections, see Corrections.py for more information). Retrieve
# all of the events from each game too; these will be added to the database. 
i = 1


def parseArguments():
    """Parse the arguements for the program by reading in the static file that
    contains the basic statistics for all teams and all seasons.
    """
    # Ask for the year/season for analysis
    currentYear = datetime.now().year
    questions = [
        inquirer.Text('startYear', message="Enter the year for the analysis to start.", default=2000),
        inquirer.Text('endYear', message="Enter the year for the analysis to end.", default=currentYear-1),
    ]
    answers = inquirer.prompt(questions)
    startYear = int(answers["startYear"])
    endYear = int(answers["endYear"])

    return startYear, endYear



basePath = "neural_net"

if exists(basePath):
    rmtree(basePath)
mkdir(basePath)


startYear, endYear = parseArguments()
startYear, endYear = min([startYear, endYear]), max([startYear, endYear])

# data to be added to a dateframe and output to an excel file.
totalData = []

seasonParsedEvents = {}


validFiles = []
for root, dirs, files in os.walk(directory):

    sp = root.split("/")
    try:
        if startYear <= int(sp[len(sp)-1]) <= endYear:
            validFiles.extend([path_join(root, f) for f in files])
    except:
        pass

for fname in validFiles:

    # print(fname)

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
            "teamType": 1,
            "winner": bool(homeTeamData["goals"] > awayTeamData["goals"])
        })
        awayTeamData.update({
            "gameId": gameInfo["game"]["pk"], 
            "teamType": 0,
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

datasetFilename = f"ANNDataset-{startYear}-{endYear}.xlsx"

print(df.isna().sum())

if exists(datasetFilename):
    remove(datasetFilename)
df.to_excel(datasetFilename)