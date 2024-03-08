# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
from unittest import TestCase, mock
from datetime import datetime
from os.path import dirname, abspath, join, exists
from os import remove
from shutil import move, copy
from json import loads
import pandas as pd
from nhl_model.ann import (
    CONFIG_FILE,
    correctData,
    _createArtifactDir,  # private but using anyways
    findGamesByDate,
    findTodaysGames,
    _getTeamNames,
    _loadConfig,  # private but testing this anyways
    prepareDataForPredictions,

)
from nhl_model.enums import CompareFunction


# Fake file for configuration - TESTING ONLY
_CONFIG_FILE_TEST_PATH = CONFIG_FILE + ".savedfortest"

# List of columns expected to be dropped
_expectedDropped = ["atTeamname", "atTricode", "htTeamname", "htTricode", "winner"]

def _createDateStr(year, month, day):
    searchDate = datetime(year, month, day)
    return f'https://api-web.nhle.com/v1/score/{searchDate.strftime("%Y-%m-%d")}'

def _createTodaysDateStr():
    now = datetime.now()
    return _createDateStr(now.year, now.month, now.day)

def _readJsonData():
    filename = join(dirname(abspath(__file__)), "MockData.json")
    with open(filename, "r") as jsonFile:
        jsonData = loads(jsonFile.read())
    return jsonData

def _moveConfigFile():
    if exists(CONFIG_FILE):
        move(CONFIG_FILE, _CONFIG_FILE_TEST_PATH)
        return True
    return False

def _setConfigFile():
    filename = join(dirname(abspath(__file__)), "mock_config.json")
    copy(filename, CONFIG_FILE)

def _moveConfigFileBack(moved):
    if moved:
        if exists(CONFIG_FILE):
            remove(CONFIG_FILE)

        if exists(_CONFIG_FILE_TEST_PATH):
            move(_CONFIG_FILE_TEST_PATH, CONFIG_FILE)

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
    if args[0] == _createTodaysDateStr():
        return MockResponse(_readJsonData()["today"], 200)
    if 'https://api-web.nhle.com/v1/score/' in args[0]:
        return MockResponse(_readJsonData()["other"], 200)

    return MockResponse(None, 404)


class ANNClassTests(TestCase):
    '''Test cases for the ANN functionality to the module.'''

    @classmethod
    def setUpClass(cls):
        '''Ensure that the artifact directory exists for testing purposes.'''
        _createArtifactDir()
        return super().setUpClass()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_find_todays_games(self, mock_get):
        '''Mock the results for request.get when calling nhl_model functions
        that require this function. The results will include faked data for
        todays games.
        '''
        response = findTodaysGames()
        self.assertIsNotNone(response)


    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_find_games_by_date(self, mock_get):
        '''Mock the results for request.get when calling nhl_model functions
        that require this function. The results will include faked data for
        games on a specific date.
        '''
        now = datetime.now()

        # technically none of this matters but set to a valid date
        year = now.year
        month = now.month
        day = now.day
        if day - 1 <= 0:
            if month - 1 <= 0:
                year = year - 1
                month = 12
            else:
                month = month - 1

            # set to the min of the max days in any month
            day = 28
        else:
            day = day - 1

        otherResponse = findGamesByDate(day, month, year)
        todaysResponse = findTodaysGames()
        self.assertIsNotNone(otherResponse)
        self.assertIsNotNone(todaysResponse)
        self.assertTrue(otherResponse != todaysResponse)


    def test_load_config_not_exist(self):
        '''Test loading an empty config file - expected result is empty'''
        moved = _moveConfigFile()
        results = _loadConfig()
        self.assertDictEqual(results, {})
        _moveConfigFileBack(moved)


    def test_load_config_not_exist_override(self):
        '''Test loading an empty/overridden config file - expected result is empty'''
        moved = _moveConfigFile()
        results = _loadConfig(True)
        self.assertDictEqual(results, {})
        _moveConfigFileBack(moved)


    def test_load_config_exists(self):
        '''Test loading an empty config file - expected result is not empty'''
        moved = _moveConfigFile()
        _setConfigFile()
        results = _loadConfig()
        self.assertIsNotNone(results)
        _moveConfigFileBack(moved)


    def test_load_config_exists_override(self):
        '''Test loading an overridden config - expected result is empty'''
        moved = _moveConfigFile()
        _setConfigFile()
        results = _loadConfig(True)
        self.assertDictEqual(results, {})
        _moveConfigFileBack(moved)


    def test_get_team_names(self):
        '''This is a simple function to test that the metadata was included
        with the installation of the package. If this does not exist there will 
        be issues!
        '''
        results = _getTeamNames()
        # we aren't checking what is in this file, it just cannot be empty
        self.assertIsNotNone(results)


    def test_correct_data_analysis_file_base(self):
        '''Test that the analysis file is corrected. This means that the labels
            atTeamname, atTriCode, htTeamname, htTricode
        are dropped. The winner label is stripped and returned as another value.
        '''
        filename = join(dirname(abspath(__file__)), "mock_analysis.xlsx")
        df = pd.read_excel(filename)

        beforeCols = df.head()

        # base -> droppable is an empty list
        correctedDf, winners = correctData(df, droppable=[])
        self.assertIsNotNone(winners)
        afterCols = correctedDf.head()

        for i in _expectedDropped:
            with self.subTest(f"Ensuring {i} is dropped during correction", i=i):
                self.assertTrue(i not in afterCols and i in beforeCols)


    def test_correct_data_analysis_file_extra(self):
        '''Test that the analysis file is corrected. This means that the labels
            atTeamname, atTriCode, htTeamname, htTricode, htTeamid
        are dropped. The winner label is stripped and returned as another value.
        '''
        filename = join(dirname(abspath(__file__)), "mock_analysis.xlsx")
        df = pd.read_excel(filename)

        beforeCols = df.head()
        droppable=["htTeamid"]

        # base -> droppable is an empty list
        correctedDf, winners = correctData(df, droppable=droppable)
        self.assertIsNotNone(winners)
        afterCols = correctedDf.head()

        expectedDropped = _expectedDropped + droppable

        for i in expectedDropped:
            with self.subTest(f"Ensuring {i} is dropped during correction", i=i):
                self.assertTrue(i not in afterCols and i in beforeCols)


    def test_correct_data_predictions_file_base(self):
        '''Test that the predictions file is corrected. This means that the labels
            atTeamname, atTriCode, htTeamname, htTricode
        are dropped. The winner label is stripped and returned as another value.
        '''
        filename = join(dirname(abspath(__file__)), "mock_predictions.xlsx")
        df = pd.read_excel(filename)

        beforeCols = df.head()

        # base -> droppable is an empty list
        correctedDf, winners = correctData(df, droppable=[])
        self.assertIsNotNone(winners)
        afterCols = correctedDf.head()

        for i in _expectedDropped:
            with self.subTest(f"Ensuring {i} is dropped during correction", i=i):
                self.assertTrue(i not in afterCols and i in beforeCols)


    def test_correct_data_predictions_file_extra(self):
        '''Test that the predictions file is corrected. This means that the labels
            atTeamname, atTriCode, htTeamname, htTricode, htTeamid
        are dropped. The winner label is stripped and returned as another value.
        '''
        filename = join(dirname(abspath(__file__)), "mock_predictions.xlsx")
        df = pd.read_excel(filename)

        beforeCols = df.head()
        droppable=["htTeamid"]

        # base -> droppable is an empty list
        correctedDf, winners = correctData(df, droppable=droppable)
        self.assertIsNotNone(winners)
        afterCols = correctedDf.head()

        expectedDropped = _expectedDropped + droppable

        for i in expectedDropped:
            with self.subTest(f"Ensuring {i} is dropped during correction", i=i):
                self.assertTrue(i not in afterCols and i in beforeCols)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_prepare_predictions_today(self, mock_get):
        '''Test preparing the data for predictions. This test will use the
        DIRECT and AVERAGES comparison methods.
        '''
        compareFunctions = [CompareFunction.DIRECT, CompareFunction.AVERAGES]
        filename = join(dirname(abspath(__file__)), "mock_predictions.xlsx")
        today = datetime.now()

        for compareFunction in compareFunctions:
            with self.subTest(
                f"Testing prepare predictions {compareFunction.name} for today", 
                compareFunction=compareFunction
            ):
                preparedDf = prepareDataForPredictions(
                    filename,
                    compareFunction,
                    today.day,
                    today.month,
                    today.year
                )
                self.assertIsNotNone(preparedDf)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_prepare_predictions_direct_other(self, mock_get):
        '''Test preparing the data for predictions. This test will use the
        DIRECT and AVERAGES comparison methods.
        '''
        compareFunctions = [CompareFunction.DIRECT, CompareFunction.AVERAGES]
        filename = join(dirname(abspath(__file__)), "mock_predictions.xlsx")
        now = datetime.now()

        # technically none of this matters but set to a valid date
        year = now.year
        month = now.month
        day = now.day
        if day - 1 <= 0:
            if month - 1 <= 0:
                year = year - 1
                month = 12
            else:
                month = month - 1

            # set to the min of the max days in any month
            day = 28
        else:
            day = day - 1

        for compareFunction in compareFunctions:
            with self.subTest(
                f"Testing prepare predictions {compareFunction.name} for other date", 
                compareFunction=compareFunction
            ):
                preparedDf = prepareDataForPredictions(
                    filename,
                    compareFunction,
                    day,
                    month,
                    year
                )
                self.assertIsNotNone(preparedDf)
