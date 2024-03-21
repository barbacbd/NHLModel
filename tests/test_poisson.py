# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-builtin
# pylint: disable=deprecated-method
from unittest import TestCase
from os.path import dirname, abspath, join
from json import loads
from collections import defaultdict
from shutil import copytree, rmtree
from nhl_model.poisson import (
    parseSchedule,
    calculateAvgGoals,
    calculateScores
)

BADSEASON = 2004
GOODSEASON = 2005

class PoissonTests(TestCase):
    '''Test cases for the Poisson functionality to the module.
    '''

    @classmethod
    def setUpClass(cls):
        '''Set up the class for testing the dataset'''
        currDir = dirname(abspath(__file__))

        splitDir = currDir.split("/")
        splitDir = splitDir[:-1] + ["src", "nhl_model", "support", "schedules", "2005"]
        copyDir = "/" + join(*splitDir)
        cls.destDir = "/".join([currDir, f"{GOODSEASON}"])
        copytree(copyDir, cls.destDir)

        with open("/".join([cls.destDir, "schedule.json"])) as jsonData:
            cls.jsonSchedule = loads(jsonData.read())

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
