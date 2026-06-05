from logging import getLogger
from statistics import mean
from requests import get
from requests.exceptions import RequestException
from nhl_model.cache import cached_request


logger = getLogger("nhl_neural_net")


@cached_request(ttl_seconds=3600)  # 1 hour for standings
def _get_standings_from_api(url: str):
    """Cached API call to get standings data.

    Args:
        url: API endpoint URL

    Returns:
        JSON response data
    """
    response = get(url)
    if hasattr(response, 'raise_for_status'):
        response.raise_for_status()
    return response.json()


def getStandings():
    '''Get all team standings data.
    '''
    endpoint = "https://api-web.nhle.com/v1/standings/now"
    jsonRequest = None

    try:
        jsonRequest = _get_standings_from_api(endpoint)
    except (RequestException, ValueError) as e:
        logger.error(f"No standings data found: {e}")
        return None

    standings = {"E": {}, "W": {}}

    if jsonRequest is not None:
        for team in jsonRequest["standings"]:
            # 8 playoff teams in each conferences
            if int(team["conferenceSequence"]) <= 8:
                standings[team["conferenceAbbrev"]][
                    team["teamAbbrev"]["default"]] = \
                        {"conf": team["conferenceSequence"], "league": team["leagueSequence"]}

            average = mean([len(standings[x]) for x in standings])  #pylint: disable=C0206
            if average == 8:
                break

    return standings
