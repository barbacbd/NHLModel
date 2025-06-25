from json import dumps
from logging import getLogger
from requests import get
from statistics import mean


def getStandings():
    '''Get all team standings data.
    '''
    endpoint = "https://api-web.nhle.com/v1/standings/now"
    jsonRequest = None
    
    try:
        jsonRequest = get(endpoint).json()
    except:
        logger.error("No team data found")
        return None

    standings = {"E": {}, "W": {}}

    if jsonRequest is not None:
        for team in jsonRequest["standings"]:
            # 8 playoff teams in each conferences
            if int(team["conferenceSequence"]) <= 8:
                standings[team["conferenceAbbrev"]][
                    team["teamAbbrev"]["default"]] = {"conf": team["conferenceSequence"], "league": team["leagueSequence"]}

            average = mean([len(standings[x]) for x in standings])
            if average == 8:
                break

    return standings
