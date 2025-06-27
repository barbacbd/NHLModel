import argparse
from datetime import datetime
from logging import getLogger, basicConfig
from nhl_model.ann import execAnn, findFiles, execAnnSpecificDate, determineWinners
from nhl_model.dataset import generateDataset
from nhl_model.playoffs import (
    getPlayoffMetadata,
    prepareResultsForNextRound,
    getTeamInfo,
    printPlayoffSeries
)
from nhl_model.poisson import execPoisson

from nhl_model.standings import getStandings


def main():
    '''main execution point.'''
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-log', '--logLevel', default="warning",
        choices=["warning", "critical", "error", "info", "debug"]
    )

    mainSubParsers = parser.add_subparsers(dest='execType')

    # ANN is the artificial neural network generation/loading. In the event of loading a model
    # the model will be used and MOST of the following parameters are not used. When the model
    # is not loaded (it will be created), and the following parameters are used for training a
    # model that will be used for predicting future game outcomes.
    annSubParser = mainSubParsers.add_parser('ann', help='Artificial Neural Network')
    annSubParser.add_argument(
        '--override', action='store_true', help='override all values in the config'
    )

    # Generate a dataset used for the artificial neural network. The training data for the
    # ANN should contain a start and end year that are different than the current year/season.
    # This will provide a good training dataset. When creating a dataset for prediction, set the
    # end and start year to the current season (ex. 2022-2023 season use 2022).
    generateSubParser = mainSubParsers.add_parser('generate', help='Generate Dataset')
    generateSubParser.add_argument(
        '-e', '--endYear', type=int, help='Season year where the dataset should end', 
        default=datetime.now().year
    )
    generateSubParser.add_argument(
        '-s', '--startYear', type=int, help='Season year where the dataset should begin', 
        default=datetime.now().year
    )
    generateSubParser.add_argument(
        '-v', '--version', help='Version of the api where data will be pulled', 
        default='new', choices=['old', 'new'],
    )
    # This argument is intended to be used to drop the information when the dataset
    # will be predicted rather than used for prediction.
    generateSubParser.add_argument(
        '--drop_score_data', help='When true, drop the scores and winner information.',
        action='store_true'
    )
    generateSubParser.add_argument(
        '--playoffs', help='When true, collect information about the playoffs.',
        action='store_true'
    )

    # Poisson distribution is used to predict the winner of a specific game based on the
    # number of goals that each team will likely score during the game. This method uses
    # the poisson distribution to predict the values and provide an output.
    poissonSubParser = mainSubParsers.add_parser('poisson', help='Poisson Distribution')
    poissonSubParser.add_argument(
        '-y', '--year', help='Year for the start of the season', 
        default=datetime.now().year
    )

    # This form of execution asks for a specific date day-month-year to run the model against.
    # This will NOT [re]generate the model, it will only execute if the model is already
    # present in /tmp/nhl_model/nhl_model
    dateSubParser = mainSubParsers.add_parser(
        'date', help='Predict the outcomes for a specific date'
    )
    dateSubParser.add_argument(
        '-d', '--day', help='Day of the month for prediction', default=datetime.now().day
    )
    dateSubParser.add_argument(
        '-m', '--month', help='Month of the year for prediction', default=datetime.now().month
    )
    dateSubParser.add_argument(
        '-y', '--year', help='Year for prediction', default=datetime.now().year
    )

    mainSubParsers.add_parser(
        'analyze', help='Analyze the output file and set the winner information.'
    )

    # This form of execution will attempt to predict the winner(s) for a specific round
    # of the playoffs.
    playoffSubParser = mainSubParsers.add_parser(
        'playoffs', help='Predict the series winner(s) for NHL playoffs.'
    )
    playoffSubParser.add_argument(
        '-r', '--round', choices=[0, 1, 2, 3, 4], default=0, type=int, 
        help='Round of the playoffs to predict.'
    )
    playoffSubParser.add_argument(
        '-y', '--year', help='Year for the playoff prediction', default=datetime.now().year
    )

    args = parser.parse_args()

    # set the logger
    basicConfig(level=args.logLevel.upper())
    logger = getLogger("nhl_neural_net")

    # execute the correct function from the execTypes dictionary.
    # Follow the imports to see what these functions actually do.
    if args.execType == 'generate':
        validFiles = findFiles(args.version, args.startYear, args.endYear, playoffs=args.playoffs)
        generateDataset(args.version, args.startYear, args.endYear,
            validFiles=validFiles, dropScoreData=args.drop_score_data,
            playoffs=args.playoffs
        )
    elif args.execType == 'analyze':
        determineWinners()
    elif args.execType == 'ann':
        execAnn(args.override)
    elif args.execType == 'poisson':
        execPoisson(args.year)
    elif args.execType == 'date':
        execAnnSpecificDate(args.day, args.month, args.year)
    elif args.execType == 'playoffs':
        # When 0 is selected we will perform our best guess for each round, but only
        # use the first round metadata. We will attempt to pick our winners for each
        # round.
        predictionRound = args.round if args.round > 0 else 1
        metadata = getPlayoffMetadata(args.year, predictionRound)
        output = execAnn(override=False, playoffData=metadata)
        printPlayoffSeries(output, predictionRound)

        if args.round == 0:
            standings = getStandings()
            if not standings:
                return

            teamData = getTeamInfo()
            if teamData is None:
                return

            for r in range(2, 5, 1):
                matchups = prepareResultsForNextRound(teamData, standings, output, r)
                output = execAnn(override=False, playoffData=matchups)
                printPlayoffSeries(output, r)


if __name__ == '__main__':
    main()
