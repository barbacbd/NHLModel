
from collections import defaultdict
from datetime import datetime
import inquirer
from json import loads
from os.path import dirname, abspath, join as path_join, exists
from scipy.stats import poisson
from statistics import mean
from nhl_score_prediction.event import Game
import pandas as pd

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


def loadExcelFile(dirList):
    _currDir = dirname(abspath(__file__))
    splitDir = _currDir.split("/")
    splitDir = splitDir[:-1] + dirList

    filename = "/" + path_join(*splitDir)
    print(filename)
    if not exists(filename):
        return None

    return pd.read_excel(filename)


df = loadExcelFile(["support", "ANNDataset.xlsx"])
df.drop(columns=df.columns[0], axis=1, inplace=True)

# The output is the result of the game (winner or loser).
# TODO: should this be a numerical value 0/1
output = df["winner"]

# Drop the output from the Dataframe, leaving the only data left as
# the dataset to train.
df.drop(labels=["winner"], axis=1,inplace=True)

df.drop(labels=["teamName", "triCode", "attackStrength", "defenseStrength"], axis=1, inplace=True)

df.fillna(0, inplace=True)
numCols = df.shape[1]


model = Sequential()
# Create a model for a neural network with 3 layers
# According to a source online, ReLU activation function is best for layers 
# except the output layer, that layer should use Sigmoid. This is the case for
# performance reasons.
model.add(Dense(12, input_shape=(numCols,), activation='relu'))
model.add(Dense(8, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

dfTensor = tf.convert_to_tensor(df.to_numpy())
outputTensor = tf.convert_to_tensor(output.to_numpy())

model.fit(dfTensor, outputTensor, epochs=150, batch_size=10)

_, accuracy = model.evaluate(dfTensor,  outputTensor)
print('Accuracy: %.2f' % (accuracy*100))