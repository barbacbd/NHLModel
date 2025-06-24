from json import dumps
from logging import getLogger
from requests import get
from nhl_model.dataset import (
    pullPlayoffDataNewAPI, 
    MAX_PLAYOFF_GAMES_PER_SEQUENCE, 
    MAX_PLAYOFF_ROUNDS
)


logger = getLogger("nhl_neural_net")


def createPlayoffMatchup(teamData, higherSeed, lowerSeed):
    '''NHL playoff rounds are a maximum of 7 games per round where the format
    is 2-2-1-1-1. This means that the higher seed will have the first two
    games at home, then the lower seed will have two home games. These games are
    guaranteed. The last three (optional) games will rotate a home game for the higher
    then lower seed. The winner of the series is the first to win 4 games. 
    '''
    higherSeedComplete = None
    lowerSeedComplete = None

    for teamInfo in teamData["data"]:
        if teamInfo["triCode"] == higherSeed:
            higherSeedComplete = teamInfo
        if teamInfo["triCode"] == lowerSeed:
            lowerSeedComplete = teamInfo

    if None in (higherSeedComplete, lowerSeedComplete):
        return
    
    games = []
    for x in range(MAX_PLAYOFF_GAMES_PER_SEQUENCE):
        if x in [0,1,4,6]:
            games.append({
                "homeTeam": higherSeedComplete,
                "awayTeam": lowerSeedComplete
            })
        else:
            games.append({
                "homeTeam": lowerSeedComplete,
                "awayTeam": higherSeedComplete
            })

    return {"games": games}


def parsePlayoffMetadata(jsonData):
    '''Parse the top and bottom seed out of the playoff metadata.
    '''
    #print(dumps(jsonData, indent=2))
    #exit(1)
    
    if "teams" in jsonData:
        # It is also possible to use the
        # jsonData["teams"]["topSeed"]["commonName"]["default"]
        return jsonData["teams"]["topSeed"]["tricode"], jsonData["teams"]["bottomSeed"]["tricode"]

    return None, None


def getPlayoffMetadata(year, currentRound=1):
    '''Playoff metadata will provide information about the matchups for the year and the
    round provided. The metadata only provides basic information such as the higher and
    lower seeds.
    '''
    if 0 >= currentRound > MAX_PLAYOFF_ROUNDS:
        return

    matchups = 2**(MAX_PLAYOFF_ROUNDS-currentRound)
    
    asciiValueStart = 97 + sum([2**(MAX_PLAYOFF_ROUNDS-x) for x in range(1, currentRound)])
    # The metadata for nhl playoff data is accessible via the letter for the matchup.
    # Based on the round of the playoffs we can find the letters expected. For instance
    # round 2 has 4 games, the first round has 8 games. Round 1 consists of letters
    # 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', so the letters for this round start at 'i'.
    letters = [chr(asciiValueStart + x) for x in range(0, matchups)] 

    matchupData = {}

    teamData = getTeamInfo()
    if teamData is None:
        return

    for letter in letters:
        try:
            endpoint = f"https://api-web.nhle.com/v1/meta/playoff-series/{year}/{letter}"
            jsonRequest = get(endpoint).json()
            topSeed, bottomSeed = parsePlayoffMetadata(jsonRequest)
            logger.debug(
                f"{year} playoffs round {currentRound} matchup "
                f"{letter} - top seed = {topSeed}, bottom seed = {bottomSeed}"
            )

            if topSeed is not None and bottomSeed is not None:
                matchupData[str(letter)] = createPlayoffMatchup(teamData, topSeed, bottomSeed)
        except:
            # assuming that the endpoint could not be reached so don't continue processing
            logger.error(f"No playoff data received for round {currentRound} of {year} - matchup {letter}.")
        
    return matchupData


def getTeamInfo():
    '''Get all team info. The team info will contain the abbreviations, full names, and 
    team ids. The playoff metadata does not provide team ids which are required for
    certain predictions.
    '''
    endpoint = "https://api.nhle.com/stats/rest/en/team"
    jsonRequest = None
    
    try:
        jsonRequest = get(endpoint).json()
    except:
        logger.error("No team data found")
        return None

    return jsonRequest
