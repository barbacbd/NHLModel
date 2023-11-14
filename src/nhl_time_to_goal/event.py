from enum import Enum
from nhl_core import NHLData


class EventType(Enum):
    """
    Current list of event Types.

    Note: Only supported events include shot types
    """
    SHOT = 'Shot'
    GOAL = 'Goal'
    BLOCKED_SHOT = 'Blocked Shot'
    MISSED_SHOT = 'Missed Shot'


def eventTypeToStr(eventType):
    # convert the EventType to a string
    for x in EventType:
        if x.value == eventType:
            return x.value

    return None


# List of all shot event types
ShotEvents = [x.value for x in EventType]


class Game:
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
        if event.result.event == EventType.GOAL.value:
            self.homeTeamGoalsActual += 1
        self.homeTeamEvents.append(event)
    
    def addAwayTeamEvent(self, event):
        if event.result.event == EventType.GOAL.value:
            self.awayTeamGoalsActual += 1
        self.awayTeamEvents.append(event)

    @property
    def winnerPredicted(self):
        if (self.homeTeamWinPercent > self.awayTeamWinPercent and \
            self.homeTeamGoalsActual > self.awayTeamGoalsActual) or \
            (self.awayTeamWinPercent > self.homeTeamWinPercent and \
             self.awayTeamGoalsActual > self.homeTeamGoalsActual):
            return True
        return False

    @property
    def totalGoals(self):
        return self.homeTeamGoalsActual + self.awayTeamGoalsActual

    @property
    def valid(self):
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
        return {
            "gameId": self.gameId,
            "homeTeamId": self.homeTeamId,
            "awayTeamId": self.awayTeamId,
            # "homeTeamEvents": [x.json for x in self.homeTeamEvents],
            # "awayTeamEvents": [x.json for x in self.awayTeamEvents],
            "homeTeamWinPercent": self.homeTeamWinPercent,
            "awayTeamWinPercent": self.awayTeamWinPercent,
            "regulationTiePercent": self.regulationTiePercent,
            "homeTeamGoalsPrediction": self.homeTeamGoalsPrediction,
            "homeTeamGoalsActual": self.homeTeamGoalsActual,
            "awayTeamGoalsPrediction": self.awayTeamGoalsPrediction,
            "awayTeamGoalsActual": self.awayTeamGoalsActual,
        }

    def fromJson(self, jsonData):
        for key, value in jsonData:
            if key in ("homeTeamEvents", "awayTeamEvents"):
                # TODO: this is a massive amount of data, so skipping for now above
                setattr(self, key, [NHLData(x) for x in value])
            else:
                setattr(self, key, value)