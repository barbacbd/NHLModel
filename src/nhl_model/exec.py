import argparse
from logging import getLogger, basicConfig
from nhl_model.ann import execAnn, findFiles
from nhl_model.dataset import generateDataset
from nhl_model.poisson import execPoisson


execTypes = {
    # main entry point to create, run, train, or predict
    # using the artificial neural network.
    'ann': execAnn,
    # use the poisson distribution predict the winners and losers
    # of the games based on the same method that sports betting 
    # occurs (generating a distirbution to predict the number of goals
    # that will be scored by each side).
    'poisson': execPoisson,
    # generate the dataset that will be used for the artificial 
    # neural network. 
    'generate': generateDataset
}

def main():
    # Set a logging level for the program
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-log', '--logLevel', 
        default="warning", 
        choices=["warning", "critical", "error", "info", "debug"]
    )
    parser.add_argument(
        '--execType',
        default='ann',
        choices=list(execTypes.keys())
    )

    args = parser.parse_args()
    basicConfig(level=args.logLevel.upper())
    logger = getLogger("nhl_neural_net")

    # execute the correct function from the execTypes dictionary.
    # Follow the imports to see what these functions actually do. 
    if args.execType == 'generate':
        output, validFiles = findFiles()
        generateDataset(
            output['version'],
            output['startYear'],
            output['endYear'],
            validFiles=validFiles
        )
    else:
        execTypes[args.execType]()

if __name__ == '__main__':
    main()