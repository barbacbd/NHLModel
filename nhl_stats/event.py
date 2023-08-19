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




class Event:

    def __init__(self, eventId=None):
        self.eventId = eventId

        # True -> Goal
        self.success = False

        self.eventType = None

        self.coordinates = {}

        self.periodTime = 0.0
        self.periodTimeRemaining = 0.0
        self.period = 0
        self.periodType = None

        self.priorShots = []

    @property
    def numPriorEvents(self):
        return len(priorShots)
