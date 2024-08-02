from json import loads, dumps
from logging import getLogger
from os import mkdir, remove
from os.path import exists, join as path_join
from warnings import warn
from datetime import datetime
from requests import get
import pandas as pd
from nhl_core.endpoints import MAX_GAME_NUMBER
from nhl_model.enums import Version
from nhl_model.poisson import parseSeasonEvents


BASE_SAVE_DIR = "/tmp/nhl_model"

newAPIFile = lambda filename: path_join(*([BASE_SAVE_DIR, filename]))
RecoveryFilename = path_join(*[BASE_SAVE_DIR, "recovery.json"])


logger = getLogger("nhl_neural_net")


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
 # NOTE: The commented out stats below were present in older versions of the API
 # but they are not in current version of the API. These values were found to be
 # useful for predicting winners.
 #   "takeaways": ["teamStats", "teamSkaterStats", "takeaways"],
 #   "giveaways": ["teamStats", "teamSkaterStats", "giveaways"],
    "hits": ["teamStats", "teamSkaterStats", "hits"],
}

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
    spPPD = powerPlayData.split("/")
    success, opportunities = int(spPPD[0]), int(spPPD[1])
    return {
        "powerPlayPercentage": round(eval(powerPlayData) * 100.0, 2) if opportunities > 0 else 0.0,
        "powerPlayGoals": success,
        "powerPlayOpportunities": opportunities,
    }


def _parseInternalTeamData(boxScoreValue, dataList):
    """Internal function to parse the nested values from the original
    json formatted dictionary. The boxscore can be pulled from either the 
    original or new version of the API.
    """
    subVar = boxScoreValue
    for i, listValue in enumerate(dataList):
        if listValue in subVar:
            subVar = subVar[listValue]
        else:
            break

        if i == len(dataList) - 1:
            return subVar

def _parseInternalBoxScoreTeams(teamDict):
    """Internal function to parse the basic team data from the box score.
    This function is used when the data originated from the original version
    of the API.

    See `_staticBoxScoreTeamData` for the expected (nested) format.
    """
    ret = {}

    for key, value in _staticBoxScoreTeamData.items():
        ret[key] = _parseInternalTeamData(teamDict, value)

    return ret


def _parseInternalBoxScoreTeamsNew(teamDict):
    """Internal function to parse the basic team data from the box score.
    This function is used when the data originated from the new version of the
    API as the format of the boxscore is different than the original version of
    the API.

    See `_staticBoxScoreTeamDataNew` for the expected (nested) format.
    """
    ret = {}

    for key, value in _staticBoxScoreTeamDataNew.items():
        ret[key] = _parseInternalTeamData(teamDict, value)

    if "powerPlayConversion" in teamDict:
        ppData = _parsePPDataNew(teamDict["powerPlayConversion"])
        ret.update(ppData)

    return ret



def _parseInternalBoxScorePlayers(teamDict):  # pylint: disable=too-many-branches
    """In the original version of the API, the player data was added to the
    box score. Parse this data for each of the teams. The following stats are 
    present for the normal skater:
    - assists
    - powerPlayAssists
    - shortHandedAssists
    - shortHandedGoals

    The following stats are present for goalies:
    - saves
    - powerPlaySaves
    - shortHandedSaves
    - evenSaves
    - shortHandedShotsAgainst
    - evenShotsAgainst
    - powerPlayShotsAgainst
    - savePercentage
    - powerPlaySavePercentage
    - shortHandedSavePercentage
    - evenStrengthSavePercentage

    The following data is calculated and added to the final dict:
    - numGoalies
    - numPlayers
    """

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

    ret = {}
    for k, v in homeTeamData.items():
        ret[f"ht{k.capitalize()}"] = v
    for k, v in awayTeamData.items():
        ret[f"at{k.capitalize()}"] = v

    return ret


def parseBoxScoreSplit(boxscore):
    """Parse the box score. The box score will serve as a great starting point
    for the neural net dataset. The boxscore differs from year to year, but the
    main data points will be present.
    """
    homeTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["home"])
    awayTeamData = _parseInternalBoxScoreTeams(boxscore["teams"]["away"])

    homeTeamData.update(_parseInternalBoxScorePlayers(boxscore["teams"]["home"]))
    awayTeamData.update(_parseInternalBoxScorePlayers(boxscore["teams"]["away"]))

    homeTeamData["teamType"] = 1
    awayTeamData["teamType"] = 0

    return homeTeamData, awayTeamData


def _parseInternalBoxScorePlayersNew(teamDict):  # pylint: disable=too-many-branches
    """In the new version of the API, the player data was added to the
    box score. Parse this data for each of the teams. In the original API
    most of the data was present, but more of the data must be calculated
    here. 
    
    The following stats are present for the normal skater:
    - assists
    - powerPlayAssists
    - shortHandedAssists
    - shortHandedGoals

    The following stats are present for goalies:
    - saves
    - powerPlaySaves
    - shortHandedSaves
    - evenSaves
    - shortHandedShotsAgainst
    - evenShotsAgainst
    - powerPlayShotsAgainst
    - savePercentage
    - powerPlaySavePercentage
    - shortHandedSavePercentage
    - evenStrengthSavePercentage
    - shortHandedGoalsAgainst

    The following data is calculated and added to the final dict:
    - numGoalies
    - numPlayers
    """
    numPlayers = 0
    numGoalies = 0

    # Setting all to None so that we can figure out where stats are missing later

    skaterDict = {
        "assists": 0,
        "shortHandedGoals": 0,
        "shortHandedAssists": 0,
        "powerPlayAssists": 0
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
        "evenStrengthSavePercentage": 0,
        "shortHandedGoalsAgainst": 0
    }

    for playerType, playerValues in teamDict.items():

        if playerType in ("forwards", "defense",):
            for playerData in playerValues:
                spTOI = playerData["toi"].split(":")
                timeOnIce = int(spTOI[0]) * 60 + int(spTOI[1])
                if timeOnIce > 0:
                    numPlayers += 1
                    skaterDict['assists'] += playerData.get("assists", 0)
                    skaterDict['shortHandedGoals'] += playerData.get("shorthandedGoals", 0)
                    skaterDict["powerPlayAssists"] += playerData.get("powerPlayPoints", 0) - \
                         playerData.get("powerPlayGoals", 0)
                    skaterDict["shortHandedAssists"] += playerData.get("shPoints", 0) - \
                        playerData.get("shorthandedGoals", 0)

        elif playerType in ("goalies",):
            for playerData in playerValues:
                spTOI = playerData["toi"].split(":")
                timeOnIce = int(spTOI[0]) * 60 + int(spTOI[1])
                if timeOnIce > 0:
                    numGoalies += 1
                    spPD = playerData["evenStrengthShotsAgainst"].split("/")
                    if len(spPD) == 2:
                        goalieDict["evenShotsAgainst"] = goalieDict["evenShotsAgainst"] + int(spPD[1])
                        goalieDict["saves"] = goalieDict["saves"] + int(spPD[0])
                        goalieDict["evenSaves"] = goalieDict["evenSaves"] + int(spPD[0])

                    spPD = playerData["powerPlayShotsAgainst"].split("/")
                    if len(spPD) == 2:
                        goalieDict["powerPlayShotsAgainst"] += int(spPD[1])
                        goalieDict["saves"] += int(spPD[0])
                        goalieDict["powerPlaySaves"] += int(spPD[0])

                    spPD = playerData["shorthandedShotsAgainst"].split("/")
                    if len(spPD) == 2:
                        goalieDict["shortHandedShotsAgainst"] += int(spPD[1])
                        goalieDict["saves"] += int(spPD[0])
                        goalieDict["shortHandedSaves"] += int(spPD[0])

    totalShotsAgainst = goalieDict["evenShotsAgainst"] + \
        goalieDict["powerPlayShotsAgainst"] + goalieDict["shortHandedShotsAgainst"]

    goalieDict.update({
        "savePercentage":
            round(float(goalieDict["saves"]) / float(totalShotsAgainst) * 100.0, 2)
                if totalShotsAgainst > 0 else 0.0,
        "powerPlaySavePercentage":
            round(float(goalieDict["powerPlaySaves"]) /
                  float(goalieDict["powerPlayShotsAgainst"]) * 100.0, 2) if \
                goalieDict["powerPlayShotsAgainst"] > 0 else 0.0,
        "shortHandedSavePercentage":
            round(float(goalieDict["shortHandedSaves"]) /
                  float(goalieDict["shortHandedShotsAgainst"]) * 100.0, 2) if \
                goalieDict["shortHandedShotsAgainst"] > 0 else 0.0,
        "evenStrengthSavePercentage":
            round(float(goalieDict["evenSaves"]) /
                  float(goalieDict["evenShotsAgainst"]) * 100.0, 2) if \
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
    def _verifyExists(bs, listOfVars):
        tmp = bs
        for var in listOfVars:
            if var not in tmp:
                return False
            tmp = tmp[var]
        return True

    homeTeamData = _parseInternalBoxScoreTeamsNew(boxscore["homeTeam"])
    awayTeamData = _parseInternalBoxScoreTeamsNew(boxscore["awayTeam"])

    if _verifyExists(boxscore, ["boxscore", "playerByGameStats", "homeTeam"]):
        homeTeamData.update(_parseInternalBoxScorePlayersNew(
            boxscore["boxscore"]["playerByGameStats"]["homeTeam"]
        ))

    if _verifyExists(boxscore, ["boxscore", "playerByGameStats", "awayTeam"]):
        awayTeamData.update(_parseInternalBoxScorePlayersNew(
            boxscore["boxscore"]["playerByGameStats"]["awayTeam"]
        ))

    ret = {}
    for k, v in homeTeamData.items():
        ret[f"ht{k.capitalize()}"] = v
    for k, v in awayTeamData.items():
        ret[f"at{k.capitalize()}"] = v

    if "id" in boxscore:
        ret.update({
            "gameId": boxscore["id"], 
            "winner": bool(ret["htGoals"] > ret["atGoals"])
        })

    if "gameDate" in boxscore:
        dateInfo = boxscore["gameDate"].split("-")
        ret.update({"year": dateInfo[0], "month": dateInfo[1], "day": dateInfo[2]})

    return ret


def parseBoxScoreNewSplit(boxscore):
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

    homeTeamData["gameId"] = boxscore["id"]
    awayTeamData["gameId"] = boxscore["id"]

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

    Example usage: 
    # The following calculates the wins/losses win percentage, any win/lose streak, total 
    # win percentage (season), and the home or away win percentage (based on the type of game
    # if the team is home or away). These are extra statistics that are not provided by the
    # box score.
    # NOTE: these calculations should be run before the current game information is added
    wins, losses, winPercent, _ = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10)
    _, _, totalWinPercent, streak = parseRecentData(teamRecentWinPercents[homeTeamData['teamId']])
    _, _, winPercentHomeRecent, _ = 
        parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], 10, "H")
    _, _, totalWinPercentHome, _ = 
        parseRecentData(teamRecentWinPercents[homeTeamData['teamId']], None, "H")
    homeTeamData.update({
        "recentWinPercent": winPercent,
        "totalWinPercent": totalWinPercent,
        "gameTypeWinPercentRecent": winPercentHomeRecent,
        "gameTypeWinPercent": totalWinPercentHome,
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


def _createEndpoint(year, gameNum):
    """Create an endpoint for a box score of a specific game using the new API.
    """
    gameId = "{}02{}".format(year, str(gameNum).zfill(4))
    return "https://api-web.nhle.com/v1/gamecenter/{}/boxscore".format(gameId)


def pullDatasetNewAPI(year):
    """Pull all of the regular season data using the new API. Save this data to a file.
    """
    currentGame = 0
    _year = year

    if _year == datetime.now().year:
        # if it isn't september, the season hasn't started and should use previous year
        if 5 < datetime.now().month < 9:
            logger.warning("the current season may not have started, please check back later")
            return

    currYearFilename = newAPIFile(f"{_year}-NHL-season.json")
    logger.debug(currYearFilename)

    shortDate = f"{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"
    jsonGameData = {
        "metadata": {
            "date": shortDate,
            "lastRegisteredGame": currentGame,
            "year": _year
        },
        "boxScores": {}
    }

    jsonData = None

    # Load the file if it exists, use this data as a starting point
    if exists(currYearFilename):
        with open(currYearFilename, "rb") as jsonFile:
            jsonData = loads(jsonFile.read())
    elif exists(RecoveryFilename):
        logger.debug(f"reading data from recovery file {RecoveryFilename}")
        with open(RecoveryFilename, "rb") as jsonFile:
            jsonData = loads(jsonFile.read())

    if jsonData:
        currentGame = jsonData["metadata"].get("lastRegisteredGame", 0)
        # read in the current box score data
        jsonGameData["boxScores"].update(jsonData.get("boxScores", {}))

    if 0 > currentGame >= MAX_GAME_NUMBER:
        logger.error(f"No more regular season games to evaluate for {_year}.")
        return currYearFilename

    # increase the starting point by 1
    currentGame += 1

    logger.debug(f"current game loaded from file = {currentGame}")

    while currentGame <= MAX_GAME_NUMBER:

        # read in all of the current year data.
        try:
            endpointPath = _createEndpoint(_year, currentGame)
            logger.debug(f"Looking for {endpointPath}")
            jsonRequest = get(endpointPath).json()
        except:
            # assuming that the endpoint could not be reached so don't continue processing
            logger.debug("No data received from request.")
            currentGame -= 1
            jsonGameData["metadata"]["lastRegisteredGame"] = currentGame
            break

        if datetime.strptime(
            jsonRequest["gameDate"], "%Y-%m-%d"
        ) >= datetime.strptime(shortDate, "%Y-%m-%d"):
            logger.debug(f"Breaking out on game {currentGame}.")
            currentGame -= 1
            jsonGameData["metadata"]["lastRegisteredGame"] = currentGame
            break

        jsonGameData["boxScores"][currentGame] = jsonRequest
        currentGame += 1

    if not exists(BASE_SAVE_DIR):
        mkdir(BASE_SAVE_DIR)

    try:
        with open(currYearFilename, "w") as jsonFile:
            jsonFile.write(dumps(jsonGameData, indent=2))
            logger.debug(f"data written to {currYearFilename}")

        if exists(RecoveryFilename):
            logger.debug(f"removing recovery file {RecoveryFilename}")
            remove(RecoveryFilename)
    except FileNotFoundError:
        logger.warning(f"failed to save file {currYearFilename}, writing to {RecoveryFilename}")
        with open(RecoveryFilename, "w") as jsonFile:
            jsonFile.write(dumps(jsonGameData, indent=2))

        return None  # error occurred - skip returning the recovery file

    return currYearFilename


def generateDataset(version, startYear, endYear, validFiles=[]):
    """Generate the Dataset that will be used as input to the neural net. This
    ultimately becomes the training data for the model. 
    """
    if not exists(BASE_SAVE_DIR):
        logger.debug(f"creating base directory {BASE_SAVE_DIR}")
        mkdir(BASE_SAVE_DIR)

    totalData = []

    seasonParsedEvents = {}

    if version == Version.OLD.value:
        warn("generating a dataset using the old API")

        for fname in validFiles:

            # find the directory and parse the events for this data
            splitPath = fname.split("/")
            year = int(splitPath[len(splitPath)-2])

            if year not in seasonParsedEvents:
                parsedHomeTeamEvents, _ = parseSeasonEvents(year)
                if None in (parsedHomeTeamEvents, ):
                    logger.warning(f"failed to find data for {year}")
                    seasonParsedEvents[year] = {}
                else:
                    seasonParsedEvents[year] = parsedHomeTeamEvents

            parsedHomeTeamEvents = seasonParsedEvents.get(year, {})

            jsonData = None
            with open(fname) as jsonFile:
                jsonData = loads(jsonFile.read())

            if jsonData:

                gameInfo = jsonData["gameData"]
                boxScore = jsonData["liveData"]["boxscore"]
                gameData = parseBoxScore(boxScore)

                gameData.update({
                    "gameId": gameInfo["game"]["pk"], 
                    "winner": bool(gameData["htGoals"] > gameData["atGoals"])
                })

                totalData.append(gameData)
    else:
        for filename in validFiles:
            jsonData = None
            with open(filename, "rb") as jsonFile:
                jsonData = loads(jsonFile.read())

            # remove all data after it is loaded into memory
            logger.debug(f"removing file {filename}")
            # remove(filename)

            # grab all boxscores from all files that were created
            if jsonData:
                for _, boxscore in jsonData["boxScores"].items():
                    totalData.append(parseBoxScoreNew(boxscore))

    # generate the dataframe and add to a spreadsheet
    df = pd.DataFrame(totalData)

    datasetFilename = newAPIFile(f"ANNDataset-{startYear}-{endYear}.xlsx")

    logger.debug(df.isna().sum())

    if exists(datasetFilename):
        remove(datasetFilename)
    df.to_excel(datasetFilename)
