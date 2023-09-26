from enum import Enum


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




class TeamStats:

    """The team stats class contains the statistics for a team. The stats are
    valid for a single season.
    """
    
    def __init__(self, teamId=None, teamName=None):
        self.teamId = teamId
        self.name = teamName

        # Game ID -> all records for the game
        self._events = {}
            
        # The game records is a list of dictionaries where
        # The keys are the names of the teams, where one should
        # match the team of this instance
        self.gameRecords = []
        

    def avgTimeToFirstGoalScored(self):
        # calculate the average time from the start of the game
        # until the first goal this team scored (includes home and away games). 
        # The value in SECONDS is returned
        return 0.0

    def avgTimeToFirstGoalScoredHome(self):
        # calculate the average time from the start of the game
        # until the first goal this team scored during home games. 
        # The value in SECONDS is returned
        return 0.0
    
    def avgTimeToFirstGoalScoredAway(self):
        # calculate the average time from the start of the game
        # until the first goal this team scored during away games. 
        # The value in SECONDS is returned
        return 0.0
    
    def avgTimeToFirstGoalAgainst(self):
        # calculate the average time from the start of the game
        # until the first goal this team lets in (includes home and away games). 
        # The value in SECONDS is returned
        return 0.0

    def avgTimeToFirstGoalAgainstHome(self):
        # calculate the average time from the start of the game
        # until the first goal this team lets in for home games. 
        # The value in SECONDS is returned
        return 0.0
    
    def avgTimeToFirstGoalAgainstAway(self):
        # calculate the average time from the start of the game
        # until the first goal this team lets in for away games. 
        # The value in SECONDS is returned
        return 0.0

    def avgGoalsScoredPerGame(self):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value (includes home and away games).
        return 0.0

    def avgGoalsScoredPerGameHome(self):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Home games.
        return 0.0

    def avgGoalsScoredPerGameAway(self):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Away games.
        return 0.0

    def avgGoalsAgainstPerGame(self):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value (includes home and away games).
        return 0.0

    def avgGoalsAgainstPerGameHome(self):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Home games.
        return 0.0

    def avgGoalsAgainstPerGameAway(self):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value. This is only for Away games.
        return 0.0

    def maxGoalsScored(self):
        # find the max number of goals scored from all records
        return 0

    def maxGoalsScoredHome(self):
        # find the max number of goals scored from all Home records
        return 0
    
    def maxGoalsScoredAway(self):
        # find the max number of goals scored from all Away records
        return 0

    def maxGoalsAgainst(self):
        # find the max number of goals against from all records
        return 0

    def maxGoalsAgainstHome(self):
        # find the max number of goals against from all Home records
        return 0

    def maxGoalsAgainstAway(self):
        # find the max number of goals against from all Away records
        return 0

    def avgTimeBetweenGoalsScoredSecs(self):
        # Find the average number of seconds between goals scored by the team. 
        # This function does not include time before the first goal.
        return 0.0

    def avgTimeBetweenGoalsScoredSecsHome(self):
        # Find the average number of seconds between goals scored by the team
        # during home games. This function does not include time before the first goal.
        return 0.0
    
    def avgTimeBetweenGoalsScoredSecsAway(self):
        # Find the average number of seconds between goals scored by the team
        # during away games. This function does not include time before the first goal.
        return 0.0
    
    def avgTimeBetweenGoalsAgainstSecs(self):
        # Find the average number of seconds between goals scored by the opponent.
        # This function does not include time before the first goal.
        return 0.0

    def avgTimeBetweenGoalsAgainstSecsHome(self):
        # Find the average number of seconds between goals scored by the opponent
        # during home games. This function does not include time before the first goal.
        return 0.0

    def avgTimeBetweenGoalsAgainstSecsAway(self):
        # Find the average number of seconds between goals scored by the opponent
        # during away games. This function does not include time before the first goal.
        return 0.0

    def avgShotsTakenBeforeGoalScored(self):
        # Find the average number of shots taken between goals. This includes
        # the first goal of the game.
        return 0.0

    def avgShotsTakenBeforeGoalScoredHome(self):
        # Find the average number of shots taken between goals for home games. This includes
        # the first goal of the game.
        return 0.0
    
    def avgShotsTakenBeforeGoalScoredAway(self):
        # Find the average number of shots taken between goals for away games. This includes
        # the first goal of the game.
        return 0.0

    def avgShotsReceivedBeforeGoalScored(self):
        # Find the average number of shots against us between goals. This includes 
        # the first goal of the game.
        return 0.0

    def avgShotsReceivedBeforeGoalScoredHome(self):
        # Find the average number of shots against us between goals for home games. This includes 
        # the first goal of the game.
        return 0.0

    def avgShotsReceivedBeforeGoalScoredAway(self):
        # Find the average number of shots against us between goals for away games. This includes 
        # the first goal of the game.
        return 0.0
