from nhl_score_prediction.structs.queue import RotatingQueue, NHLGameRecords
from unittest import main, TestCase


class TestQueue(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxSize = 10
        cls.rQueue = RotatingQueue(
            maxSize=cls.maxSize, 
            data=[]  # empty
        )

        cls.NHLQueue = NHLGameRecords(
            maxSize=cls.maxSize,
            data=[]  # empty
        )

    def test_01_add_to_rqueue(self):
        # add a single value to empty list
        self.assertEqual(len(self.rQueue), 0)
        self.rQueue.append(0)
        self.assertEqual(len(self.rQueue), 1)


    def test_02_count_single_value(self):
        # count the number of entries for "0"
        self.assertEqual(self.rQueue.count(0), 1)


    def test_03_expand_rqueue(self):
        # expand a valid number of values to the queue
        self.rQueue.extend(
            [x for x in range(1, self.maxSize)]
        )
        self.assertEqual(len(self.rQueue), self.maxSize)


    def test_04_add_to_rqueue_circle(self):
        # add a new value to the rotating queue which should 
        # drop a value from the front and add the new value
        self.rQueue.append(20)
        self.assertEqual(self.rQueue.count(0), 0)
        self.assertEqual(self.rQueue.count(20), 1)
        self.assertEqual(len(self.rQueue), self.maxSize)


    def test_05_extend_rqueue_add_few_to_full(self):
        # add a few extra values to the list. 
        listToAdd = [30, 40, 50]
        self.rQueue.extend(listToAdd)

        for x in listToAdd:
            with self.subTest(f"Testing {x} appears once in the list", x=x):
                self.assertTrue(self.rQueue.count(x) == 1)

        self.assertEqual(len(self.rQueue), self.maxSize)


    def test_06_extend_rqueue_too_many(self):
        # Extend by too many values, but only the max size should be kept
        listToAdd = [x*10 for x in range(self.maxSize*2)]
        self.rQueue.extend(listToAdd)

        lenToUse = len(listToAdd)-self.maxSize
        compareList = listToAdd[lenToUse:]
        for x in compareList:
            with self.subTest(f"Testing {x} appears once in the list", x=x):
                self.assertTrue(self.rQueue.count(x) == 1)

        self.assertEqual(len(self.rQueue), self.maxSize)



