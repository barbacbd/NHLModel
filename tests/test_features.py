# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
from unittest import TestCase
from os.path import dirname, abspath, join
import pandas as pd
from nhl_model.ann import correctData
from nhl_model.features import (
    findFeaturesMRMR,
    findFeaturesF1Scores
)


class FeatureTests(TestCase):
    '''Test cases for the Features functionality to the module.
    '''

    @classmethod
    def setUpClass(cls):
        '''Set up the class for testing the dataset'''
        analysisFile = join(dirname(abspath(__file__)), "mock_analysis.xlsx")
        trainDF = pd.read_excel(analysisFile)
        # filter out the output/winner and a few categorical columns
        cls.trainDF, cls.trainOutput = correctData(trainDF, droppable=[])

        return super().setUpClass()

    def test_find_features_mrmr(self):
        '''Test the functionality of the feature finding algorithm wrapper for mRMR'''

        maxSize = self.trainDF.shape[1]

        _expectedResults = {
            None: 10,             # pick the optimal amount
            0: 10,                # same as above
            -1: 10,               # negative
            5: 5,                 # somewhere between max and min
            maxSize+1: maxSize-1, # greater than max size
            maxSize: maxSize-1    # one less than max size is returned when >= features
        }

        for key, value in _expectedResults.items():
            with self.subTest(f"testing MRMR {key}", key=key, value=value):
                features = findFeaturesMRMR(self.trainDF, self.trainOutput, K=key)
                self.assertEqual(value, len(features))

    def test_find_features_f1_scores(self):
        '''Test the functionality of the feature finding algorithm wrapper for F1 Scores'''
        # This is kind of a bad example as all values above 0.8 are 1 and everything
        # below is the size of the features list
        _expectedResults = {
            1.0: 1,
            0.90: 1,
            0.80: 55,
        }

        for key, value in _expectedResults.items():
            with self.subTest(f"testing f1 scores {key}", key=key, value=value):
                features = findFeaturesF1Scores(self.trainDF, self.trainOutput, precision=key)
                self.assertEqual(value, len(features))
