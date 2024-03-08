from enum import Enum


class CompareFunction(Enum):
    '''Types of functions used for comparing data.'''
    # The default comparison function. AVERAGES takes all of the data points for
    # the home and away team when they were home and away respectively, the data
    # points are averaged for all games of this type. For instance, if the home team
    # scored 4, 5, 6 goals in their three home games, the average number of goals
    # value would be 5 for goals.
    AVERAGES = 'averages'

    # Direct indicates that (when applicable) the home and away team
    # values should be used from the games in which they played each other
    # if this data cannot be found, then the AVERAGES method is used.
    # There must be a record of the home team being the home team and the
    # away team being the away team when the two teams played each other.
    DIRECT = 'direct'


class EventType(Enum):
    """
    Current list of event Types.

    Note: Only supported events include shot types
    """
    SHOT = 'Shot'
    GOAL = 'Goal'
    BLOCKED_SHOT = 'Blocked Shot'
    MISSED_SHOT = 'Missed Shot'


class TeamSide(Enum):
    '''Simple identifier to indicate home vs away status of 
    a team during a game.
    '''
    AWAY = 0
    HOME = 1


class Version(Enum):
    '''Type/Version of the API to use for data.'''
    # The new version will pull the data directly from the new
    # version of the API.
    NEW = "new"

    # The old version requires the data is located in the `support`
    # directory in data/nhl_data subdirectories
    OLD = "old"
