from collections import defaultdict
from datetime import datetime
import inquirer
from json import loads
from os.path import dirname, abspath, join as path_join, exists
from scipy.stats import poisson
from statistics import mean
from nhl_score_prediction.event import Game


def readStatisticsFile(dirList):
    """Read in the json file data to grab the names of the teams. The 
    file is called `NhlYearlyStatistics.json` and lives in the support
    directory of the current project.
    """
    _currDir = dirname(abspath(__file__))
    splitDir = _currDir.split("/")
    splitDir = splitDir[:-2] + dirList

    filename = "/" + path_join(*splitDir)
    if not exists(filename):
        return None

    with open(filename, "rb") as jsonFile:
        jsonData = loads(jsonFile.read())

    return jsonData


def getSchedule(year):
    """Read the schedule file (json) from a specific file location. The files are located
    in a subdirectory named for the year or beginning year for the season.
    """
    jsonData = readStatisticsFile(["support", "schedules", str(year), "schedule.json"])
    return jsonData


def parseSchedule(schedule):
    """Parse the schedule into a set of home and away games. Technically the
    home and away games are the same object, but there is a copy for the home 
    team and the away team. 
    """
    homeTeamEvents = defaultdict(list)
    awayTeamEvents = defaultdict(list)
    for game in schedule:
        g = Game("randomData")
        g.fromJson(game)

        homeTeamEvents[g.homeTeamId].append(g)
        awayTeamEvents[g.awayTeamId].append(g)

    return homeTeamEvents, awayTeamEvents


def calculateAvgGoals(events):
    """Calculate the number of goals home and away. The 
    returned values are the averages. 
    """
    goalsScoredHome = []
    goalsScoredAway = []
    for _, v in events.items():
        goalsScoredHome.extend([x.homeTeamGoalsActual for x in v])
        goalsScoredAway.extend([x.awayTeamGoalsActual for x in v])

    avgGoalsScoredHomeTotal = mean(goalsScoredHome)
    avgGoalsScoredAwayTotal = mean(goalsScoredAway)

    return avgGoalsScoredHomeTotal, avgGoalsScoredAwayTotal


def calculateScores(teamIds, homeTeamEvents, awayTeamEvents):
    """The following calculations are performed for each team in the
    list of team IDs:
    - Home offensive score
    - Home defensive score
    - Away offensive score
    - Away offensive score

    :return: Dictionary where the keys are each of the team Ids in the 
    list passed in. Each value is a dictionary with the following keys:
        - homeAttackStrength
        - homeDefenseStrength
        - awayAttackStrength
        - awayDefenseStrength
    When any of the values is None, the value could not be calculated.
    """
    avgGoalsScoredHomeTotal, avgGoalsScoredAwayTotal = calculateAvgGoals(homeTeamEvents)

    scores = {}

    for teamId in teamIds:
        teamScores = {
            "homeAttackStrength": None,
            "homeDefenseStrength": None,
            "awayAttackStrength": None,
            "awayDefenseStrength": None
        }

        # Home Attack Strength
        avgHomeGoals = None if teamId not in homeTeamEvents else \
            mean([x.homeTeamGoalsActual for x in homeTeamEvents[teamId]])
        if avgHomeGoals is not None:
            homeAttackStrength = avgHomeGoals / avgGoalsScoredHomeTotal
            teamScores["homeAttackStrength"] = homeAttackStrength

        # Home Defense Strength 
        avgHomeGoalsAgainst = None if teamId not in homeTeamEvents else \
            mean([x.awayTeamGoalsActual for x in homeTeamEvents[teamId]])
        if avgHomeGoalsAgainst is not None:
            homeDefenseStrength = avgHomeGoalsAgainst / avgGoalsScoredAwayTotal
            teamScores["homeDefenseStrength"] = homeDefenseStrength

        # Away Attack Strength
        avgAwayGoals = None if teamId not in awayTeamEvents else \
            mean([x.awayTeamGoalsActual for x in awayTeamEvents[teamId]])
        if avgAwayGoals is not None:
            awayAttackStrength = avgAwayGoals / avgGoalsScoredAwayTotal
            teamScores["awayAttackStrength"] = awayAttackStrength
        
        # Away Defense Strength
        avgAwayGoalsAgainst = None if teamId not in awayTeamEvents else \
            mean([x.homeTeamGoalsActual for x in awayTeamEvents[teamId]])
        if avgAwayGoalsAgainst is not None:
            awayDefenseStrength = avgAwayGoalsAgainst / avgGoalsScoredHomeTotal
            teamScores["awayDefenseStrength"] = awayDefenseStrength

        # add the team specific data to the dictionary of values
        scores[teamId] = teamScores

    return scores


def parseArguments():
    """Parse the arguements for the program by reading in the static file that
    contains the basic statistics for all teams and all seasons.
    """
    # Ask for the year/season for analysis
    currentYear = datetime.now().year
    questions = [
        inquirer.Text('year', message="Enter the year for the season start.", default=currentYear-1),
    ]
    answers = inquirer.prompt(questions)
    year = int(answers["year"])

    # Get the entire schedule 
    schedule = getSchedule(year)
    if schedule is None:
        print(f"Failed to find a schedule for year {year}")
        exit(1)

    # Get the schedule for the previous year
    # This will be used for the first home and away game for each
    # team during the selected year.
    previousSchedule = getSchedule(year-1)
    if previousSchedule is None:
        print(f"Failed to find a schedule for previous year {year-1}")
        exit(1)

    if None in (schedule, previousSchedule):
        print("Failed to find a valid schedule for")
        exit(1)

    return schedule, previousSchedule


def findMaxGoalsScored(events):
    # Get the maximum number of goals scored based on the games provided
    goalsScored = []
    for _, value in events.items():
        for game in value:
            goalsScored.extend([game.homeTeamGoalsActual, game.awayTeamGoalsActual])
    return max(goalsScored)


def createPredictions(maxGoals, homeTeamGoalsPredicted, awayTeamGoalsPredicted):
    """Create the win percentages for both teams based on the supplied data.
    
    :param maxGoals: Maximum number of goals scored by any team in a game.
    :param homeTeamGoalsPredicted: The value is calculated from the offense and 
    defense scores according to the mean number of home goals in home games.
    :param awayTeamGoalsPredicted: The value is calculated from the offense and 
    defense scores according to the mean number of away goals in away games.

    :return homeWinPercent, awayWinPercent, regulationTiePercent, Dataframe for all values
    """

    # increase the max number of goals by 1 to include all goals in the calculations
    _maxGoals = maxGoals + 1

    pdfData = {"home": [], "away": []}
    for i in range(_maxGoals):
        pdfData["home"].append(poisson.pmf(i, mu=homeTeamGoalsPredicted))
        pdfData["away"].append(poisson.pmf(i, mu=awayTeamGoalsPredicted))

    # calculate the chances of a winning atleast 1 point (tie in regulation)
    regulationDrawCalc = 0.0
    for i in range(_maxGoals):
        regulationDrawCalc += pdfData["home"][i] * pdfData["away"][i]

    # calculate the chances of home team winning 3 points
    homeTeamWinCalc = 0.0
    for i in range(_maxGoals):
        for j in range(i, _maxGoals):
            if i != j:
                homeTeamWinCalc += pdfData["home"][j] * pdfData["away"][i]

    # calculate the chances of away team winning 3 points
    awayTeamWinCalc = 0.0
    for i in range(_maxGoals):
        for j in range(i, _maxGoals):
            if i != j:
                awayTeamWinCalc += pdfData["away"][j] * pdfData["home"][i]

    return homeTeamWinCalc, awayTeamWinCalc, regulationDrawCalc, pdfData


def main():
    """Main execution point

    Currently this would predict the score for the current season, theoretically if the the 
    season continued. 

    GOAL: Read the previous season and current season data. Use this information to 
    predict the scores for the current season or season that the user enters.

    """
    schedule, previousSchedule = parseArguments()
    homeTeamEventsPrev, awayTeamEventsPrev = parseSchedule(previousSchedule)
    totalTeamIdsPrevSeason = set(list(homeTeamEventsPrev.keys()))
    totalTeamIdsPrevSeason.update(list(awayTeamEventsPrev.keys()))
    previousSeasonScores  = calculateScores(
        list(totalTeamIdsPrevSeason), 
        homeTeamEventsPrev, 
        awayTeamEventsPrev
    )

    # Predict the values for the current schedule
    parsedHomeTeamEvents = defaultdict(list)
    parsedAwayTeamEvents = defaultdict(list)

    winsPredictedCorrect = 0

    for game in schedule:

        g = Game("randomGame")
        g.fromJson(game)

        homeTeamScores = {}
        awayTeamScores = {}

        findTeamScoresCurrSeason = []

        # use the previous season data to predict the home values
        if g.homeTeamId not in parsedHomeTeamEvents:
            if g.homeTeamId in previousSeasonScores:
                homeTeamScores.update(previousSeasonScores[g.homeTeamId])
            else:
                # indicates that the team may be new, or they don't have records
                # from the previous year. Use the entire average for all teams
                # from the previous year. 
                # TODO: will this just average to 1?
                homeTeamScores.update({"homeAttackStrength": 1.0, "homeDefenseStrength": 1.0})
        else:
            findTeamScoresCurrSeason.append(g.homeTeamId)

        # use the previous season data to predict away values
        if g.awayTeamId not in parsedAwayTeamEvents:
            if g.awayTeamId in previousSeasonScores:
                awayTeamScores.update(previousSeasonScores[g.awayTeamId])
            else:
                # indicates that the team may be new, or they don't have records
                # from the previous year. Use the entire average for all teams
                # from the previous year. 
                # TODO: will this just average to 1?
                awayTeamScores.update({"awayAttackStrength": 1.0, "awayDefenseStrength": 1.0})
        else:
            findTeamScoresCurrSeason.append(g.awayTeamId)

        # Time to parse using the current seasonal data    
        if findTeamScoresCurrSeason:
            currentScores = calculateScores(
                findTeamScoresCurrSeason, 
                parsedHomeTeamEvents, 
                parsedAwayTeamEvents
            )
        
            if g.homeTeamId in currentScores:
                homeTeamScores.update(currentScores[g.homeTeamId])
            if g.awayTeamId in currentScores:
                awayTeamScores.update(currentScores[g.awayTeamId])
    
            avgHomeGoalsScored, avgAwayGoalsScored = calculateAvgGoals(parsedHomeTeamEvents)
            maxGoals = findMaxGoalsScored(parsedHomeTeamEvents)
        else:
            avgHomeGoalsScored, avgAwayGoalsScored = calculateAvgGoals(homeTeamEventsPrev)
            maxGoals = findMaxGoalsScored(homeTeamEventsPrev)

        # Predict the number of goals for the home and away teams.
        # The Poisson Distribution only requires the mean value in this case these predicted values.
        # There is a tendency to regress to the mean - The Law of Averages. Even when there are
        # outlier games we should observe more stability in prediction as the season continues.
        homeTeamGoalsPredicted = homeTeamScores["homeAttackStrength"] * awayTeamScores["awayDefenseStrength"] * avgHomeGoalsScored
        awayTeamGoalsPredicted = awayTeamScores["awayAttackStrength"] * homeTeamScores["homeDefenseStrength"] * avgAwayGoalsScored

        
        homeTeamWinCalc, awayTeamWinCalc, regulationDrawCalc, pdfData = createPredictions(
            maxGoals, homeTeamGoalsPredicted, awayTeamGoalsPredicted
        )

        g.fromJson(
            {
                "homeTeamWinPercent": round(homeTeamWinCalc * 100.0, 2),
                "homeTeamGoalsPrediction": homeTeamGoalsPredicted,
                "awayTeamWinPercent": round(awayTeamWinCalc * 100.0, 2),
                "awayTeamGoalsPrediction": awayTeamGoalsPredicted,
                "regulationTiePercent": round(regulationDrawCalc * 100.0, 2),
                "poissonPDF": pdfData
            }
        )

        if g.winnerPredicted:
            winsPredictedCorrect += 1


        # update the home and away events that have been parsed - each game
        # is both a home and an away event
        parsedHomeTeamEvents[g.homeTeamId].append(g)
        parsedAwayTeamEvents[g.awayTeamId].append(g)

    print(f"Number of Games: {len(schedule)}")
    print(f"Number of correctly predicted games: {winsPredictedCorrect}")
    print(f"Percent of correctly predicted games: {round(float(winsPredictedCorrect)/float(len(schedule)) *100.0, 2)}")
    

if __name__ == '__main__':
    main()
