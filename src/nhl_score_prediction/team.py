from enum import Enum
from nhl_score_prediction.event import EventType
from statistics import mean


SECONDS_PER_PERIOD = 1200  # 20 * 60


class TeamSide(Enum):
    # simple identifier to indicate home vs away status of
    # a team during a game. 
    AWAY = 0
    HOME = 1


class Team:

    __slots__ = [
        "name",
        "abbreviation",
        "teamName",
        "locationName",
	    "firstYearOfPlay",
	    "franchiseId"
    ]

    def __init__(self, jsonData):
        self._setFromJson(jsonData)

    def _setFromJson(self, jsonData):
        if not isinstance(jsonData, dict):
            return

        for k, v in jsonData.items():

            if k in Team.__slots__ and \
                getattr(self, k, None) is None:
                setattr(self, k, v)

            if isinstance(v, dict):
                self._setFromJson(v)


    @property
    def json(self):
        return  {
            attr: getattr(self, attr)
            for attr in Team.__slots__
        }


def parseTimeMMSS(timeStr):
    minutes, seconds = map(int, timeStr.split(":"))
    return (minutes*60) + seconds


class TeamStats:

    """The team stats class contains the statistics for a team. The stats are
    valid for a single season.
    """
    
    def __init__(self, teamId=None, teamName=None):
        self.teamId = teamId
        self.name = teamName
            
        # The game records is a list of dictionaries where
        # The keys are the names of the teams, where one should
        # match the team of this instance
        self.gameRecords = []
    
        self._awayEvents = {}
        self._homeEvents = {}

    def _generateInternalId(self):
        return len(self._awayEvents) + len(self._homeEvents) + 1

    def addAwayEvent(self, event):
        internalEventId = self._generateInternalId()
        self._awayEvents[internalEventId] = event

    def addHomeEvent(self, event):
        internalEventId = self._generateInternalId()
        self._homeEvents[internalEventId] = event

    def _correctNumEventsIncluded(self, maxIncludedRecords, home=True, away=False):
        if maxIncludedRecords <= 0:
            return 0

        total = 0
        if home:
            total += len(self._homeEvents)
        if away:
            total += len(self._awayEvents)

        if maxIncludedRecords > total:
            return total
        
        return maxIncludedRecords


    def _isolateGames(self, home, away, reverse=True):
        games = {}
        if home:
            games.update(self._homeEvents)
        if away:
            games.update(self._awayEvents)
        
        if reverse:
            # sort based on the entry number (essentially the game played), then reverse
            # the list to get the most recent games first
            return dict(reversed(games.items()))
        else:
            return dict(sorted(games.items()))
    

    def _isolateEvents(self, game_num, game, against):
        # determine the list of events that should be searched for the game
        # Home events are used when the game number exists in the home games and 
        # we are not looking for goals against, or the game number is in away games
        # and we are looking for goals against.
        # The opposite is true for away events.
        if (game_num in self._awayEvents and not against) or \
            (game_num in self._homeEvents and against):
            return game.awayTeamEvents
        return game.homeTeamEvents


    def _averageTimeToGoal(self, maxIncludedRecords, home=True, away=False, against=False):
        games = self._isolateGames(home, away)

        numEvents = len(games) if maxIncludedRecords is None else \
            self._correctNumEventsIncluded(maxIncludedRecords, home, away)

        times = []

        # during a game in which no goals were scored - add the 60 minute
        for game_num, game in games.items():
            foundGoal = False
            gameEvents = self._isolateEvents(game_num, game, against)

            for event in gameEvents:
                if event.result.event == EventType.GOAL.value:
                    period = event.about.period - 1
                    times.append((period * SECONDS_PER_PERIOD) + parseTimeMMSS(event.about.periodTime))
                    foundGoal = True
                    break
                            
            # during a game in which the team did not score, 
            # add the regulation time of the game
            if not foundGoal:
                times.append(3 * SECONDS_PER_PERIOD)

            # found the max number of events
            if len(times) >= numEvents:
                break
    
        # make sure that the number of events matches the expected
        assert len(times) == numEvents

        return round(mean(times), 2)


    def avgTimeToFirstGoalScored(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team scored (includes home and away games). 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, True, True, False)


    def avgTimeToFirstGoalScoredHome(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team scored during home games. 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, True, False, False)


    def avgTimeToFirstGoalScoredAway(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team scored during away games. 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, False, True, False)


    def avgTimeToFirstGoalAgainst(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team lets in (includes home and away games). 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, True, True, True)


    def avgTimeToFirstGoalAgainstHome(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team lets in for home games. 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, True, False, True)
    

    def avgTimeToFirstGoalAgainstAway(self, maxIncludedRecords=None):
        # calculate the average time from the start of the game
        # until the first goal this team lets in for away games. 
        # The value in SECONDS is returned
        return self._averageTimeToGoal(maxIncludedRecords, False, True, True)


    def _goalsScored(self, maxIncludedRecords, home=True, away=False, against=False):
        games = self._isolateGames(home, away)

        numEvents = len(games) if maxIncludedRecords is None else \
            self._correctNumEventsIncluded(maxIncludedRecords, home, away)

        goals = []

        # during a game in which no goals were scored - add the 60 minute
        for game_num, game in games.items():
            goalsInGame = 0
            gameEvents = self._isolateEvents(game_num, game, against)

            for event in gameEvents:
                if event.result.event == EventType.GOAL.value:
                    goalsInGame += 1
            
            # stow the number of goals in this game
            goals.append(goalsInGame)

            # found the max number of events
            if len(goals) >= numEvents:
                break
    
        # make sure that the number of events matches the expected
        assert len(goals) == numEvents

        return goals


    def goalsScoredHomeGames(self, maxIncludedRecords=None):
        # Find the number of goals for each home game. This will find a list
        # of values (one for each home game). 
        return self._goalsScored(maxIncludedRecords, True, False, False)


    def goalsScoredAwayGames(self, maxIncludedRecords=None):
        # Find the number of goals for each away game. This will find a list
        # of values (one for each away game). 
        return self._goalsScored(maxIncludedRecords, False, True, False)


    def goalsScoredAgainstHomeGames(self, maxIncludedRecords=None):
        # Find the number of goals scored against for each home game. This will find a list
        # of values (one for each home game). 
        return self._goalsScored(maxIncludedRecords, True, False, True)


    def goalsScoredAgainstAwayGames(self, maxIncludedRecords=None):
        # Find the number of goals scored against for each away game. This will find a list
        # of values (one for each away game). 
        return self._goalsScored(maxIncludedRecords, False, True, True)


    def _numGoalsScored(self, maxIncludedRecords, home=True, away=False, against=False):
        goals = self._goalsScored(maxIncludedRecords, home, away, against)
        return round(mean(goals), 2)


    def avgGoalsScoredPerGame(self, maxIncludedRecords=None):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value (includes home and away games).
        return self._numGoalsScored(maxIncludedRecords, True, True, False)


    def avgGoalsScoredPerGameHome(self, maxIncludedRecords=None):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Home games.
        return self._numGoalsScored(maxIncludedRecords, True, False, False)


    def avgGoalsScoredPerGameAway(self, maxIncludedRecords=None):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Away games.
        return self._numGoalsScored(maxIncludedRecords, False, True, False)


    def avgGoalsAgainstPerGame(self, maxIncludedRecords=None):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value (includes home and away games).
        return self._numGoalsScored(maxIncludedRecords, True, True, True)


    def avgGoalsAgainstPerGameHome(self, maxIncludedRecords=None):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Home games.
        return self._numGoalsScored(maxIncludedRecords, True, False, True)


    def avgGoalsAgainstPerGameAway(self, maxIncludedRecords=None):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Away games.
        return self._numGoalsScored(maxIncludedRecords, False, True, True)


    def _maxGoals(self, maxIncludedRecords, home=True, away=False, against=False):
        games = self._isolateGames(home, away)

        numEvents = len(games) if maxIncludedRecords is None else \
            self._correctNumEventsIncluded(maxIncludedRecords, home, away)

        goals = []

        # during a game in which no goals were scored - add the 60 minute
        for game_num, game in games.items():
            goalsInGame = 0
            gameEvents = self._isolateEvents(game_num, game, against)

            for event in gameEvents:
                if event.result.event == EventType.GOAL.value:
                    goalsInGame += 1
            
            # stow the number of goals in this game
            goals.append(goalsInGame)

            # found the max number of events
            if len(goals) >= numEvents:
                break
    
        # make sure that the number of events matches the expected
        assert len(goals) == numEvents

        return max(goals)


    def maxGoalsScored(self, maxIncludedRecords=None):
        # find the max number of goals scored from all records
        return self._maxGoals(maxIncludedRecords, True, True, False)


    def maxGoalsScoredHome(self, maxIncludedRecords=None):
        # find the max number of goals scored from all Home records
        return self._maxGoals(maxIncludedRecords, True, False, False)


    def maxGoalsScoredAway(self, maxIncludedRecords=None):
        # find the max number of goals scored from all Away records
        return self._maxGoals(maxIncludedRecords, False, True, False)


    def maxGoalsAgainst(self, maxIncludedRecords=None):
        # find the max number of goals against from all records
        return self._maxGoals(maxIncludedRecords, True, True, True)


    def maxGoalsAgainstHome(self, maxIncludedRecords=None):
        # find the max number of goals against from all Home records
        return self._maxGoals(maxIncludedRecords, True, False, True)


    def maxGoalsAgainstAway(self, maxIncludedRecords=None):
        # find the max number of goals against from all Away records
        return self._maxGoals(maxIncludedRecords, False, True, True)
    

    def _averageTimeBetweenGoals(self, maxIncludedRecords, home=True, away=False, against=False):
        games = self._isolateGames(home, away)

        numEvents = len(games) if maxIncludedRecords is None else \
            self._correctNumEventsIncluded(maxIncludedRecords, home, away)

        times = []

        parsedEvents = 0
        # during a game in which no goals were scored - add the 60 minute
        for game_num, game in games.items():
            gameEvents = self._isolateEvents(game_num, game, against)
            _goalTimes = []

            for event in gameEvents:
                if event.result.event == EventType.GOAL.value:
                    period = event.about.period - 1
                    _goalTimes.append((period * SECONDS_PER_PERIOD) + parseTimeMMSS(event.about.periodTime))
                            
            # during a game in which the team did not score, 
            # add the regulation time of the game
            if len(_goalTimes) == 0:
                times.append(3 * SECONDS_PER_PERIOD)
            else:
                _goalTimes.insert(0, 0)
                for i in range(1, len(_goalTimes)):
                    times.append(_goalTimes[i] - _goalTimes[i-1])

            parsedEvents += 1
            # found the max number of events
            if parsedEvents >= numEvents:
                break

        return round(mean(times), 2)


    def avgTimeBetweenGoalsScoredSecs(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the team. 
        # This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, True, True, False)


    def avgTimeBetweenGoalsScoredSecsHome(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the team
        # during home games. This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, True, False, False)
    
    
    def avgTimeBetweenGoalsScoredSecsAway(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the team
        # during away games. This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, False, True, False)
    
    
    def avgTimeBetweenGoalsAgainstSecs(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the opponent.
        # This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, True, True, True)
    

    def avgTimeBetweenGoalsAgainstSecsHome(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the opponent
        # during home games. This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, True, False, True)
    

    def avgTimeBetweenGoalsAgainstSecsAway(self, maxIncludedRecords=None):
        # Find the average number of seconds between goals scored by the opponent
        # during away games. This function does not include time before the first goal.
        return self._averageTimeBetweenGoals(maxIncludedRecords, False, True, True)


    def _shotsBetweenGoals(self, maxIncludedRecords, home=True, away=False, against=False):
        games = self._isolateGames(home, away)

        numEvents = len(games) if maxIncludedRecords is None else \
            self._correctNumEventsIncluded(maxIncludedRecords, home, away)

        shots = []
        parsedEvents = 0

        # during a game in which no goals were scored - add the 60 minute
        for game_num, game in games.items():
            shotsTaken = 0
            shotsCaptured = []
            gameEvents = self._isolateEvents(game_num, game, against)

            for event in gameEvents:
                if event.result.event == EventType.SHOT.value:
                    shotsTaken += 1
                elif event.result.event == EventType.GOAL.value:
                    shotsCaptured.append(shotsTaken)
                    shotsTaken = 0
            
            # only save the total shots if none were scored during the game
            if len(shotsCaptured) == 0:
                shots.append(shotsTaken)
            else:
                shots.extend(shotsCaptured)
            
            parsedEvents += 1
            # found the max number of events
            if parsedEvents >= numEvents:
                break

        return round(mean(shots), 2)


    def avgShotsTakenBeforeGoalScored(self, maxIncludedRecords=None):
        # Find the average number of shots taken between goals. This includes
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, True, True, False)


    def avgShotsTakenBeforeGoalScoredHome(self, maxIncludedRecords=None):
        # Find the average number of shots taken between goals for home games. This includes
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, True, False, False)
    

    def avgShotsTakenBeforeGoalScoredAway(self, maxIncludedRecords=None):
        # Find the average number of shots taken between goals for away games. This includes
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, False, True, False)


    def avgShotsReceivedBeforeGoalScored(self, maxIncludedRecords=None):
        # Find the average number of shots against us between goals. This includes 
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, True, True, True)


    def avgShotsReceivedBeforeGoalScoredHome(self, maxIncludedRecords=None):
        # Find the average number of shots against us between goals for home games. This includes 
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, True, False, True)
    

    def avgShotsReceivedBeforeGoalScoredAway(self, maxIncludedRecords=None):
        # Find the average number of shots against us between goals for away games. This includes 
        # the first goal of the game.
        return self._shotsBetweenGoals(maxIncludedRecords, False, True, True)


    def json(self, maxIncludedRecords=None):
        return {
            "id": self.teamId,
            "name": self.name,
            "awayGames": len(self._awayEvents),
            "homeGames": len(self._homeEvents),
            "avgTimeToFirstGoalScored": self.avgTimeToFirstGoalScored(maxIncludedRecords),
            "avgTimeToFirstGoalScoredHome": self.avgTimeToFirstGoalScoredHome(maxIncludedRecords),
            "avgTimeToFirstGoalScoredAway": self.avgTimeToFirstGoalScoredAway(maxIncludedRecords),
            "avgTimeToFirstGoalAgainst": self.avgTimeToFirstGoalAgainst(maxIncludedRecords),
            "avgTimeToFirstGoalAgainstHome": self.avgTimeToFirstGoalAgainstHome(maxIncludedRecords),
            "avgTimeToFirstGoalAgainstAway": self.avgTimeToFirstGoalAgainstAway(maxIncludedRecords),
            "avgGoalsScoredPerGame": self.avgGoalsScoredPerGame(maxIncludedRecords),
            "avgGoalsScoredPerGameHome": self.avgGoalsScoredPerGameHome(maxIncludedRecords),
            "avgGoalsScoredPerGameAway": self.avgGoalsScoredPerGameAway(maxIncludedRecords),
            "avgGoalsAgainstPerGame": self.avgGoalsAgainstPerGame(maxIncludedRecords),
            "avgGoalsAgainstPerGameHome": self.avgGoalsAgainstPerGameHome(maxIncludedRecords),
            "avgGoalsAgainstPerGameAway": self.avgGoalsAgainstPerGameAway(maxIncludedRecords),
            "maxGoalsScored": self.maxGoalsScored(maxIncludedRecords),
            "maxGoalsScoredHome": self.maxGoalsScoredHome(maxIncludedRecords),
            "maxGoalsScoredAway": self.maxGoalsScoredAway(maxIncludedRecords),
            "maxGoalsAgainst": self.maxGoalsAgainst(maxIncludedRecords),
            "maxGoalsAgainstHome": self.maxGoalsAgainstHome(maxIncludedRecords),
            "maxGoalsAgainstAway": self.maxGoalsAgainstAway(maxIncludedRecords),
            "avgTimeBetweenGoalsScoredSecs": self.avgTimeBetweenGoalsScoredSecs(maxIncludedRecords),
            "avgTimeBetweenGoalsScoredSecsHome": self.avgTimeBetweenGoalsScoredSecsHome(maxIncludedRecords),
            "avgTimeBetweenGoalsScoredSecsAway": self.avgTimeBetweenGoalsScoredSecsAway(maxIncludedRecords),
            "avgTimeBetweenGoalsAgainstSecs": self.avgTimeBetweenGoalsAgainstSecs(maxIncludedRecords),
            "avgTimeBetweenGoalsAgainstSecsHome": self.avgTimeBetweenGoalsAgainstSecsHome(maxIncludedRecords),
            "avgTimeBetweenGoalsAgainstSecsAway": self.avgTimeBetweenGoalsAgainstSecsAway(maxIncludedRecords),
            "avgShotsTakenBeforeGoalScored": self.avgShotsTakenBeforeGoalScored(maxIncludedRecords),
            "avgShotsTakenBeforeGoalScoredHome": self.avgShotsTakenBeforeGoalScoredHome(maxIncludedRecords),
            "avgShotsTakenBeforeGoalScoredAway": self.avgShotsTakenBeforeGoalScoredAway(maxIncludedRecords),
            "avgShotsReceivedBeforeGoalScored": self.avgShotsReceivedBeforeGoalScored(maxIncludedRecords),
            "avgShotsReceivedBeforeGoalScoredHome": self.avgShotsReceivedBeforeGoalScoredHome(maxIncludedRecords),
            "avgShotsReceivedBeforeGoalScoredAway": self.avgShotsReceivedBeforeGoalScoredAway(maxIncludedRecords),
            "goalsScoredHomeGames": self.goalsScoredHomeGames(maxIncludedRecords),
            "goalsScoredAwayGames": self.goalsScoredAwayGames(maxIncludedRecords),
            "goalsScoredAgainstHomeGames": self.goalsScoredAgainstHomeGames(maxIncludedRecords),
            "goalsScoredAgainstAwayGames": self.goalsScoredAgainstAwayGames(maxIncludedRecords),
        }