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
        

    @property
    def avgTimeToFirstGoalScored(self):
        # calculate the average time from the start of the game
        # until the first goal this team scored. The value in SECONDS
        # is returned
        return 0.0


    @property
    def avgTimeToFirstGoalAgainst(self):
        # calculate the average time from the start of the game
        # until the first goal this team lets in. The value in SECONDS
        # is returned
        return 0.0


    @property
    def avgGoalsScoredPerGame(self):
        # Find the total number of goals scored for all games where
        # the team matches the name of this instance. Take the average
        # of that value.
        return 0.0

    @property
    def avgGoalsAgainstPerGame(self):
        # Find the total number of goals against for all games where
        # the team matches the name of this instance. Take the average
        # of that value.
        return 0.0

    @property
    def maxGoalsScored(self):
        # find the max number of goals scored from all records
        return 0

    @property
    def maxGoalsAgainst(self):
        # find the max number of goals against from all records
        return 0


    @property
    def avgTimeBetweenGoalsScoredSecs(self):
        return 0.0
    
    @property
    def avgTimeBetweenGoalsAgainstSecs(self):
        return 0.0

    @property
    def avgShotsTakenBeforeGoalScored(self):
        return 0.0

    @property
    def avgShotsReceivedBeforeGoalScored(self):
        return 0.0
