# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
from unittest import TestCase
from nhl_model.event import (
    Game,
)


class EventClassTests(TestCase):
    '''Test cases for the Event functionality to the module.'''

    @classmethod
    def setUpClass(cls):
        '''Create an event that will be used for testing.'''
        cls.regulationTiePerent = 0.25  # always the same

        cls.homeTeamWinExpected = Game(gameId=0, homeTeamId=1, awayTeamId=2)
        cls.homeTeamWinExpected.fromJson({
            "homeTeamWinPercent": 0.43,
            "awayTeamWinPercent": 0.32,
            "regulationTiePercent": cls.regulationTiePerent,
            "homeTeamGoalsPrediction": 3,
            "homeTeamGoalsActual": 5,
            "awayTeamGoalsPrediction": 2,
            "awayTeamGoalsActual": 1,
        })

        cls.homeTeamLoseNotExpected = Game(gameId=0, homeTeamId=1, awayTeamId=2)
        cls.homeTeamLoseNotExpected.fromJson({
            "homeTeamWinPercent": 0.43,
            "awayTeamWinPercent": 0.32,
            "regulationTiePercent": cls.regulationTiePerent,
            "homeTeamGoalsPrediction": 3,
            "homeTeamGoalsActual": 1,
            "awayTeamGoalsPrediction": 2,
            "awayTeamGoalsActual": 5,
        })

        cls.awayTeamWinExpected = Game(gameId=0, homeTeamId=1, awayTeamId=2)
        cls.awayTeamWinExpected.fromJson({
            "homeTeamWinPercent": 0.32,
            "awayTeamWinPercent": 0.43,
            "regulationTiePercent": cls.regulationTiePerent,
            "homeTeamGoalsPrediction": 2,
            "homeTeamGoalsActual": 1,
            "awayTeamGoalsPrediction": 3,
            "awayTeamGoalsActual": 4,
        })

        cls.awayTeamLoseNotExpected = Game(gameId=0, homeTeamId=1, awayTeamId=2)
        cls.awayTeamLoseNotExpected.fromJson({
            "homeTeamWinPercent": 0.32,
            "awayTeamWinPercent": 0.43,
            "regulationTiePercent": cls.regulationTiePerent,
            "homeTeamGoalsPrediction": 2,
            "homeTeamGoalsActual": 8,
            "awayTeamGoalsPrediction": 3,
            "awayTeamGoalsActual": 2,
        })

        cls.invalidEvent = Game(gameId=1)

        return super().setUpClass()

    def test_winner_predicted(self):
        '''Test that the winner was predicted correctly in all events.'''
        events = {
            self.homeTeamWinExpected: True,
            self.homeTeamLoseNotExpected: False,
            self.awayTeamWinExpected: True,
            self.awayTeamLoseNotExpected: False,
        }

        for key, value in events.items():
            with self.subTest(f"testing predicted winners", key=key, value=value):
                self.assertEqual(key.winnerPredicted, value)

    def test_winner(self):
        '''Test winner value returned.'''
        events = {
            self.homeTeamWinExpected: "home",
            self.homeTeamLoseNotExpected: "away",
            self.awayTeamWinExpected: "away",
            self.awayTeamLoseNotExpected: "home",
        }

        for key, value in events.items():
            with self.subTest(f"testing winners", key=key, value=value):
                self.assertEqual(key.winner, value)

    def test_total_goals(self):
        '''Test total goals.'''
        events = {
            self.homeTeamWinExpected: 6,
            self.homeTeamLoseNotExpected: 6,
            self.awayTeamWinExpected: 5,
            self.awayTeamLoseNotExpected: 10,
        }

        for key, value in events.items():
            with self.subTest(f"testing total goals", key=key, value=value):
                self.assertEqual(key.totalGoals, value)

    def test_valid(self):
        '''Test that the event (game) is valid.'''
        events = {
            self.homeTeamWinExpected: True,
            self.homeTeamLoseNotExpected: True,
            self.awayTeamWinExpected: True,
            self.awayTeamLoseNotExpected: True,
            self.invalidEvent: False
        }

        for key, value in events.items():
            with self.subTest(f"testing validity", key=key, value=value):
                self.assertEqual(key.valid, value)
