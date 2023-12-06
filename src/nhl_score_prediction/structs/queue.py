

class RotatingQueue:

    """Rotating list that only keep the last maxSize entries."""

    def __init__(self, maxSize=10, data=[]):
        # default the size to 10 if the max entries is less than 1
        self.maxSize = maxSize if maxSize > 0 else 10

        self._data = []

        if isinstance(data, list):
            if len(data) <= self.maxSize:
                self._data = data
            else:
                _numToRemove = len(data) - self.maxSize
                self._data = data[_numToRemove:]

    def append(self, x):
        if len(self._data) == self.maxSize:
            self._data.pop(0)
        self._data.append(x)

    def clear(self):
        self._data.clear()
    
    def extend(self, x):
        _lenNewData = len(x)
        if len(self._data) + _lenNewData <= self.maxSize:
            self._data.extend(x)
        else:
            if _lenNewData >= self.maxSize:
                _numToRemove = _lenNewData - self.maxSize
                self._data = x[_numToRemove:]
            else:
                _numToRemove = len(self._data) + _lenNewData - self.maxSize
                self._data = self._data[_numToRemove:] + x

    def count(self, x):
        return self._data.count(x)

    def __len__(self):
        return len(self._data)

    def __contains__(self, item):
        return item in self._data
    


class NHLGameRecords(RotatingQueue):

    """Keep track of previous wins and losses in X number of games."""

    def __init__(self, maxSize=10, data=[]):
        super().__init__(maxSize=maxSize, data=data)

    def addWin(self):
        super().append(True)
    
    def addLoss(self):
        super().append(False)
    
    @property
    def winPercent(self):
        _len = len(self)
        if _len == 0:
            return 0.0
        return round((float(super().count(True)) / float(len(self))) * 100.0, 2)

    @property
    def losePercent(self):
        return 100.0 - self.winPercent

    @property
    def wins(self):
        return super().count(True)

    @property
    def losses(self):
        return super().count(False)