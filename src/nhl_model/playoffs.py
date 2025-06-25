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


def determineSeeds(standings, teamOneTriCode, teamTwoTriCode):
    '''Determine the high/low seed from the standings.

    When the teams have the same standings (in the event of the finals), 
    then None, None should be returned. This indicates that both are the same.
    '''
    teamOneStandingLeague = -1
    teamTwoStandingLeague = -1

    for conf in standings:
        if teamOneTriCode in standings[conf]:
            teamOneStandingLeague = standings[conf][teamOneTriCode]["league"]
        if teamTwoTriCode in standings[conf]:
            teamTwoStandingLeague = standings[conf][teamTwoTriCode]["league"]

    if teamOneStandingLeague < teamTwoStandingLeague:
        return teamOneTriCode, teamTwoTriCode
    return teamTwoTriCode, teamOneTriCode


def prepareResultsForNextRound(teamData, standings, previousRoundResults, currentRound):
    '''Prepare the results from the previous round for the current round of the 
    playoffs. The intention is to attempt to predict the winner of the stanley cup.
    '''
    previousRound = currentRound - 1

    previousMatchups = 2**(MAX_PLAYOFF_ROUNDS-previousRound)
    asciiValueStart = 97 + sum([2**(MAX_PLAYOFF_ROUNDS-x) for x in range(1, previousRound)])
    asciiValueEnd = asciiValueStart + previousMatchups

    winners = {}
    for letter in previousRoundResults:
        winners[letter] = max(previousRoundResults[letter], key=previousRoundResults[letter].get)

    matchups = {}
    asciiLetterValue = 97 + sum([2**(MAX_PLAYOFF_ROUNDS-x) for x in range(1, currentRound)])
    for x in range(asciiValueStart, asciiValueEnd, 2):
        # print(f"{winners[str(chr(x))]} vs {winners[str(chr(x+1))]}")

        higherSeed, lowerSeed = determineSeeds(standings, winners[str(chr(x))], winners[str(chr(x+1))])
        matchups[str(chr(asciiLetterValue))] = createPlayoffMatchup(teamData, higherSeed, lowerSeed)
        asciiLetterValue += 1

    return matchups


def printPlayoffSeries(output, predictionRound):
    print(f"\nPredictions for NHL Playoff Round {predictionRound}\n")
    for letter in output:
        winner = max(output[letter], key=output[letter].get)
        loser = min(output[letter], key=output[letter].get)
        print(f"Predicting {winner} defeats {loser} {output[letter][winner]} - "
            f"{output[letter][loser]} in series {predictionRound}.{letter}")
