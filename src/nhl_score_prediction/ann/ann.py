import argparse
import inquirer
from json import dumps, loads
from logging import basicConfig, getLogger
from math import sqrt
from nhl_score_prediction.ann.features import findFeaturesMRMR, findFeaturesF1Scores
from nhl_score_prediction.event import Game
from os import listdir
from os.path import dirname, abspath, join as path_join, exists
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


FEATURE_FILE = path_join(*[dirname(abspath(__file__)), "features.json"])

# Look up dictionary for the type of feature selection algorithms
featureSelectionData = {
    "mRMR": findFeaturesMRMR,
    "F1 Scores": findFeaturesF1Scores,
}

def parseInput():
    """Ask the user for input. This will determine if a new model is created or 
    a new/different one is created.
    """
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
            inquirer.Text('numEpochs', message="How many epochs during training?", default=1000),
            inquirer.Text('batchSize', message="Size of batches?", default=30),
            inquirer.List('analysisFile', message="File used to train the data.", choices=files),
            inquirer.List('featureSelection', message='Feature selection method.', choices=list(featureSelectionData.keys()))
        ]
        answers = inquirer.prompt(questions)
        analysisFile = answers["analysisFile"]

        outputs["analysisFile"] = path_join(*[locationPath, analysisFile])
        outputs["featureSelection"] = answers["featureSelection"]
        outputs["numEpochs"] = int(answers["numEpochs"])
        outputs["batchSize"] = int(answers["batchSize"])

        if answers["featureSelection"] == "mRMR":
            questions = [
                inquirer.Text('K', message="K", default=10)
            ]
            answers = inquirer.prompt(questions)
            outputs["K"] = int(answers["K"])
        elif answers["featureSelection"] == "F1 Scores":
            questions = [
                inquirer.Text('precision', message="precision", default=1.0)
            ]
            answers = inquirer.prompt(questions)
            outputs["precision"] = float(answers["precision"])

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


def correctData(df, droppable=[]):
    """Alter the dataframe to remove categorical data. When item(s) are provided
    via the `droppable` argument, those columns will be removed from the dataframe too.
    """
    df.drop(columns=df.columns[0], axis=1, inplace=True)

    # report the output values. This can be used as a prediction
    # value or a training data outcome
    output = df["winner"]

    labelsToRemove = ["teamId", "teamName", "triCode"] + droppable 

    # Drop the output from the Dataframe, leaving the only data left as
    # the dataset to train.
    df.drop(labels=["winner"], axis=1,inplace=True)
    df.drop(labels=labelsToRemove, axis=1, inplace=True)
    df.fillna(0, inplace=True)

    return df, output


# Set a logging level for the program
parser = argparse.ArgumentParser()
parser.add_argument(
    '-log', '--logLevel', 
    default="warning", 
    choices=["warning", "critical", "error", "info", "debug"]
)
args = parser.parse_args()
basicConfig(level=args.logLevel.upper())
logger = getLogger("nhl_neural_net")

# Ask for all user input
outputs = parseInput()

model = None
if "analysisFile" in outputs:
    logger.debug("creating new model")
    analysisFile = outputs["analysisFile"]
    trainDF = pd.read_excel(analysisFile)

    # filter out the output/winner and a few categorical columns
    trainDF, trainOutput = correctData(trainDF, droppable=[])

    # use the default values for feature selection (when applicable).
    logger.debug(f"feature selection algorithm: {outputs['featureSelection']}")
    features = featureSelectionData[outputs["featureSelection"]](trainDF, trainOutput, **outputs)
    logger.debug(f"selected features: {features}")

    with open(FEATURE_FILE, "w") as jsonFile:
        jsonFile.write(dumps({"features": features}, indent=2))

    # only keep the features that we selected
    trainDF = trainDF[features]
    _, numLabels = trainDF.shape

    model = Sequential()
    # Create a model for a neural network with 3 layers
    # According to a source online, ReLU activation function is best for layers 
    # except the output layer, that layer should use Sigmoid. This is the case for
    # performance reasons.
    level = max([numLabels, 16])
    logger.info(f"Creating first layer = {level}")
    model.add(Dense(level, input_shape=(numLabels,), activation='relu'))    
    while True:
        level = int(sqrt(level))
        if level <= 1:
            # Looking for a single value 0 or 1 for the output
            logger.info(f"Creating final layer = 1")
            model.add(Dense(1, activation='sigmoid'))
            break
        logger.info(f"Creating next layer = {level}")
        model.add(Dense(level, activation='relu'))

    # create the model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    # tensorflow requires data in a specific format. convert this the expected format
    dfTensor = tf.convert_to_tensor(trainDF.to_numpy())
    outputTensor = tf.convert_to_tensor(trainOutput.to_numpy())

    model.fit(dfTensor, outputTensor, epochs=outputs["numEpochs"], batch_size=outputs["batchSize"])
    _, accuracy = model.evaluate(dfTensor,  outputTensor)

    # after creating a new model, ask the user if we should save this.
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
    logger.debug("loading saved model")
    model = tf.keras.models.load_model(outputs["savedModelFile"])

if model is None:
    logger.error("model creation/load failed.")
    exit(1)


if not exists(FEATURE_FILE):
    logger.critical(f"failed to find features file {FEATURE_FILE}")
    exit(1)

features = []
with open(FEATURE_FILE, 'rb') as jsonFile:
    jsonData = loads(jsonFile.read())

    features = jsonData.get("features", [])

if not features:
    logger.critical("failed to access features")
    exit(1)

# the file to compare predicted vs actual data to will always be present
# the model has been loaded/created 
predictFile = outputs["predictFile"]
predictDF = pd.read_excel(predictFile)
predictDF, actualOutput = correctData(predictDF)

# only keep the columns that are the same as the features we selected.
# NOTE: this will fail if the features do not exist in the data set to predict
predictDF = predictDF[features]

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

