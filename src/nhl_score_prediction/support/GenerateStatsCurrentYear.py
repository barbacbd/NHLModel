
# if current file exists, read it and determine last games read and
# date/time of last read. if the day difference is greater than 1 read
# 

from datetime import datetime
from json import loads, dumps
from os.path import exists, join as path_join, dirname, abspath
from requests import get
from nhl_core.endpoints import MAX_GAME_NUMBER


def createEndpoint(year, gameNum):
    gameId = "{}02{}".format(year, str(gameNum).zfill(4))
    return "https://api-web.nhle.com/v1/gamecenter/{}/boxscore".format(gameId)


CurrYearFilename = path_join(*[dirname(abspath(__file__)), "NHLOpenSeason.json"])
BoxScoreEndpoint = "https://api-web.nhle.com/v1/gamecenter/{}/boxscore"

currentGame = 0
currentYear = datetime.now().year
# if it isn't september, the season hasn't started and should use previous year
if datetime.now().month < 9:
    currentYear -= 1

shortDate = f"{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"
jsonGameData = {
    "metadata": {
        "date": shortDate,
        "lastRegisteredGame": currentGame
    },
    "boxScores": {}
}


# Load the file if it exists, use this data as a starting point 
if exists(CurrYearFilename):
    with open(CurrYearFilename, "rb") as jsonFile:
        jsonData = loads(jsonFile.read())
    
    if jsonData:
        currentGame = jsonData["metadata"].get("lastRegisteredGame", 0)

        if datetime.strptime(jsonData["metadata"]["date"], "%Y-%m-%d") >= datetime.strptime(shortDate, "%Y-%m-%d"):
            print(f"Date in file is greater than or equal to todays date, skipping ...")
            exit(1)

        # read in the current box score data    
        jsonGameData["boxScores"].update(jsonData.get("boxScores", {}))

    if 0 > currentGame >= MAX_GAME_NUMBER:
        print(f"No more regular season games to evaluate for {currentYear}.")
        exit(1)

# increase the starting point by 1
currentGame += 1


while True:

    # read in all of the current year data. 
    try:
        jsonRequest = get(createEndpoint(currentYear, currentGame)).json()
    except:
        # assuming that the endpoint could not be reached so don't continue processing
        print("Data data received from request.")
        currentGame -= 1
        jsonGameData["metadata"]["lastRegisteredGame"] = currentGame
        break

    if datetime.strptime(jsonRequest["gameDate"], "%Y-%m-%d") >= datetime.strptime(shortDate, "%Y-%m-%d"):
        print(f"Breaking out on game {currentGame}.")
        currentGame -= 1
        jsonGameData["metadata"]["lastRegisteredGame"] = currentGame
        break

    jsonGameData["boxScores"][currentGame] = jsonRequest
    currentGame += 1

with open(CurrYearFilename, "w") as jsonFile:
    jsonFile.write(dumps(jsonGameData, indent=2))