from collections import defaultdict
from json import loads
import os
from os import mkdir, remove
from os.path import exists, join as path_join, dirname, abspath
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

# TODO: Need to read in the new data. And grab the data below if it exists. Create
# the dataframe and/or spreadsheet for the data. 
_staticBoxScoreTeamDataNew = {
    "teamId": ["id"],
    "teamName": ["name", "default"],
    "triCode": ["abbrev"],
    "goals": ["score"],
    "pim": ["pim"],
    "shots": ["sog"],
    "faceOffWinPercentage": ["faceoffWinningPctg"],
    "blocked": ["blocks"],
    "hits": ["hits"],
}

def _parsePPDataNew(powerPlayData):
    """Parse the power play information from the "new" boxscore data that 
    can be retrieved from the new API.
    """
    sp = powerPlayData.split("/")
    success, opportunities = int(sp[0]), int(sp[1])
    return {
        "powerPlayPercentage": round(eval(powerPlayData) * 100.0, 2) if opportunities > 0 else 0.0,
        "powerPlayGoals": success,
        "powerPlayOpportunities": opportunities,
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


def _parseInternalBoxScoreTeamsNew(teamDict):
    ret = {}

    for key, value in _staticBoxScoreTeamDataNew.items():
        ret[key] = _parseInternalTeamData(teamDict, value)
    
    ppData = _parsePPDataNew(teamDict["powerPlayConversion"])
    ret.update(ppData)

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


def _parseInternalBoxScorePlayersNew(teamDict):
    numPlayers = 0
    numGoalies = 0

    # Setting all to None so that we can figure out where stats are missing later

    skaterDict = {
        "assists": 0,
    }
    goalieDict = {
        "saves": 0,
        "powerPlaySaves": 0,
        "shortHandedSaves": 0,
        "evenSaves": 0,
        "shortHandedShotsAgainst": 0,
        "evenShotsAgainst": 0,
        "powerPlayShotsAgainst": 0,
        "savePercentage": 0,
        "powerPlaySavePercentage": 0,
        "shortHandedSavePercentage": 0,
        "evenStrengthSavePercentage": 0
    }

    for playerType, playerValues in teamDict.items():

        if playerType in ("forwards", "defense",):
            for playerData in playerValues:
                spTOI = playerData["toi"].split(":")
                timeOnIce = int(spTOI[0]) * 60 + int(spTOI[1])
                if timeOnIce > 0:
                    numPlayers += 1
                    skaterDict['assists'] += playerData["assists"]

        elif playerType in ("goalies",):
            for playerData in playerValues:
                spTOI = playerData["toi"].split(":")
                timeOnIce = int(spTOI[0]) * 60 + int(spTOI[1])
                if timeOnIce > 0:
                    numGoalies += 1
                    sp = playerData["evenStrengthShotsAgainst"].split("/")
                    if len(sp) == 2:
                        goalieDict["evenShotsAgainst"] = goalieDict["evenShotsAgainst"] + int(sp[1])
                        goalieDict["saves"] = goalieDict["saves"] + int(sp[0])
                        goalieDict["evenSaves"] = goalieDict["evenSaves"] + int(sp[0])

                    sp = playerData["powerPlayShotsAgainst"].split("/")
                    if len(sp) == 2:
                        goalieDict["powerPlayShotsAgainst"] += int(sp[1])
                        goalieDict["saves"] += int(sp[0])
                        goalieDict["powerPlaySaves"] += int(sp[0])

                    sp = playerData["shorthandedShotsAgainst"].split("/")
                    if len(sp) == 2:
                        goalieDict["shortHandedShotsAgainst"] += int(sp[1])
                        goalieDict["saves"] += int(sp[0])
                        goalieDict["shortHandedSaves"] += int(sp[0])

    totalShotsAgainst = goalieDict["evenShotsAgainst"] + \
        goalieDict["powerPlayShotsAgainst"] + goalieDict["shortHandedShotsAgainst"]

    goalieDict.update({
        "savePercentage": 
            round(float(goalieDict["saves"]) / float(totalShotsAgainst) * 100.0, 2) if totalShotsAgainst > 0 else 0.0,
        "powerPlaySavePercentage": 
            round(float(goalieDict["powerPlaySaves"]) / float(goalieDict["powerPlayShotsAgainst"]) * 100.0, 2) if \
                goalieDict["powerPlayShotsAgainst"] > 0 else 0.0,
        "shortHandedSavePercentage": 
            round(float(goalieDict["shortHandedSaves"]) / float(goalieDict["shortHandedShotsAgainst"]) * 100.0, 2) if \
                goalieDict["shortHandedShotsAgainst"] > 0 else 0.0,
        "evenStrengthSavePercentage": 
            round(float(goalieDict["evenSaves"]) / float(goalieDict["evenShotsAgainst"]) * 100.0, 2) if \
                goalieDict["evenShotsAgainst"] > 0 else 0.0,
    })

    skaterDict.update(goalieDict)
    skaterDict["numGoalies"] = numGoalies
    skaterDict["numPlayers"] = numPlayers

    return skaterDict


def parseBoxScoreNew(boxscore):
    """Parse the box score (new version). This version of the box score should be read
    from the NHLOpenSeason.json file. The box score will serve as a great starting point
    for the neural net dataset. The boxscore differs from year to year, but the
    main data points will be present.
    """
    homeTeamData = _parseInternalBoxScoreTeamsNew(boxscore["homeTeam"])
    awayTeamData = _parseInternalBoxScoreTeamsNew(boxscore["awayTeam"])

    homeTeamData.update(_parseInternalBoxScorePlayersNew(
        boxscore["boxscore"]["playerByGameStats"]["homeTeam"]
    ))
    awayTeamData.update(_parseInternalBoxScorePlayersNew(
        boxscore["boxscore"]["playerByGameStats"]["awayTeam"]
    ))

    homeTeamData.update({
        "gameId": boxscore["id"], 
        "teamType": 1,
        "winner": bool(homeTeamData["goals"] > awayTeamData["goals"])
    })
    awayTeamData.update({
        "gameId": boxscore["id"], 
        "teamType": 0,
        "winner": not homeTeamData["winner"]
    })

    return homeTeamData, awayTeamData


def parseRecentData(data, maxRecords=None, gameType=""):
    """Parse the results of games and return the wins, losses, winPercent, streak
    from that period indicated by maxRecords. The winPercent will always be greater
    than or equal to 0.0. The streak will be a positive number when there is a Win Streak
    in progress, and a negative number when there is a Losing Streak in progress.
    
    The information stored in `data` is expected to be in the format 
    ex: [["W", "H"], ["L", "A"], ...] where `data` is a list of
    data points that contain the record "W" for win and "L" for loss as the first
    index followed by "H" for home and "A" for away in the second index.

    NOTE: the data should be stored in order from most recent (index 0) to furthest
    away in time (index n-1).

    The `maxRecords` indicates the period of data to parse records for. For instance 
    `maxRecords` of 10 would parse the last 10 games.

    The `gameType` should be empty for home AND away games to be parsed together. The
    `gameType` should be "H" for home or "A" for away games respectively. Other values 
    DO NOT raise an error, there will just be no records found and the results will be
    skewed/invalid.
    """
    _maxRecords = len(data) if maxRecords is None else maxRecords

    if gameType == "":
        x = [_[0] for _ in data[:_maxRecords]]
    else:
        x = []
        for v in data:
            if v[1] == gameType:
                x.append(v[0])
            
            if len(x) == _maxRecords:
                break

    wins = x.count("W")
    losses = x.count("L")
    winPercent = round((float(wins) / float(len(x))) * 100.0, 2) if len(x) > 0 else 0.0

    streak = 0
    if len(x) > 0:
        # streak is positive for W and negative for L
        streakType = x[0]
        streak = 1
        for v in x[1:]:
            if v != streakType:
                break
            streak += 1
        
        if streakType == "L":
            streak = -streak

    return wins, losses, winPercent, streak


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
    validFiles = []
    output = {}
    questions = [
        inquirer.List('version', message="Select a version of data", choices=["new", "old"])
    ]
    answers = inquirer.prompt(questions)
    output["version"] = answers["version"]

    if answers["version"] == "old":
        # Ask for the year/season for analysis
        currentYear = datetime.now().year
        questions = [
            inquirer.Text('startYear', message="Enter the year for the analysis to start.", default=2000),
            inquirer.Text('endYear', message="Enter the year for the analysis to end.", default=currentYear-1),
        ]
        answers = inquirer.prompt(questions)
        startYear = int(answers["startYear"])
        endYear = int(answers["endYear"])
        startYear, endYear = min([startYear, endYear]), max([startYear, endYear])
        output.update({"startYear": startYear, "endYear": endYear})

        for root, dirs, files in os.walk(directory):
            sp = root.split("/")
            try:
                if startYear <= int(sp[len(sp)-1]) <= endYear:
                    validFiles.extend([path_join(root, f) for f in files])
            except:
                pass
    else:
        # This is new so read the "NHLOpenSeason.json" file
        validFiles.append(
            path_join(*[dirname(abspath(__file__)), "NHLOpenSeason.json"])
        )

    return output, validFiles


# data to be added to a dateframe and output to an excel file.
totalData = []

seasonParsedEvents = {}
teamRecentWinPercents = defaultdict(list)

parsedOutput, validFiles = parseArguments()
version = parsedOutput["version"]
startYear = parsedOutput.get("startYear", None)
endYear = parsedOutput.get("endYear", None)

if version == "old":
    for fname in validFiles:

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
            
            # The following calculates the wins/losses win percentage, any win/lose streak, total 
            # win percentage (season), and the home or away win percentage (based on the type of game
            # if the team is home or away). These are extra statistics that are not provided by the
            # box score.
            # NOTE: these calculations should be run before the current game information is added
            wins, losses, winPercent, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10)
            _, _, totalWinPercent, streak = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']])
            _, _, winPercentHomeRecent, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10, "H")
            _, _, totalWinPercentHome, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], None, "H")
            homeTeamData.update({
                "recentWinPercent": winPercent,
                "totalWinPercent": totalWinPercent,
                "gameTypeWinPercentRecent": winPercentHomeRecent,
                "gameTypeWinPercent": totalWinPercentHome,
                "streak": streak
            })
            wins, losses, winPercent, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], 10)
            _, _, totalWinPercent, streak = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']])
            _, _, winPercentAwayRecent, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], 10, "A")
            _, _, totalWinPercentAway, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], None, "A")
            awayTeamData.update({
                "recentWinPercent": winPercent,
                "totalWinPercent": totalWinPercent,
                "gameTypeWinPercentRecent": winPercentAwayRecent,
                "gameTypeWinPercent": totalWinPercentAway,
                "streak": streak
            })

            # Now that the data above has been added to the list of features that _could_ determine
            # the outcome of a game, add the actual outcome of the game and home vs away value
            # to be used for the next calculations.
            if homeTeamData["goals"] > awayTeamData["goals"]:
                teamRecentWinPercents[homeTeamData["teamId"]].insert(0, ["W", "H"])
                teamRecentWinPercents[awayTeamData["teamId"]].insert(0, ["L", "A"])
            else:
                teamRecentWinPercents[homeTeamData["teamId"]].insert(0, ["L", "H"])
                teamRecentWinPercents[awayTeamData["teamId"]].insert(0, ["W", "A"])

            # When performing the poisson distribution, an attack vs defense score was created.
            # This _could_ be a useful statistic for predicting future game outcomes. The attack and
            # defense score can be calculated for any team at any time during the season, so this
            # means that there is less estimation involved.
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
else:
    # new version
    jsonData = None
    with open(validFiles[0]) as jsonFile:
        jsonData = loads(jsonFile.read())

    year = None
    for k, v in jsonData["boxScores"].items():
        year = int(str(v["id"])[:4])
        break
    startYear = year
    endYear = year

    # start the new dictionary of data
    seasonParsedEvents[year] = {}
    parsedHomeTeamEvents = {}

    localGameData = {}
    for _, boxscore in jsonData["boxScores"].items():
        homeTeamData, awayTeamData = parseBoxScoreNew(boxscore)

        # print(homeTeamData)
        # print(awayTeamData)
    
        # The following calculates the wins/losses win percentage, any win/lose streak, total 
        # win percentage (season), and the home or away win percentage (based on the type of game
        # if the team is home or away). These are extra statistics that are not provided by the
        # box score.
        # NOTE: these calculations should be run before the current game information is added
        wins, losses, winPercent, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10)
        _, _, totalWinPercent, streak = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']])
        _, _, winPercentHomeRecent, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10, "H")
        _, _, totalWinPercentHome, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], None, "H")
        homeTeamData.update({
            "recentWinPercent": winPercent,
            "totalWinPercent": totalWinPercent,
            "gameTypeWinPercentRecent": winPercentHomeRecent,
            "gameTypeWinPercent": totalWinPercentHome,
            "streak": streak
        })
        wins, losses, winPercent, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], 10)
        _, _, totalWinPercent, streak = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']])
        _, _, winPercentAwayRecent, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], 10, "A")
        _, _, totalWinPercentAway, _ = parseRecentData(teamRecentWinPercents[awayTeamData['teamId']], None, "A")
        awayTeamData.update({
            "recentWinPercent": winPercent,
            "totalWinPercent": totalWinPercent,
            "gameTypeWinPercentRecent": winPercentAwayRecent,
            "gameTypeWinPercent": totalWinPercentAway,
            "streak": streak
        })

        # Now that the data above has been added to the list of features that _could_ determine
        # the outcome of a game, add the actual outcome of the game and home vs away value
        # to be used for the next calculations.
        if homeTeamData["goals"] > awayTeamData["goals"]:
            teamRecentWinPercents[homeTeamData["teamId"]].insert(0, ["W", "H"])
            teamRecentWinPercents[awayTeamData["teamId"]].insert(0, ["L", "A"])
        else:
            teamRecentWinPercents[homeTeamData["teamId"]].insert(0, ["L", "H"])
            teamRecentWinPercents[awayTeamData["teamId"]].insert(0, ["W", "A"])

        # When performing the poisson distribution, an attack vs defense score was created.
        # This _could_ be a useful statistic for predicting future game outcomes. The attack and
        # defense score can be calculated for any team at any time during the season, so this
        # means that there is less estimation involved.
        # if homeTeamData["teamId"] in parsedHomeTeamEvents:
        #     for game in parsedHomeTeamEvents[homeTeamData["teamId"]]:
        #         if game.gameId == gameInfo["game"]["pk"]:
        #             homeTeamData.update({
        #                 "attackStrength": game.homeAttackStrength, 
        #                 "defenseStrength": game.homeDefenseStrength,
        #             })
        #             awayTeamData.update({
        #                 "attackStrength": game.awayAttackStrength,
        #                 "defenseStrength": game.awayDefenseStrength,
        #             })

        totalData.extend([homeTeamData, awayTeamData])



# generate the dataframe and add to a spreadsheet

# keys = set([x.keys() for x in totalData])
df = pd.DataFrame(totalData)

datasetFilename = f"ANNDataset-{startYear}-{endYear}.xlsx"

print(df.isna().sum())

if exists(datasetFilename):
    remove(datasetFilename)
df.to_excel(datasetFilename)


# # predict the optimal number of features 
# from sklearn.metrics import f1_score
# from sklearn.ensemble import RandomForestClassifier


# output = df["winner"]

# # Drop the output from the Dataframe, leaving the only data left as
# # the dataset to train.
# df.drop(labels=["winner"], axis=1,inplace=True)
# df.drop(labels=[
#         "teamId",
#         "teamName", 
#         "triCode", 
#     ], 
#     axis=1, 
#     inplace=True
# )
