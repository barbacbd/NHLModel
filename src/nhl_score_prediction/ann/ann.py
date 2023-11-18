
from collections import defaultdict
from datetime import datetime
import inquirer
from json import loads
from os import listdir
from os.path import dirname, abspath, join as path_join, exists
from scipy.stats import poisson
from statistics import mean
from nhl_score_prediction.event import Game
import pandas as pd

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


def inquireFiles():

    outputs = {}

    useModel = "no"

    questions = [
        inquirer.List('useModel', message="Would you like to use a saved model?", choices=["yes", "no"]),
    ]
    answers = inquirer.prompt(questions)
    useModel = answers['useModel']

    # The xlsx files are always output from the GenerateANNDataset.py script in support.
    # Look for the output files from that directory with an xlsx extension.
    analysisFile = ""
    sp = dirname(abspath(__file__)).split("/")
    dir = sp[:-1] + ["support"]
    locationPath = "/" + path_join(*dir)
    files = [x for x in listdir(locationPath) if x.endswith(".xlsx")]

    savedModelFile = "None"

    if useModel == "yes":
        # the saved file will be in this directory.
        potentialFiles = listdir(dirname(abspath(__file__)))
        potentialFiles.insert(0, savedModelFile)

        questions = [
            inquirer.List('savedModel', message="Select the model file.", choices=potentialFiles),
        ]
        answers = inquirer.prompt(questions)
        savedModelFile = answers['savedModel']

    # this way in the event that no model was selected continue processing
    if useModel == "no" or savedModelFile == "None":
        questions = [
            inquirer.List('analysisFile', message="File used to train the data.", choices=files),
        ]
        answers = inquirer.prompt(questions)
        analysisFile = answers["analysisFile"]

        outputs["analysisFile"] = path_join(*[locationPath, analysisFile])
    else:
        outputs["savedModelFile"] = path_join(*[dirname(abspath(__file__)), savedModelFile])

    # We are always looking for the file to predict values for
    if analysisFile in files:
        files.remove(analysisFile)
    questions = [
        inquirer.List('predictFile', message="File to try to predict the values.", choices=files),
    ]
    answers = inquirer.prompt(questions)
    predictFile = answers["predictFile"]
    outputs["predictFile"] = path_join(*[locationPath, predictFile])

    return outputs


def correctData(df):
    df.drop(columns=df.columns[0], axis=1, inplace=True)

    # report the output values. This can be used as a prediction
    # value or a training data outcome
    output = df["winner"]

    # Drop the output from the Dataframe, leaving the only data left as
    # the dataset to train.
    df.drop(labels=["winner"], axis=1,inplace=True)
    df.drop(labels=[
            "teamId",
            "teamName", 
            "triCode", 
            # "attackStrength", 
            # "defenseStrength", 
            "faceOffWinPercentage",
            "shortHandedSavePercentage",
            "gameId",
            "numPlayers"
        ], 
        axis=1, 
        inplace=True
    )
    df.fillna(0, inplace=True)

    return df, output


# Ask for all user input
outputs = inquireFiles()

model = None
if "analysisFile" in outputs:
    analysisFile = outputs["analysisFile"]
    trainDF = pd.read_excel(analysisFile)
    trainDF, trainOutput = correctData(trainDF)

    numObservations, numLabels = trainDF.shape

    model = Sequential()
    # Create a model for a neural network with 3 layers
    # According to a source online, ReLU activation function is best for layers 
    # except the output layer, that layer should use Sigmoid. This is the case for
    # performance reasons.
    model.add(Dense(32, input_shape=(numLabels,), activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(4, activation='relu'))

    # Looking for a single value 0 or 1 for the output
    model.add(Dense(1, activation='sigmoid'))

    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    dfTensor = tf.convert_to_tensor(trainDF.to_numpy())
    outputTensor = tf.convert_to_tensor(trainOutput.to_numpy())

    model.fit(dfTensor, outputTensor, epochs=250, batch_size=10)
    _, accuracy = model.evaluate(dfTensor,  outputTensor)

    questions = [
        inquirer.List('saveModel', message="Would you like to save the model?", choices=["yes", "no"]),
    ]
    answers = inquirer.prompt(questions)
    if answers["saveModel"] == "yes":
        questions = [
            inquirer.Text('modelName', message="What would you like to name the model?", default="nhl_model"),
        ]
        answers = inquirer.prompt(questions)
        model.save(path_join(*[dirname(abspath(__file__)), answers["modelName"]]))

elif "savedModelFile" in outputs:
    model = tf.keras.models.load_model(outputs["savedModelFile"])

if model is None:
    print("model creation/load failed.")
    exit(1)

# the file to compare predicted vs actual data to will always be present
# the model has been loaded/created 
predictFile = outputs["predictFile"]
predictDF = pd.read_excel(predictFile)
predictDF, actualOutput = correctData(predictDF)

predicted = model.predict(predictDF)
predictedOutcomes = [int(round(x[0], 2)) for x in predicted]
actualOutput = [int(x) for x in actualOutput]

assert len(actualOutput) == len(predictedOutcomes)

diffValues = [int(abs(actualOutput[i] - predictedOutcomes[i])) for i in range(len(actualOutput))]
totalDiffs = int(sum(diffValues))
correct = int(len(actualOutput) - totalDiffs)
accuracy = round(100.0 * (float(correct) / float(len(actualOutput))), 2)

print(f"Correct outcomes: {correct} ({accuracy}%)")
print(f"Incorrect outcomes: {totalDiffs} ({round(100 - accuracy, 2)}%)")

