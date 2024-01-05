from datetime import datetime
from enum import Enum
import inquirer
from json import dumps, loads
from logging import getLogger
from math import sqrt
from nhl_model.dataset import pullDatasetNewAPI, BASE_SAVE_DIR
from nhl_model.enums import CompareFunction, Version
from nhl_model.features import (
    findFeaturesMRMR, 
    findFeaturesF1Scores
)
from os import listdir, walk, mkdir
from os.path import dirname, abspath, join as path_join, exists
import pandas as pd
import requests
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from warnings import warn


FEATURE_FILE = path_join(*[BASE_SAVE_DIR, "features.json"])
OLD_DATA_DIR = path_join(*[dirname(abspath(__file__)), "support", "data", "nhl_data"])

logger = getLogger("nhl_neural_net")


# Look up dictionary for the type of feature selection algorithms
FeatureSelectionData = {
    "mRMR": findFeaturesMRMR,
    "F1 Scores": findFeaturesF1Scores,
}


def findFiles():
    """Parse the arguements for the program by reading in the static file that
    contains the basic statistics for all teams and all seasons.
    """

    currentYear = datetime.now().year

    validFiles = []
    output = {}
    questions = [
        inquirer.List('version', message="Select a version of data", choices=[x.value for x in Version]),
        inquirer.Text('startYear', message="Enter the year for the analysis to start.", default=currentYear-1),
        inquirer.Text('endYear', message="Enter the year for the analysis to end.", default=currentYear-1),
    ]
    answers = inquirer.prompt(questions)
    output["version"] = answers["version"]
    startYear = int(answers["startYear"])
    endYear = int(answers["endYear"])

    # correct the data 
    startYear, endYear = min([startYear, endYear]), max([startYear, endYear])

    output.update({
        "version": output["version"],
        "startYear": startYear, 
        "endYear": endYear
    })

    if answers["version"] == Version.OLD.value:
        warn(f"search {OLD_DATA_DIR} for valid files, please select the 'new' version instead")

        # NOTE: if the user wants to use the original version of the API, the
        # data must already exist. The API can no longer be reached. For this particular
        # task, the data is expected to exist in the `directory` location above.
        for root, dirs, files in walk(OLD_DATA_DIR):
            sp = root.split("/")
            try:
                if startYear <= int(sp[len(sp)-1]) <= endYear:
                    validFiles.extend([path_join(root, f) for f in files])
            except:
                pass
    else:
        for year in range(startYear, endYear+1):
            createdFile = pullDatasetNewAPI(year)
            if createdFile is not None:
                validFiles.append(createdFile)

    if not validFiles:
        logger.debug("found no valid files")

    return output, validFiles


def parseAnnArguments():
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
    files = [x for x in listdir(BASE_SAVE_DIR) if x.endswith(".xlsx")]

    savedModelFile = "None"

    if useModel == "yes":
        # the saved file will be in this directory.
        potentialFiles = listdir(BASE_SAVE_DIR)
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
            inquirer.List('featureSelection', message='Feature selection method.', choices=list(FeatureSelectionData.keys()))
        ]
        answers = inquirer.prompt(questions)
        analysisFile = answers["analysisFile"]

        outputs["analysisFile"] = path_join(*[BASE_SAVE_DIR, analysisFile])
        outputs["featureSelection"] = answers["featureSelection"]
        outputs["numEpochs"] = int(answers["numEpochs"])
        outputs["batchSize"] = int(answers["batchSize"])

        if answers["featureSelection"] == "mRMR":
            questions = [
                inquirer.Text('K', message="K", default=10)
            ]
            answers = inquirer.prompt(questions)

            try:
                outputs["K"] = int(answers["K"])
            except TypeError:
                pass
            finally:
                outputs["K"] = outputs.get("K", None)
                if outputs["K"] == 0:
                    outputs["K"] = None

        elif answers["featureSelection"] == "F1 Scores":
            questions = [
                inquirer.Text('precision', message="precision", default=1.0)
            ]
            answers = inquirer.prompt(questions)
            outputs["precision"] = float(answers["precision"])

    else:
        outputs["savedModelFile"] = path_join(*[BASE_SAVE_DIR, savedModelFile])

    # We are always looking for the file to predict values for
    if analysisFile in files:
        files.remove(analysisFile)
    questions = [
        inquirer.List('predictFile', message="File to try to predict the values.", choices=files),
    ]
    answers = inquirer.prompt(questions)
    predictFile = answers["predictFile"]
    outputs["predictFile"] = path_join(*[BASE_SAVE_DIR, predictFile])

    return outputs


def saveModel():
    """Ask the user if they wish to save the model
    """
    questions = [
        inquirer.List('saveModel', message="Would you like to save the model?", choices=["yes", "no"]),
    ]
    answers = inquirer.prompt(questions)
    if answers["saveModel"] == "yes":
        questions = [
            inquirer.Text('modelName', message="What would you like to name the model?", default="nhl_model"),
        ]
        answers = inquirer.prompt(questions)

        return answers['modelName']

    return None


def findTodaysGames():
    """Query the API to find the games that will be played today.
    """
    todaysDate = datetime.now()
    data = f'https://api-web.nhle.com/v1/score/{todaysDate.strftime("%Y-%m-%d")}'

    try:
        todaysGameData = requests.get(data).json()
    except:
        logger.error("failed to retrieve NHL data")
        return None

    if "games" not in todaysGameData or len(todaysGameData["games"]) == 0:
        logger.error(f"no games foud for today {todaysDate}")
        return None

    return todaysGameData


def _getTeamNames():
    """Read the names of teams from the file in support. NHLTeams.json.
    """
    teamsData = path_join(*[dirname(abspath(__file__)), "support", "NHLTeams.json"])
    with open(teamsData, "rb") as jsonFile:
        jsonData = loads(jsonFile.read())
    return jsonData


def _createAverages(df):
    """Given a dataframe that contains the records of all games played during a 
    season, find the average values for each team during their home and away games.

    For instance: if a team has played 3 home games and the number of goals in those
    games are 4, 5, 6 respectively, then the average goals for a home game for this 
    team is 5.
    """
    logger.debug("creating the averages dataframe")
    teamIds = list(set(df["htTeamid"].tolist()))

    # logger.debug(f"Team IDS: {teamIds}")

    data = []
    for teamId in teamIds:
        homeTeamRecords = df.loc[(df['htTeamid']==teamId)]
        homeTeamRecords = homeTeamRecords.mean(axis=0).astype(float)
        homeTeamRecords['htTeamid'] = teamId
        homeTeamRecords['atTeamid'] = 0
        data.append(homeTeamRecords)

        awayTeamRecords = df.loc[(df['atTeamid']==teamId)]
        awayTeamRecords = awayTeamRecords.mean(axis=0).astype(float)
        awayTeamRecords['htTeamid'] = 0
        awayTeamRecords['atTeamid'] = teamId
        data.append(awayTeamRecords)

    # Now we have all of the average data from the current season, use this data to predict the next games 
    averagesDF = pd.DataFrame(data, columns=df.columns)

    if not __debug__:
        logger.debug("creating averages.xlsx")
        averagesDF.to_excel(path_join(*[BASE_SAVE_DIR, "averages.xlsx"]))
    
    return averagesDF


def _createHeadToHead(df):
    """Given a dataframe that contains the records of all games played during a 
    season, find the average values for teams that have played each other. If teams
    have played a home and home then there will be a record where each team is the 
    home and away team.
    """
    def _handleAverages(avgs, homeTeamId, awayTeamId):
        """Helper function to extract the home and away Team average data.
        The data will be combined into a single record and returned.
        """
        hr = avgs.loc[(avgs['htTeamid']==homeTeamId)]
        ar = avgs.loc[(avgs['atTeamid']==awayTeamId)]    

        idx = hr.index[0]
        for col in ar.columns:
            if col.startswith("at"):
                hr.at[idx, col] = ar.iloc[0][col]
        
        return hr


    logger.debug("creating the head to head dataframe")

    averagesDF = _createAverages(df)

    teamIds = list(set(df["htTeamid"].tolist()))

    data = []
    for i in range(len(teamIds)):
        firstTeam = teamIds[i]
        
        for j in range(i, len(teamIds)):
            secondTeam = teamIds[j]

            if firstTeam == secondTeam:
                continue

            homeFirst = df.loc[(df['htTeamid']==firstTeam) & (df['atTeamid']==secondTeam)]
            homeFirst.dropna(inplace=True)
            if not homeFirst.empty:
                homeFirst = homeFirst.mean(axis=0).astype(float)
                homeFirst['htTeamid'] = firstTeam
                homeFirst['atTeamid'] = secondTeam
                data.append(homeFirst)
            else:
                # squeeze/convert the Dataframe to a Series
                data.append(_handleAverages(averagesDF, firstTeam, secondTeam).squeeze(axis=0))

            homeSec = df.loc[(df['htTeamid']==secondTeam) & (df['atTeamid']==firstTeam)]
            homeSec.dropna(inplace=True)
            if not homeSec.empty:
                homeSec = homeSec.mean(axis=0).astype(float)
                homeSec['htTeamid'] = secondTeam
                homeSec['atTeamid'] = firstTeam
                data.append(homeSec)
            else:
                # squeeze/convert the Dataframe to a Series
                data.append(_handleAverages(averagesDF, secondTeam, firstTeam).squeeze(axis=0))

    # Now we have all of the average data from the current season for head to head matches
    h2hDF = pd.DataFrame(data, columns=df.columns)

    if not __debug__:
        logger.debug("creating head_to_head.xlsx")
        h2hDF.to_excel(path_join(*[BASE_SAVE_DIR, "head_to_head.xlsx"]))
    
    return h2hDF


def correctData(df, droppable=[]):
    """Alter the dataframe to remove categorical data. When item(s) are provided
    via the `droppable` argument, those columns will be removed from the dataframe too.
    """
    df.drop(columns=df.columns[0], axis=1, inplace=True)

    # report the output values. This can be used as a prediction
    # value or a training data outcome
    output = df["winner"]

    labelsToRemove = ["atTeamname", "atTricode", "htTeamname", "htTricode"] + droppable 

    # Drop the output from the Dataframe, leaving the only data left as
    # the dataset to train.
    df.drop(labels=["winner"], axis=1,inplace=True)
    df.drop(labels=labelsToRemove, axis=1, inplace=True)
    df.fillna(0, inplace=True)

    return df, output


def createModel(analysisFile, featureSelection, **kwargs):
    """Create the model that will be used for predicting future games. If the user has 
    selected this function then a new model is created. 

    :param analysisFile: Filename of the input to the model. This can be any number of records.
    These records are expected to be created using the functions in `dataset.py`.

    :param featureSelection: Algorithm used for selecting the features used during 
    model training as well as output prediction.

    :kwargs:
    - numEpochs - number of epochs to be run during model training
    - batchSize - batch size input for model training
    - other - please see the feature selection algorithms in `features.py` for more information
    as inputs to the algorithms.
    """
    logger.debug("creating new model")
    trainDF = pd.read_excel(analysisFile)

    # filter out the output/winner and a few categorical columns
    trainDF, trainOutput = correctData(trainDF, droppable=[])

    # use the default values for feature selection (when applicable).
    logger.debug(f"feature selection algorithm: {featureSelection}")
    features = FeatureSelectionData[featureSelection](trainDF, trainOutput, **kwargs)
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
        model.add(Dense(level, activation='sigmoid'))

    # create the model
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    # tensorflow requires data in a specific format. convert this the expected format
    dfTensor = tf.convert_to_tensor(trainDF.to_numpy())
    outputTensor = tf.convert_to_tensor(trainOutput.to_numpy())

    logger.debug("fitting and training model")
    model.fit(dfTensor, outputTensor, epochs=kwargs['numEpochs'], batch_size=kwargs['batchSize'])
    _, accuracy = model.evaluate(dfTensor,  outputTensor)

    # attempt to save the model    
    modelName = saveModel()
    if modelName is not None:
        model.save(path_join(*[BASE_SAVE_DIR, modelName]))

    return model


def prepareDataForPredictions(predictFile, comparisonFunction=CompareFunction.AVERAGES):
    """Prepare the data for predicting the outcomes of the games that will be played today.
    
    :param predictFile: Filename of the all of the data to be used as input for predictions.
    Generally that includes all of the data from the current year, but as long as the data is
    formatted to match that of the input to the model, then this could include data over any
    specified period of time. 

    :param comparisonFunction: Type of function used for comparing data. See the enumeration
    `CompareFunction` above for more information.

    :return: Dataframe containing records for the home and away teams that will play today.
    """
    # the file to compare predicted vs actual data to will always be present
    # the model has been loaded/created 
    predictDF = pd.read_excel(predictFile)
    predictDF, actualOutput = correctData(predictDF)

    todaysGameData = findTodaysGames()
    if not todaysGameData:
        logger.error("failed to find todays game data")
        return None

    if comparisonFunction == CompareFunction.AVERAGES:
        dataPointDF = _createAverages(predictDF)

        futrData = []
        for game in todaysGameData["games"]:
            logger.debug(f"Creating data for today: home = {game['homeTeam']['id']}, away = {game['awayTeam']['id']}")
            htRecord = dataPointDF.loc[(dataPointDF['htTeamid']==game['homeTeam']['id'])]
            atRecord = dataPointDF.loc[(dataPointDF['atTeamid']==game['awayTeam']['id'])]    

            idx = htRecord.index[0]
            for col in atRecord.columns:
                if col.startswith("at"):
                    htRecord.at[idx, col] = atRecord.iloc[0][col]

            futrData.append(htRecord)
        
        return pd.concat(futrData)

    elif comparisonFunction == CompareFunction.DIRECT:
        dataPointDF = _createHeadToHead(predictDF)

        futrData = []
        for game in todaysGameData["games"]:
            logger.debug(f"Creating data for today: home = {game['homeTeam']['id']}, away = {game['awayTeam']['id']}")
            record = dataPointDF.loc[(dataPointDF['htTeamid']==game['homeTeam']['id']) & (dataPointDF['atTeamid']==game['awayTeam']['id'])]
            futrData.append(record)
        
        return pd.concat(futrData)

    else:
        _compareStr = comparisonFunction.value if isinstance(comparisonFunction, Enum) else comparisonFunction
        logger.error(f"failed to find the comparison function {_compareStr}")

    return None


def execAnn():
    if not exists(BASE_SAVE_DIR):
        logger.debug(f"creating base directory {BASE_SAVE_DIR}")
        mkdir(BASE_SAVE_DIR)

    # Ask for all user input
    outputs = parseAnnArguments()

    model = None
    if "analysisFile" in outputs:
        model = createModel(**outputs)
    elif "savedModelFile" in outputs:
        logger.debug("loading saved model")
        model = tf.keras.models.load_model(outputs["savedModelFile"])

    if model is None:
        logger.error("valid model not found")
        return

    if not exists(FEATURE_FILE):
        logger.critical(f"failed to find features file {FEATURE_FILE}")
        return

    features = []
    with open(FEATURE_FILE, 'rb') as jsonFile:
        jsonData = loads(jsonFile.read())

        features = jsonData.get("features", [])

    if not features:
        logger.critical("failed to access features")
        return

    preparedDF = prepareDataForPredictions(
        outputs["predictFile"], 
        comparisonFunction=CompareFunction.DIRECT
        # comparisonFunction=CompareFunction.DIRECT
    )

    if preparedDF is None:
        logger.error("failed to prepare data for predictions")
        return

    if not __debug__:
        logger.debug("creating future.xlsx")
        preparedDF.to_excel(path_join(*[BASE_SAVE_DIR, "future.xlsx"]))


    # ensure that only the selected feature found above are present in the dataframe
    preparedDF = preparedDF[features]

    predicted = model.predict(preparedDF)
    predictedOutcomes = [int(round(x[0], 2)) for x in predicted]

    # extract metadata for comparison
    teams = _getTeamNames()
    todaysGameData = findTodaysGames()

    outputForDF = []
    for index, game in enumerate(todaysGameData["games"]):
        print(index)
        homeTeam = [x["fullName"] for x in teams if x["id"] == game['homeTeam']['id']][0]
        awayTeam = [x["fullName"] for x in teams if x["id"] == game['awayTeam']['id']][0]

        predictedWinner = homeTeam if predictedOutcomes[index] == 1 else awayTeam
        outputForDF.append({
            "home": homeTeam,
            "away": awayTeam,
            "predictedWinner": predictedWinner
        })

        print(f"home = {homeTeam:<30} away = {awayTeam:<30} predicted winner = {predictedWinner:<30}")

    if outputForDF:
        todaysDate = datetime.now()
        filename = f'{todaysDate.strftime("%Y-%m-%d")}-predictions.xlsx'
        filename = path_join(*[BASE_SAVE_DIR, filename])
        pd.DataFrame.from_dict(outputForDF, orient='columns').to_excel(filename)
