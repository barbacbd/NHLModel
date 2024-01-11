import argparse
from datetime import datetime
from logging import getLogger, basicConfig
from nhl_model.ann import execAnn, findFiles
from nhl_model.dataset import generateDataset
from nhl_model.poisson import execPoisson


def main():
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

    # Generate a dataset used for the artificial neural network. The training data for the ANN should                                                                                                                                         
    # contain a start and end year that are different than the current year/season. This will                                                                                                                                                 
    # provide a good training dataset. When creating a dataset for prediction, set the end and start                                                                                                                                          
    # year to the current season (ex. 2022-2023 season use 2022).                                                                                                                                                                             
    generateSubParser = mainSubParsers.add_parser('generate', help='Generate Dataset')
    generateSubParser.add_argument(
        '-e', '--endYear', help='Season year where the dataset should end', default=datetime.now().year
    )
    generateSubParser.add_argument(
        '-s', '--startYear', help='Season year where the dataset should begin', default=datetime.now().year
    )
    generateSubParser.add_argument(
        '-v', '--version', help='Version of the api where data will be pulled', default='new', choices=['old', 'new'],
    )

    # Poisson distribution is used to predict the winner of a specific game based on the                                                                                                                                                      
    # number of goals that each team will likely score during the game. This method uses                                                                                                                                                      
    # the poisson distribution to predict the values and provide an output.                                                                                                                                                                   
    poissonSubParser = mainSubParsers.add_parser('poisson', help='Poisson Distribution')
    poissonSubParser.add_argument('-y', '--year', help='Year for the start of the season', default=datetime.now().year)

    args = parser.parse_args()

    # set the logger
    basicConfig(level=args.logLevel.upper())
    logger = getLogger("nhl_neural_net")

    # execute the correct function from the execTypes dictionary.
    # Follow the imports to see what these functions actually do. 
    if args.execType == 'generate':
        validFiles = findFiles(args.version, args.startYear, args.endYear)
        generateDataset(args.version, args.startYear, args.endYear, validFiles=validFiles)
    elif args.execType == 'ann':
        execAnn(args.override)
    elif args.execTpe == 'poisson':
        execPoisson(args.year)

if __name__ == '__main__':
    main()