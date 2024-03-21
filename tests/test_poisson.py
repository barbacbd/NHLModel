# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-builtin
# pylint: disable=deprecated-method
from unittest import TestCase
from os.path import dirname, abspath, join, exists
from json import loads
from collections import defaultdict
from shutil import copytree, rmtree
from nhl_core.endpoints import MAX_GAME_NUMBER
from nhl_model.poisson import (
    parseSchedule,
    calculateAvgGoals,
    calculateScores,
    getSeasonEventsFromSchedules,
)

BADSEASON = 2004
GOODSEASON = 2005
TOPSEASON = 2006

def mocked_schedules_get(year):
    if year is None or year == BADSEASON:
        return None

    currDir = dirname(abspath(__file__))
    splitDir = currDir.split("/")
    splitDir = splitDir[:-1] + ["src", "nhl_model", "support", "schedules", f"{year}", "schedule.json"]
    filename = "/" + join(*splitDir)

    with open(filename, "rb") as jsonData:
        return loads(jsonData.read())


class PoissonTests(TestCase):
    '''Test cases for the Poisson functionality to the module.
    '''

    @classmethod
    def setUpClass(cls):
        '''Set up the class for testing the dataset'''
        currDir = dirname(abspath(__file__))

        # Grab and save the data in the GOOD SEASON
        splitDir = currDir.split("/")
        splitDir = splitDir[:-1] + ["src", "nhl_model", "support", "schedules", f"{GOODSEASON}"]
        copyDir = "/" + join(*splitDir)
        cls.destDir = "/".join([currDir, f"{GOODSEASON}"])

        if exists(cls.destDir):
            rmtree(cls.destDir, ignore_errors=True)

        copytree(copyDir, cls.destDir)

        with open("/".join([cls.destDir, "schedule.json"])) as jsonData:
            cls.jsonSchedule = loads(jsonData.read())

        # Grab and save the data in the TOP SEASON
        splitDir = currDir.split("/")
        splitDir = splitDir[:-1] + ["src", "nhl_model", "support", "schedules", f"{TOPSEASON}"]
        copyDir = "/" + join(*splitDir)
        cls.destDirTop = "/".join([currDir, f"{TOPSEASON}"])

        if exists(cls.destDirTop):
            rmtree(cls.destDirTop, ignore_errors=True)

        copytree(copyDir, cls.destDirTop)

        with open("/".join([cls.destDirTop, "schedule.json"])) as jsonData:
            cls.jsonScheduleTop = loads(jsonData.read())

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        # cleanup everything that we copied in.
        rmtree(cls.destDir, ignore_errors=True)

        return super().tearDownClass()

    def test_parse_schedule_good(self):
        '''Test parsing a schedule.'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)
        self.assertIsNotNone(homeTeamEvents)
        self.assertIsNotNone(awayTeamEvents)

    def test_parse_schedule_bad(self):
        '''Test parsing a schedule that is None'''
        homeTeamEvents, awayTeamEvents = parseSchedule(None)
        self.assertTrue(isinstance(homeTeamEvents, defaultdict) and len(homeTeamEvents) == 0)
        self.assertTrue(isinstance(awayTeamEvents, defaultdict) and len(awayTeamEvents) == 0)

    def test_parse_schedule_empty_list(self):
        '''Test parsing a schedule that does not exist.'''
        homeTeamEvents, awayTeamEvents = parseSchedule([])
        self.assertTrue(isinstance(homeTeamEvents, defaultdict) and len(homeTeamEvents) == 0)
        self.assertTrue(isinstance(awayTeamEvents, defaultdict) and len(awayTeamEvents) == 0)

    def test_calculate_average_goals(self):
        '''Test parsing the schedule and getting the average number of goals.'''
        homeTeamEvents, _ = parseSchedule(self.jsonSchedule)
        avgGoalsScoredHomeTotal, _ = calculateAvgGoals(homeTeamEvents)
        self.assertAlmostEquals(avgGoalsScoredHomeTotal, 3.1797, places=4)

    def test_calculate_scores_single(self):
        '''Test a single entry to calculate scores for. In this case the team
        is the St. Louis Blues (id=19).'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)
        ids = [19]  # st louis blues

        scores = calculateScores(ids, homeTeamEvents, awayTeamEvents)
        for id in ids:
            with self.subTest(f"Ensure id {id} returned", id=id):
                self.assertTrue(id in scores)
                for key, value in scores[id].items():
                    with self.subTest(
                        f"Ensuring {id} is not None values", 
                        key=key,
                        value=value
                    ):
                        self.assertIsNotNone(value)

    def test_calculate_scores_multiple(self):
        '''Test multiple valid teams to calculate scores for. In this case two
        rivals are used, the St. Louis Blues(19) and the Chicago Blackhawks (16).'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)
        ids = [
            19,  # St. Louis Blues
            16,  # Chicago Blackhawks
        ]

        scores = calculateScores(ids, homeTeamEvents, awayTeamEvents)
        for id in ids:
            with self.subTest(f"Ensure id {id} returned", id=id):
                self.assertTrue(id in scores)
                for key, value in scores[id].items():
                    with self.subTest(
                        f"Ensuring {id} is not None values", 
                        key=key,
                        value=value
                    ):
                        self.assertIsNotNone(value)


    def test_calculate_scores_not_exist(self):
        '''Calculate the scores when the id does not exist.'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)
        ids = [
            600,  # unknown team
        ]

        scores = calculateScores(ids, homeTeamEvents, awayTeamEvents)
        for id in ids:
            with self.subTest(f"Ensure id {id} not returned", id=id):
                self.assertTrue(id in scores)
                for key, value in scores[id].items():
                    with self.subTest(
                        f"Ensuring {id} is all None values", 
                        key=key,
                        value=value
                    ):
                        self.assertIsNone(value)

    def test_calculate_scores_empty(self):
        '''Calculate the scores (should be empty) when an empty list of ids is passed.'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)
        scores = calculateScores([], homeTeamEvents, awayTeamEvents)
        self.assertTrue(len(scores) == 0)

    def test_calculate_scores_multi_with_invalid(self):
        '''Calculate the scores for each team knowing that one of the ids is not
        valid.'''
        homeTeamEvents, awayTeamEvents = parseSchedule(self.jsonSchedule)

        validIds = [19]  # St. Louis Blues
        invalidIds = [600]  # unknown team

        ids = validIds + invalidIds

        scores = calculateScores(ids, homeTeamEvents, awayTeamEvents)
        for id in validIds:
            with self.subTest(f"Ensure id {id} returned", id=id):
                self.assertTrue(id in scores)
                for key, value in scores[id].items():
                    with self.subTest(
                        f"Ensuring {id} is not None values", 
                        key=key,
                        value=value
                    ):
                        self.assertIsNotNone(value)

        for id in invalidIds:
            with self.subTest(f"Ensure id {id} not returned", id=id):
                self.assertTrue(id in scores)
                for key, value in scores[id].items():
                    with self.subTest(
                        f"Ensuring {id} is all None values", 
                        key=key,
                        value=value
                    ):
                        self.assertIsNone(value)

    def test_parse_season_events_no_schedule(self):
        '''Test when the schedule is None'''
        parsedHomeTeamEvents, parsedAwayTeamEvents = getSeasonEventsFromSchedules(
            None, self.jsonSchedule
        )

        self.assertIsNone(parsedHomeTeamEvents)
        self.assertIsNone(parsedAwayTeamEvents)

    def test_parse_season_events_no_previous(self):
        '''Test when the previous schedule is None'''
        parsedHomeTeamEvents, parsedAwayTeamEvents = getSeasonEventsFromSchedules(
            self.jsonScheduleTop, None
        )

        self.assertIsNone(parsedHomeTeamEvents)
        self.assertIsNone(parsedAwayTeamEvents)

    def test_parse_season_events(self):
        parsedHomeTeamEvents, parsedAwayTeamEvents = getSeasonEventsFromSchedules(
            self.jsonScheduleTop, self.jsonSchedule
        )

        # each game is both an away and home event so there should be entries for
        # all teams.
        self.assertEqual(len(parsedHomeTeamEvents), len(parsedAwayTeamEvents))

        total = 0
        for key in parsedHomeTeamEvents:
            total += len(parsedHomeTeamEvents[key])

        # These schedules do NOT include the full expansion teams so the number
        # of games should be less than max
        self.assertLess(total, MAX_GAME_NUMBER)
