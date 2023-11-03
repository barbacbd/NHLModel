from datetime import datetime
import inquirer
from json import loads
from os.path import dirname, abspath
from nhl_core.endpoints import NHL_FIRST_SEASON
from scipy.stats import poisson
import matplotlib.pyplot as plt
from pandas import DataFrame
from statistics import mean


def readStatisticsFile():
    """Read in the json file data to grab the names of the teams. The 
    file is called `NhlYearlyStatistics.json` and lives in the support
    directory of the current project.
    """
    _currDir = dirname(abspath(__file__))
    splitDir = _currDir.split("/")
    splitDir = splitDir[:-2] + ["support", "NhlYearlyStatistics.json"]

    with open("/".join(splitDir), "rb") as jsonFile:
        jsonData = loads(jsonFile.read())

    return jsonData


def parseArguments():
    """Parse the arguements for the program by reading in the static file that
    contains the basic statistics for all teams and all seasons.
    """
    # get the year then implement argparse 
    currentYear = datetime.now().year
    questions = [
        inquirer.Text('year', message="Enter the year for the season start.", default=currentYear-1),
    ]
    answers = inquirer.prompt(questions)
    
    year = int(answers["year"])
    if NHL_FIRST_SEASON > year > currentYear:
        # TODO: Add debugging logger here
        year = currentYear - 1

    teamNames = []
    season = f"{year}{year+1}"

    jsonData = readStatisticsFile()
    if season in jsonData:
        for k, v in jsonData[season].items():
            teamNames.append(v["name"])

    if not teamNames:
        return None
    teamNames.sort()

    questions = [
        inquirer.List("homeTeam", message="Name of the home team for analysis.", choices=teamNames),
        inquirer.List("awayTeam", message="Name of the away team for analysis.", choices=teamNames)
    ]
    answers = inquirer.prompt(questions)

    return {
        "season": season,
        "homeTeam": answers["homeTeam"],
        "awayTeam": answers["awayTeam"]
    }


def getJsonRecord(season, teamName=None):
    """Get the statistical records from the json data for a particular 
    season and team.

    :param season: {year}{year+1} string representation of the nhl season
    :param teamName: Name of the to find the record for.
    """
    teamData = []

    jsonData = readStatisticsFile()
    if season in jsonData:
        for k, v in jsonData[season].items():
            if teamName is None:
                teamData.append(v)
            elif teamName == v["name"]:
                return v
    return teamData


def getTotalGoals(season):
    # The number of goals scored home or away will always be the same
    # since there is always a home and away team. 
    records = getJsonRecord(season)
    goalsScored = []
    for teamData in records:
        goalsScored.extend(teamData["goalsScoredHomeGames"])
    return goalsScored


def calculate(season, homeTeam, awayTeam):

    goalsScored = getTotalGoals(season)
    goalScoredMean, maxGoalsScored = round(mean(goalsScored), 2), max(goalsScored)
    homeTeamRecord = getJsonRecord(season, homeTeam)
    awayTeamRecord = getJsonRecord(season, awayTeam)

    # calculate the home team offensive score
    homeTeamAvgGoalsScoredPerGameHome = homeTeamRecord["avgGoalsScoredPerGameHome"]
    homeAttackStrength = homeTeamAvgGoalsScoredPerGameHome / goalScoredMean

    # calculate the away team defensive score
    awayTeamAvgGoalsAgainstPerGameAway = awayTeamRecord["avgGoalsAgainstPerGameAway"]
    awayDefenseStrength = awayTeamAvgGoalsAgainstPerGameAway / goalScoredMean

    # estiamted number of goals for home team to score
    homeTeamGoalPrediction = homeAttackStrength * awayDefenseStrength * goalScoredMean

    # calculate the away team offensive score
    awayTeamAvgGoalsScoredPerGameAway = awayTeamRecord["avgGoalsScoredPerGameAway"]
    awayAttackStrength = awayTeamAvgGoalsScoredPerGameAway / goalScoredMean

    # calculate the home team defensive score
    homeTeamAvgGoalsAgainstPerGameHome = homeTeamRecord["avgGoalsAgainstPerGameHome"]
    homeDefenseStrength = homeTeamAvgGoalsAgainstPerGameHome / goalScoredMean

    # estiamted number of goals for away team to score
    awayTeamGoalPrediction = awayAttackStrength * homeDefenseStrength * goalScoredMean

    # add one to the max goals to include it in the scores 
    # otherwise the forloop will not use it
    maxGoalsScored += 1

    pdfData = {homeTeam: [], awayTeam: []}
    for i in range(maxGoalsScored):
        pdfData[homeTeam].append(poisson.pmf(i, mu=homeTeamGoalPrediction))
        pdfData[awayTeam].append(poisson.pmf(i, mu=awayTeamGoalPrediction))

    # calculate the chances of a winning atleast 1 point (tie in regulation)
    regulationDrawCalc = 0.0
    for i in range(maxGoalsScored):
        regulationDrawCalc += pdfData[homeTeam][i] * pdfData[awayTeam][i]

    # calculate the chances of home team winning 3 points
    homeTeamWinCalc = 0.0
    for i in range(maxGoalsScored):
        for j in range(i, maxGoalsScored):
            if i != j:
                homeTeamWinCalc += pdfData[homeTeam][j] * pdfData[awayTeam][i]

    # calculate the chances of away team winning 3 points
    awayTeamWinCalc = 0.0
    for i in range(maxGoalsScored):
        for j in range(i, maxGoalsScored):
            if i != j:
                awayTeamWinCalc += pdfData[awayTeam][j] * pdfData[homeTeam][i]

    return {
        "tie": regulationDrawCalc,
        "homeWin": homeTeamWinCalc,
        "awayWin": awayTeamWinCalc,
        "homeGoals": homeTeamGoalPrediction,
        "awayGoals": awayTeamGoalPrediction,
        "pdf": pdfData
    }


def main():
    """Main execution point
    """
    args = parseArguments()
    if not args:
        exit(1)

    calculations = calculate(args["season"], args["homeTeam"], args["awayTeam"])

    homeWinPercent = calculations["homeWin"]
    awayWinPercent = calculations["awayWin"]
    regulationTiePercent = calculations["tie"]
    homeGoals = calculations["homeGoals"]
    awayGoals = calculations["awayGoals"]
    pdfData = calculations["pdf"]

    df = DataFrame.from_dict(pdfData, orient='index')
    print(df)

    print(f"{args['homeTeam']} (HOME) win percentage: {round(homeWinPercent*100.0, 2)}")
    print(f"{args['awayTeam']} (AWAY) win percentage: {round(awayWinPercent*100.0, 2)}")
    print(f"Regulation tie percent: {round(regulationTiePercent*100.0,2)}")
    print(f"Expected Score (HOME) {int(round(homeGoals, 0))} - {int(round(awayGoals, 0))} (AWAY)")



if __name__ == '__main__':
    main()
