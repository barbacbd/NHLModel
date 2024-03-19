# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
from unittest import TestCase, mock
from nhl_model.dataset import (
    parseBoxScore,
    parseBoxScoreSplit,
    parseBoxScoreNew,
    parseBoxScoreNewSplit,
    pullDatasetNewAPI,
    RecoveryFilename,
    newAPIFile,
    BASE_SAVE_DIR
)
from nhl_core.endpoints import MAX_GAME_NUMBER
from os.path import dirname, abspath, join, exists
from json import loads, dumps
from datetime import datetime
from shutil import move
from os import remove, mkdir


def _movedFile(filename):
    if exists(filename):
        move(filename, f"{filename}.old")
        return True
    return False


def _moveFileBack(filename, moved):
    if moved:
        if exists(filename):
            remove(filename)
        if exists(f"{filename}.old"):
            move(f"{filename}.old", filename)


class MockResponse:
    '''Class to mock the behavior and results of the requests.get function
    in the findGamesByDate function.
    '''

    def __init__(self, data, status_code):
        '''Fill the class with the required data for a response'''
        self.data = data
        self.code = status_code

    def read(self):
        return self.data

    def json(self):
        return self.data


def mocked_requests_get(*args, **kwargs):
    filename = join(dirname(abspath(__file__)), "DatasetMockData.json")
    with open(filename, "r") as jsonFile:
        jsonData = loads(jsonFile.read())
    
    if jsonData is not None:
        return MockResponse(jsonData, 200)
    return MockResponse(jsonData, 400)


class DatasetTests(TestCase):
    '''Test cases for the Dataset functionality to the module.
    
    Note: The tests do NOT currently cover:
    - parseRecentData (this is currently not used)
    - pullDatasetNewAPI 
    - generateDataset (technically this is mostly covered through the other tests)
    '''

    @classmethod
    def setUpClass(cls):
        '''Set up the class for testing the dataset'''
        oldFile = join(dirname(abspath(__file__)), "MockDataOld.json")
        with open(oldFile, "r") as jsonFile:
            cls.oldJsonData = loads(jsonFile.read())

        oldGameInfo = cls.oldJsonData["gameData"]
        cls.oldDataBoxScore = cls.oldJsonData["liveData"]["boxscore"]

        cls.oldGameData = {
            "gameId": oldGameInfo["game"]["pk"],             
        }
    
        newFile = join(dirname(abspath(__file__)), "MockDataNew.json")
        with open(newFile, "r") as jsonFile:
            cls.newJsonData = loads(jsonFile.read())
        cls.newDataBoxScore = cls.newJsonData["boxScores"]["1"]

        return super().setUpClass()


    def test_parse_boxscore(self):
        '''Test the functionality of the parse box score. This only tests the
        functionality of old data. Technically this method is considered deprecated
        so this isn't expected, but the functions need to be tested.
        '''
        _expectedResults = {
            "htTeamid": 18,
            "htTeamname": "Nashville Predators",
            "htTricode": "NSH",
            "htGoals": 4,
            "htPim": 13,
            "htShots": 32,
            "htPowerplaypercentage": "0.0",
            "htPowerplaygoals": 0.0,
            "htPowerplayopportunities": 4.0,
            "htFaceoffwinpercentage": "45.5",
            "htBlocked": 11,
            "htHits": 23,
            "htAssists": 8,
            "htPowerplayassists": 0,
            "htShorthandedassists": 0,
            "htShorthandedgoals": 0,
            "htSaves": 30,
            "htPowerplaysaves": 8,
            "htShorthandedsaves": 0,
            "htEvensaves": 22,
            "htShorthandedshotsagainst": 0,
            "htEvenshotsagainst": 23,
            "htPowerplayshotsagainst": 8,
            "htSavepercentage": 96.7741935483871,
            "htPowerplaysavepercentage": 100.0,
            "htShorthandedsavepercentage": None,
            "htEvenstrengthsavepercentage": 95.65217391304348,
            "htNumgoalies": 1,
            "htNumplayers": 18,
            "atTeamid": 28,
            "atTeamname": "San Jose Sharks",
            "atTricode": "SJS",
            "atGoals": 1,
            "atPim": 13,
            "atShots": 31,
            "atPowerplaypercentage": "0.0",
            "atPowerplaygoals": 0.0,
            "atPowerplayopportunities": 4.0,
            "atFaceoffwinpercentage": "54.5",
            "atBlocked": 23,
            "atHits": 22,
            "atAssists": 2,
            "atPowerplayassists": 0,
            "atShorthandedassists": 0,
            "atShorthandedgoals": 0,
            "atSaves": 28,
            "atPowerplaysaves": 8,
            "atShorthandedsaves": 1,
            "atEvensaves": 19,
            "atShorthandedshotsagainst": 1,
            "atEvenshotsagainst": 22,
            "atPowerplayshotsagainst": 8,
            "atSavepercentage": 90.32258064516128,
            "atPowerplaysavepercentage": 100.0,
            "atShorthandedsavepercentage": 100.0,
            "atEvenstrengthsavepercentage": 86.36363636363636,
            "atNumgoalies": 1,
            "atNumplayers": 18,
            "gameId": 2022020001,
            "winner": True
        }

        gameData = parseBoxScore(self.oldDataBoxScore)
        gameData.update(self.oldGameData)
        # add the winner information
        gameData.update({
            "winner": bool(gameData["htGoals"] > gameData["atGoals"])
        })

        for key, value in _expectedResults.items():
            with self.subTest(f"Ensuring {key} is found and correct", key=key, value=value):
                self.assertTrue(key in gameData)
                self.assertEqual(value, gameData[key])

    def test_parse_boxscoresplit(self):
        '''Test the functionality of the parse box score split function that returns the data
        for the home and away teams separately. This only tests the
        functionality of old data. Technically this method is considered deprecated
        so this isn't expected, but the functions need to be tested.
        '''
        _expectedHomeTeamResults = {
            "teamId": 18,
            "teamName": "Nashville Predators",
            "triCode": "NSH",
            "goals": 4,
            "pim": 13,
            "shots": 32,
            "powerPlayPercentage": "0.0",
            "powerPlayGoals": 0.0,
            "powerPlayOpportunities": 4.0,
            "faceOffWinPercentage": "45.5",
            "blocked": 11,
            "hits": 23,
            "assists": 8,
            "powerPlayAssists": 0,
            "shortHandedAssists": 0,
            "shortHandedGoals": 0,
            "saves": 30,
            "powerPlaySaves": 8,
            "shortHandedSaves": 0,
            "evenSaves": 22,
            "shortHandedShotsAgainst": 0,
            "evenShotsAgainst": 23,
            "powerPlayShotsAgainst": 8,
            "savePercentage": 96.7741935483871,
            "powerPlaySavePercentage": 100.0,
            "shortHandedSavePercentage": None,
            "evenStrengthSavePercentage": 95.65217391304348,
            "numGoalies": 1,
            "numPlayers": 18,
            "teamType": 1
        }

        _expectedAwayTeamResults = {
            "teamId": 28,
            "teamName": "San Jose Sharks",
            "triCode": "SJS",
            "goals": 1,
            "pim": 13,
            "shots": 31,
            "powerPlayPercentage": "0.0",
            "powerPlayGoals": 0.0,
            "powerPlayOpportunities": 4.0,
            "faceOffWinPercentage": "54.5",
            "blocked": 23,
            "hits": 22,
            "assists": 2,
            "powerPlayAssists": 0,
            "shortHandedAssists": 0,
            "shortHandedGoals": 0,
            "saves": 28,
            "powerPlaySaves": 8,
            "shortHandedSaves": 1,
            "evenSaves": 19,
            "shortHandedShotsAgainst": 1,
            "evenShotsAgainst": 22,
            "powerPlayShotsAgainst": 8,
            "savePercentage": 90.32258064516128,
            "powerPlaySavePercentage": 100.0,
            "shortHandedSavePercentage": 100.0,
            "evenStrengthSavePercentage": 86.36363636363636,
            "numGoalies": 1,
            "numPlayers": 18,
            "teamType": 0
        }

        homeTeamData, awayTeamData = parseBoxScoreSplit(self.oldDataBoxScore)

        for key, value in _expectedHomeTeamResults.items():
            with self.subTest(f"Ensuring {key} is found and correct for home team", key=key, value=value):
                self.assertTrue(key in homeTeamData)
                self.assertEqual(value, homeTeamData[key])

        for key, value in _expectedAwayTeamResults.items():
            with self.subTest(f"Ensuring {key} is found and correct for away team", key=key, value=value):
                self.assertTrue(key in awayTeamData)
                self.assertEqual(value, awayTeamData[key])
    
    def test_parse_boxscore_new(self):
        '''Test the functionality of the parse box score for new datasets.'''
        _expectedResults = {
            "htTeamid": 18,
            "htTeamname": "Predators",
            "htTricode": "NSH",
            "htGoals": 4,
            "htPim": 13,
            "htShots": 32,
            "htFaceoffwinpercentage": 45.5,
            "htBlocked": 11,
            "htHits": 23,
            "htPowerplaypercentage": 0.0,
            "htPowerplaygoals": 0,
            "htPowerplayopportunities": 4,
            "htAssists": 8,
            "htShorthandedgoals": 0,
            "htShorthandedassists": 0,
            "htPowerplayassists": 0,
            "htSaves": 30,
            "htPowerplaysaves": 8,
            "htShorthandedsaves": 0,
            "htEvensaves": 22,
            "htShorthandedshotsagainst": 0,
            "htEvenshotsagainst": 23,
            "htPowerplayshotsagainst": 8,
            "htSavepercentage": 96.77,
            "htPowerplaysavepercentage": 100.0,
            "htShorthandedsavepercentage": 0.0,
            "htEvenstrengthsavepercentage": 95.65,
            "htNumgoalies": 1,
            "htNumplayers": 18,
            "atTeamid": 28,
            "atTeamname": "Sharks",
            "atTricode": "SJS",
            "atGoals": 1,
            "atPim": 13,
            "atShots": 31,
            "atFaceoffwinpercentage": 54.5,
            "atBlocked": 23,
            "atHits": 22,
            "atPowerplaypercentage": 0.0,
            "atPowerplaygoals": 0,
            "atPowerplayopportunities": 4,
            "atAssists": 2,
            "atShorthandedgoals": 0,
            "atShorthandedassists": 0,
            "atPowerplayassists": 0,
            "atSaves": 28,
            "atPowerplaysaves": 8,
            "atShorthandedsaves": 1,
            "atEvensaves": 19,
            "atShorthandedshotsagainst": 1,
            "atEvenshotsagainst": 22,
            "atPowerplayshotsagainst": 8,
            "atSavepercentage": 90.32,
            "atPowerplaysavepercentage": 100.0,
            "atShorthandedsavepercentage": 100.0,
            "atEvenstrengthsavepercentage": 86.36,
            "atNumgoalies": 1,
            "atNumplayers": 18,
            "gameId": 2022020001,
            "winner": True
        }

        gameData = parseBoxScoreNew(self.newDataBoxScore)

        for key, value in _expectedResults.items():
            with self.subTest(f"Ensuring {key} is found and correct (new)", key=key, value=value):
                self.assertTrue(key in gameData)
                self.assertEqual(value, gameData[key])

    def test_parse_boxscoresplit_new(self):
        '''Test the functionality of the parse box score (new) split function that returns the data
        for the home and away teams separately.
        '''
        _expectedHomeTeamResults = {
            "teamId": 18,
            "teamName": "Predators",
            "triCode": "NSH",
            "goals": 4,
            "pim": 13,
            "shots": 32,
            "faceOffWinPercentage": 45.5,
            "blocked": 11,
            "hits": 23,
            "powerPlayPercentage": 0.0,
            "powerPlayGoals": 0,
            "powerPlayOpportunities": 4,
            "assists": 8,
            "shortHandedGoals": 0,
            "shortHandedAssists": 0,
            "powerPlayAssists": 0,
            "saves": 30,
            "powerPlaySaves": 8,
            "shortHandedSaves": 0,
            "evenSaves": 22,
            "shortHandedShotsAgainst": 0,
            "evenShotsAgainst": 23,
            "powerPlayShotsAgainst": 8,
            "savePercentage": 96.77,
            "powerPlaySavePercentage": 100.0,
            "shortHandedSavePercentage": 0.0,
            "evenStrengthSavePercentage": 95.65,
            "numGoalies": 1,
            "numPlayers": 18,
            "gameId": 2022020001
        }

        _expectedAwayTeamResults = {
            "teamId": 28,
            "teamName": "Sharks",
            "triCode": "SJS",
            "goals": 1,
            "pim": 13,
            "shots": 31,
            "faceOffWinPercentage": 54.5,
            "blocked": 23,
            "hits": 22,
            "powerPlayPercentage": 0.0,
            "powerPlayGoals": 0,
            "powerPlayOpportunities": 4,
            "assists": 2,
            "shortHandedGoals": 0,
            "shortHandedAssists": 0,
            "powerPlayAssists": 0,
            "saves": 28,
            "powerPlaySaves": 8,
            "shortHandedSaves": 1,
            "evenSaves": 19,
            "shortHandedShotsAgainst": 1,
            "evenShotsAgainst": 22,
            "powerPlayShotsAgainst": 8,
            "savePercentage": 90.32,
            "powerPlaySavePercentage": 100.0,
            "shortHandedSavePercentage": 100.0,
            "evenStrengthSavePercentage": 86.36,
            "numGoalies": 1,
            "numPlayers": 18,
            "gameId": 2022020001
        }

        homeTeamData, awayTeamData = parseBoxScoreNewSplit(self.newDataBoxScore)

        for key, value in _expectedHomeTeamResults.items():
            with self.subTest(f"Ensuring {key} is found and correct for home team (new)", key=key, value=value):
                self.assertTrue(key in homeTeamData)
                self.assertEqual(value, homeTeamData[key])

        for key, value in _expectedAwayTeamResults.items():
            with self.subTest(f"Ensuring {key} is found and correct for away team (new)", key=key, value=value):
                self.assertTrue(key in awayTeamData)
                self.assertEqual(value, awayTeamData[key])
    
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_pull_dataset_api_new_base(self, mock_get):
        '''Test pulling the dataset with the new api.'''
        now = datetime.now()

        year = now.year
        expectedResult = None

        # if it isn't september, the season hasn't started and should use previous year
        if datetime.now().month >= 9:
            expectedResult = newAPIFile(f"{year}-NHL-season.json")
        elif datetime.now().month <= 5:
            year -= 1
            expectedResult = newAPIFile(f"{year}-NHL-season.json")

        movedCurrFile = _movedFile(expectedResult) if expectedResult is not None else False
        movedRecoveryFile = _movedFile(RecoveryFilename)

        if not exists(BASE_SAVE_DIR):
            mkdir(BASE_SAVE_DIR)


        filename = join(dirname(abspath(__file__)), "DatasetMockData.json")
        with open(filename, "r") as jsonFile:
            readData = loads(jsonFile.read())

        # setting the game to the last one so that the search does NOT continue
        jsonData = {
            "metadata": {
                "date": "",
                "lastRegisteredGame": MAX_GAME_NUMBER,
                "year": year
            },
            "boxScores": readData["boxScores"]
        }

        with open(expectedResult, "w+") as jsonFile:
            jsonFile.write(dumps(jsonData, indent=2))

        currFilename = pullDatasetNewAPI(year)

        # move these back before running tests to ensure these are reset
        _moveFileBack(expectedResult, movedCurrFile)
        _moveFileBack(RecoveryFilename, movedRecoveryFile)

        if expectedResult is None:
            self.assertIsNone(currFilename)
        
        remove(currFilename)
        self.assertEqual(currFilename, expectedResult)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_pull_dataset_api_new_negative(self, mock_get):
        '''Test pulling the dataset with the new api.'''
        now = datetime.now()

        year = now.year
        expectedResult = None

        # if it isn't september, the season hasn't started and should use previous year
        if datetime.now().month >= 9:
            expectedResult = newAPIFile(f"{year}-NHL-season.json")
        elif datetime.now().month <= 5:
            year -= 1
            expectedResult = newAPIFile(f"{year}-NHL-season.json")

        movedCurrFile = _movedFile(expectedResult) if expectedResult is not None else False
        movedRecoveryFile = _movedFile(RecoveryFilename)

        if not exists(BASE_SAVE_DIR):
            mkdir(BASE_SAVE_DIR)


        filename = join(dirname(abspath(__file__)), "DatasetMockData.json")
        with open(filename, "r") as jsonFile:
            readData = loads(jsonFile.read())

        # setting the game to the negative number so that the search does NOT continue
        jsonData = {
            "metadata": {
                "date": "",
                "lastRegisteredGame": -2,
                "year": year
            },
            "boxScores": readData["boxScores"]
        }

        with open(expectedResult, "w+") as jsonFile:
            jsonFile.write(dumps(jsonData, indent=2))

        currFilename = pullDatasetNewAPI(year)

        # move these back before running tests to ensure these are reset
        _moveFileBack(expectedResult, movedCurrFile)
        _moveFileBack(RecoveryFilename, movedRecoveryFile)

        if expectedResult is None:
            self.assertIsNone(currFilename)
        
        remove(currFilename)
        self.assertEqual(currFilename, expectedResult)

