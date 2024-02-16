# pylint: disable=missing-module-docstring
# pylint: disable=invalid-name

from nhl_core import NHLData
from nhl_model.enums import EventType


# List of all shot event types
ShotEvents = [x.value for x in EventType]


class Game:
    '''A Game contains all home and away team events that have occurred during
    an NHL game.
    '''

    # pylint: disable=too-many-instance-attributes

    def __init__(self, gameId, homeTeamId=None, awayTeamId=None):
        self.gameId = gameId
        self.homeTeamId = homeTeamId
        self.awayTeamId = awayTeamId
        self.homeTeamEvents = []
        self.awayTeamEvents = []

        # Values for prediction and analysis
        self.homeTeamWinPercent = 0.0
        self.awayTeamWinPercent = 0.0
        self.regulationTiePercent = 0.0
        self.homeTeamGoalsPrediction = 0
        self.homeTeamGoalsActual = 0
        self.awayTeamGoalsPrediction = 0
        self.awayTeamGoalsActual = 0

    def addHomeTeamEvent(self, event):
        '''Add an event that occurred due to actions performed by the home team.'''
        if event.result.event == EventType.GOAL.value:
            self.homeTeamGoalsActual += 1
        self.homeTeamEvents.append(event)

    def addAwayTeamEvent(self, event):
        '''Add an event that occurred due to actions performed by the away team.'''
        if event.result.event == EventType.GOAL.value:
            self.awayTeamGoalsActual += 1
        self.awayTeamEvents.append(event)

    @property
    def winnerPredicted(self):
        '''Returns true when the predicted winner is the actual winner.'''
        if (self.homeTeamWinPercent > self.awayTeamWinPercent and \
            self.homeTeamGoalsActual > self.awayTeamGoalsActual) or \
            (self.awayTeamWinPercent > self.homeTeamWinPercent and \
             self.awayTeamGoalsActual > self.homeTeamGoalsActual):
            return True
        return False

    @property
    def winner(self):
        '''Return home or away based on the team that scored the most goals.'''
        return "home" if self.homeTeamGoalsActual > self.awayTeamGoalsActual else "away"

    @property
    def totalGoals(self):
        '''Get the sum of goals that both teams scored.'''
        return self.homeTeamGoalsActual + self.awayTeamGoalsActual

    @property
    def valid(self):
        '''Returns true when the home and away teams are set.'''
        # technically it is possible to have no events saved, but the team Ids must be present
        return None not in (self.homeTeamId, self.awayTeamId)

    def goals(self):
        """Returns a dict of number of goals for each team id for easy calculation
        """
        return {
            self.homeTeamId: self.homeTeamGoalsActual,
            self.awayTeamId: self.awayTeamGoalsActual
        }

    @property
    def json(self):
        '''Return a dictionary that contains a valid json representation of the instance.'''
        return {
            "gameId": self.gameId,
            "homeTeamId": self.homeTeamId,
            "awayTeamId": self.awayTeamId,
            # Missing the actual events. This is too much to load/unload to files
            "homeTeamWinPercent": self.homeTeamWinPercent,
            "awayTeamWinPercent": self.awayTeamWinPercent,
            "regulationTiePercent": self.regulationTiePercent,
            "homeTeamGoalsPrediction": self.homeTeamGoalsPrediction,
            "homeTeamGoalsActual": self.homeTeamGoalsActual,
            "awayTeamGoalsPrediction": self.awayTeamGoalsPrediction,
            "awayTeamGoalsActual": self.awayTeamGoalsActual,
        }

    def fromJson(self, jsonData):
        '''Set this instance from a valid json formatted dictionary.'''
        for key, value in jsonData.items():
            if key in ("homeTeamEvents", "awayTeamEvents"):
                setattr(self, key, [NHLData(x) for x in value])
            else:
                setattr(self, key, value)
