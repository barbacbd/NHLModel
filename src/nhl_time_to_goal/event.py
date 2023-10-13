from enum import Enum


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
    def __init__(self, homeTeamId=None, awayTeamId=None):
        self.homeTeamId = homeTeamId
        self.awayTeamId = awayTeamId
        self.homeTeamEvents = []
        self.awayTeamEvents = []

    @property
    def valid(self):
        # technically it is possible to have no events saved, but the team Ids must be present
        return None not in (self.homeTeamId, self.awayTeamId)
    
    @property
    def json(self):
        return {
            "homeTeamId": self.homeTeamId,
            "awayTeamId": self.awayTeamId,
            "homeTeamEvents": len(self.homeTeamEvents),
            "awayTeamEvents": len(self.awayTeamEvents)
        }
