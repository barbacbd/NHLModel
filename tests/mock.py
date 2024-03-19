# pylint: disable=invalid-name
# pylint: disable=missing-function-docstring
import pytest

pytestmark = pytest.mark.skip("Class created for testing purposes only.")


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
