<h1>NHL Model</h1>
<h1 align="center">

![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black) [![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/barbacbd/NHLModel/actions)

[![Build](https://github.com/barbacbd/NHLModel/actions/workflows/python-app.yml/badge.svg)](https://github.com/barbacbd/NHLModel/actions/workflows/python-app.yml)
[![Pylint](https://github.com/barbacbd/NHLModel/actions/workflows/pylint.yml/badge.svg)](https://github.com/barbacbd/NHLModel/actions/workflows/pylint.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/barbacbd/NHLModel/main)](https://github.com/barbacbd/NHLModel/commit/) ![Code Coverage](https://raw.githubusercontent.com/barbacbd/NHLModel/main/.cov/coverage-badge.svg)
</h1>

# Table of Contents

  * [Artificial Neural Network](#artificial-neural-network)
    * [Saved Data](#saved-data)
    * [Generating Datasets](#generating-datasets)
    * [Training](#training)
      * [Layers](#layers)
    * [Compare Functions](#compare-functions)
      * [Direct](#direct)
      * [Averages](#averages)
    * [Feature Selection](#feature-selection)
      * [MRMR](#mrmr-feature-selection)
      * [F1 Scores](#f1-scores)
    * [Predicting Future Games](#predicting-future-games)
    * [Predicting Past Games](#predicting-past-games)
    * [Analyzing](#analyzing)
  * [Poisson Distribution](#nhl-score-prediction---poisson-distribution)
    * [Poisson Requirements](#requirements)
    * [Law of Averages](#law-of-averages)
    * [Limitations](#limitations)
    * [Predicting Scores](#predicting-scores)
    * [Cumulative Distribution Function](#cumulative-distribution-function-cdf)
    * [Probability Distribution Function](#probability-density-function-pdf)
    * [Functionality](#functionality)
    * [Game Example](#example-of-theoretical-game)
    * [Predicting Scores](#predicting-the-scores-for-a-season)
    * [Season Prediction Example](#example-of-season-prediction)

## Artificial Neural Network

The artificial neural network is used to create a model for predicting the outcomes of future NHL games based on previous games. 

### Saved Data

All data generated while using the executable is saved in `/tmp/nhl_model`. 

### Generating Datasets

Generating the datasets is very important as these are the input variables for the model. No matter your choice of `old` vs `new`, the same data will be generated. The `old` method is deprecated, and requires that the user has used the `old` version of the NHL api to locally pull the data to their machine. The `new` method will create the dataset using the `new` version of the NHL api. 

_Recommended_: If the user would like to update the data for the current year before evaluating a model, select the `execType` of `generate` and use the current year as the start and end year parameters. 

### Training

The user will be asked to input the `batch size` and number of `epochs` to train a model. These values can be looked up online, and these are up to the users judgement. 

**Note**: _It is important not to over train a model, so use caution when altering these input parameters_. 

#### Layers

The package will select the number of layers by using the square root method. The initial layer will contain at least 16 output variables (the larger the number of input variables the larger this layer will be). Each subsequent layer will have square root of the number of outputs as the layer before it. The final layer will contain only one output as we are looking for Winner/Loser (0 or 1).

The first layer uses the activation type of `relu` while all other layers utilize the activation type of `sigmoid`.

### Compare Functions

There are two methods for evaluating data that will be used to estimate an outcome of each game. The two methods are called
`DIRECT` and `AVERAGES`.

#### DIRECT

A `DIRECT` comparison will use the data from all head to head matches between the two teams in question. For instance, if the St. Louis Blues
are playing the Chicago Blackhawks, and we want to predict the winner, the data from their previous games this season will be averaged together
to estimate all of the model input parameters. It is important to note that the two teams MUST have played at least 1 game where the current home team
and away team were also playing as home and away in a previous game between these two teams. If the previous games look like:

| HOME TEAM | HOME TEAM SCORE | AWAY TEAM | AWAY TEAM SCORE |
| --------- | --------------- | --------- | --------------- |
| CHICAGO BLACKHAWKS | 3 | ST. LOUIS BLUES | 2 |
| CHICAGO BLACKHAWKS | 3 | ST. LOUIS BLUES | 4 |

The data will not be used to predict 

| HOME TEAM | HOME TEAM SCORE | AWAY TEAM | AWAY TEAM SCORE |
| --------- | --------------- | --------- | --------------- |
| ST. LOUIS BLUES | x | CHICAGO BLACKHAWKS | X |

In the event that no head-to-head data can be found matching the current
circumstances, then the `AVERAGES` method will be used for that game.

#### AVERAGES

The `AVERAGES` comparison will use ALL of the data for a home team and away team and average all of the data together. For instance if we are looking for the field `goals` for the home team CHICAGO BLACKHAWKS:

| HOME TEAM | HOME TEAM SCORE | AWAY TEAM | AWAY TEAM SCORE |
| --------- | --------------- | --------- | --------------- |
| CHICAGO BLACKHAWKS | 3 | ST. LOUIS BLUES | 2 |
| CHICAGO BLACKHAWKS | 3 | NEW YORK ISLANDERS | 4 |
| CHICAGO BLACKHAWKS | 4 | DALLAS STARS | 8 |
| CHICAGO BLACKHAWKS | 6 | DETROIT RED WINGS | 1 |

The average number of goals scored for the home team (the Blackhawks in this case) is 4. The average number of goals scored by the away team when the Blackhawks are the home team is 3.75. These numbers can be plugged into the model when predicting future games. 

**Note**: _The process is carried out for all input variables in the model_.

### Feature Selection

The process of selecting which features are _most_ important to the model is extremely important in the models success rate. Feature selection is also important as it will decrease the possiblity of over training the model; in this case including useless data that may effect the output later.

#### MRMR Feature Selection

Maximum Relevance Minimum Redundancy is a relatively new feature selection algorithm that attempts to eliminate parameters/features that are dependent and provide the least amount of support to the overall goal. 

When the user selects this algorithm, they have a choice to provide the number of features that they would like selected. In this case the `X` relevant features are selected that have the highest scores related to the models success. In the event that the user enters `0`, the number of features selected is based on the number whose scores are above the average value. For instance if the model has 12 parameters and 5 have a MRMR score above average, then those 5 features are selected.

#### F1-Scores

The F1 Scores are evaluated using a Random Forest Classification method. The user must provide a percision score from 0.0 to 1.0. 

Then the iterative process begins and a precision score is output based on the number of variables used for the model evaluation. For instance if the model has 12 parameters/features, a precision score is given for using 1, 2, 3, 4, 5, ... features. A table such as the following may be seen:

| Features | F1-Score |
| -------- | -------- |
| 1 | 1.0 |
| 2 | 1.0 |
| 3 | 0.5 | 
...

In this case if the user selected a precision of 1.0, the model would select 2 features as that is the maximum number of features where the F1-Score was greater than or equal to the supplied value. 

The 2 features with the highest scores would then be chosen and returned. 

### Predicting Future Games

When the user selects the `ann` option for the `execType`, the NHL games (if any) for the current day will be pulled and the outcomes will be predicted using the input data. The outcomes will be printed on the screen:

```
home = New Jersey Devils              away = Chicago Blackhawks             predicted winner = New Jersey Devils             
home = Washington Capitals            away = Carolina Hurricanes            predicted winner = Carolina Hurricanes           
home = Anaheim Ducks                  away = Winnipeg Jets                  predicted winner = Winnipeg Jets   
```

The data will also be saved to a file: `"%Y-%m-%d"-predictions.xlsx`.

### Predicting Past Games

**Note**: _This is not currently available in the package, but was conducted during the package creation as a test_.

The same model that is created through this process can be used to predict games that have already happened. The success rate of past game predictions was between 92.0% and 98.5%. The exact percentage of correctly evaluated games was due to different parameters during model creation.

The work here was abandoned because past games are easy to predict when all of the data is available. Predicting future games requires that the current data be used as a reference for inputs to predict future values. For instance, we may not not know the number of shots taken will be but we can average the number of shots taken and use that as input. 

### Analyzing 

The `predictions.xlsx` file will contain all of the predictions that have been made. Once those games are played, the data from the games can be retrieved and compared against the predictions. The `predictions.xlsx` file will be updated with the values to indicate how the prediction went.

The following shows the data before analyzing the games from 10/14/2023:

| homeTeam | awayTeam | gameDate | datePredicted | predictedWinner | correct | winner |
| -------- | -------- | -------- | ------------- | --------------- | ------- | ------ |
| Ottawa Senators | Philadelphia Flyers |	2023-10-14 | 2024-07-19 |	Ottawa Senators | | |


The following shows the data after analyzing the games from 10/14/2023:

| homeTeam | awayTeam | gameDate | datePredicted | predictedWinner | correct | winner |
| -------- | -------- | -------- | ------------- | --------------- | ------- | ------ |
| Ottawa Senators | Philadelphia Flyers |	2023-10-14 | 2024-07-19 |	Ottawa Senators | TRUE | Senators |

## NHL Score Prediction - Poisson Distribution

Poisson distributions fall under the category of discrete probability distributions. The outcome of the Poisson distribution is the number of times that an event occurs. Poisson distributions can be utilized to predict the number of events occurring within a given time interval.

### Requirements

- Events must happen randomly and independently. The probability of any single event occurring does not and cannot affect the probability of another event occurring. 
- The mean number of events that occur in a given time interval must be known. 

### Law of Averages

The Poisson distribution makes use of the law of averages. The more data points in the analysis, it is more likely that the predicted scores and predicted winners will tend towards the mean. Simply, the more data points, the more likely we can predict the winner. Seems like an obvious observation, but given the only value that the poisson distribution uses is the mean (mu), this may be simpler said than done.

### Limitations

There is no way to account for immediate changes that could have a major impact on any of the statistical values required for the calculation and estimation of the poisson distribution. 

- New Coach
- New Players
  - new injured players
  - player(s) returning from injury
  - trades
- Any human factor such as:
  - Personal connection to other players in your shift
  - Personal issues such as split from spouse
- Time on road vs. time at home

### Predicting Scores

The goal will be to predict the score of a hockey game. There are multiple sides to every hockey game. The home team and away team as well as the number of goals scored and given up given the game location. 

  * Home Team
    * Number of goals scored 
    * Number of goals given up
  * Away Team
    * Number of goals scored
    * Number of goals given up

The ability to predict the score of an NHL game requires a distribution for all four topics above. 

### Cumulative Distribution Function (CDF)

The CDF provides the probability that a random variable will take a value less than or equal to the random variable value. 

### Probability Density Function (PDF)

The PDF provides the probability that a random variable will take on the exact value of the random variable. For the purpose of predicting scores, the PDF or Probability Mass Function (PMF) will be used since the prediction looks at the exact number of goals.

### Functionality

First, find the number of goals that the home team is expected to score. 

  * Estimate the number of goals that the home team will score
    * Calcualte the home team offensive score (1).
      * Get the average number of goals scored by the home team during home games (2).
      * Divide this number by the average number of goals scored in all games (the entire league) during regulation.
    * Calculate the away team defensive score (3).
      * Get the average number of goals given up by the away team during away games.
      * Divide this number by the average number of goals scored in all games (the entire league) during regulation.
    * Multiply the (1), (2), and (3) above.


  * Estimate the number of goals that the away team will score
    * Calcualte the away team offensive score (4).
      * Get the average number of goals scored by the away team during away games (5).
      * Divide this number by the average number of goals scored in all games (the entire league) during regulation.
    * Calculate the home team defensive score (6).
      * Get the average number of goals given up by the home team during home games.
      * Divide this number by the average number of goals scored in all games (the entire league) during regulation.
    * Multiply the (4), (5), and (6) above.


  * Get the max number of goals scored by any team this year (optional).
  * Calculate the PDF/PMF scores for each team.
    * For each value K in 0 - Max Number of goals scored (or any chosen number)
      * Run the poisson.pmf function (homeTeamEstimatedGoals, K)
      * Run the poisson.pmf function (awayTeamEstimatedGoals, K)

  * To calculate the Regulation Tie values, multiply the probabilities together where K matches (for instance 0-0), and add all of the probabilities together for each instance (0-0, 1-1, ... etc).
  * To calculate the Win percentage for a team, multiply the probability of each team scoring their respective goals and add the results together.
    * Note: a win would mean that the value for a team must be greater than the scores of the other team, so most scores can be ignored. 

### Example of theoretical game

The following example analyzes the St. Louis Blues (HOME) against the Boston Bruins (AWAY).

```
               0         1         2         3         4         5        6         7         8         9
Blues   0.088986  0.215282  0.260413  0.210004  0.127014  0.061457  0.02478  0.008564  0.002590  0.000696
Bruins  0.014786  0.062308  0.131287  0.184418  0.194289  0.163750  0.11501  0.069238  0.036472  0.017077

```
The pdf/pmf matrix is output with all runs. The above data presents the probability that the number of goals (columns) will be scored by either team.

```
Blues (HOME) win percentage: 18.21
Bruins (AWAY) win percentage: 68.04
Regulation tie percent: 12.59
Expected Score (HOME) 2 - 4 (AWAY)
```
The snippet above presents the user with the probability that each team will win or if there will be a tie in regulation. The user can also see the predicted score. 


### Predicting the scores for a season

The original study was to find the win percentage for the home and away teams given a hypothetical game. In the original study I proposed a game between the
St. Louis Blues and the Boston Bruins. That does not mean that the Blues and Bruins played or would play. The original study also performed the calculation for
the entire season and then performed the calculations as though the next game in the schedule was between the Blues and Bruins. 

The study/analysis has been adjusted to predict the scores/winners for all games of previous seasons. When no data has been set for the current season (first games home and away for each team), the cumulative data from the previous season is used for the calculations. By performing this data we are minimizing the dependence on the previous season data as there are so many factors that change. 

### Example of season prediction

The following predictions are based off of the same process above. The algorithm uses the previous season for intial games (where seasonal data is missing). All other calculations are based off of the current season values. This is an iterative process, so variables such as max goals scored, home team wins, away team wins, etc. can and will change.

The following numbers are based on the `2022-2023` NHL season.

```
Number of Games: 1312, correctly predicted: 730, percent: 55.64
```

That doesn't seem too impressive for a prediction value. That is true, using the poisson distribution is roughly as useful as flipping a coin to predict the winner. These numbers are consistent from year to year, but what happens when we analyze the data in smaller groups to see if our odds increase over the length of the season?

Let's add some simple data to the end of the `main` to figure this out:

```python
# Look at the predicted vs actual winner every 100 entries
totalGames = {}
for k, v in parsedHomeTeamEvents.items():
    for g in v:
        totalGames[g.gameId] = g


totalGames = dict(sorted(totalGames.items()))

sortedGames = list(totalGames.values())
for i in range(0, len(sortedGames), 100):   
    currAnalysis = sortedGames[i:i+100]

    winsPredicted = 0
    for x in currAnalysis:
        if x.winnerPredicted:
            winsPredicted += 1
    
    print(f"Number of Games: {len(currAnalysis)}, correctly predicted: {winsPredicted}, percent: {round(float(winsPredicted)/float(len(currAnalysis)) *100.0, 2)}")
```

```
Number of Games: 100, correctly predicted: 51, percent: 51.0
Number of Games: 100, correctly predicted: 52, percent: 52.0
Number of Games: 100, correctly predicted: 50, percent: 50.0
Number of Games: 100, correctly predicted: 56, percent: 56.0
Number of Games: 100, correctly predicted: 53, percent: 53.0
Number of Games: 100, correctly predicted: 63, percent: 63.0
Number of Games: 100, correctly predicted: 53, percent: 53.0
Number of Games: 100, correctly predicted: 50, percent: 50.0
Number of Games: 100, correctly predicted: 56, percent: 56.0
Number of Games: 100, correctly predicted: 56, percent: 56.0
Number of Games: 100, correctly predicted: 52, percent: 52.0
Number of Games: 100, correctly predicted: 64, percent: 64.0
Number of Games: 100, correctly predicted: 66, percent: 66.0
Number of Games: 12, correctly predicted: 8, percent: 66.67
```

Looking the data over every 100 games, it seems that we can have a bit more luck predicting games as the season continues. However, this does not hold true for every season. 

Q: _What does this mean?_ <br>
A: The Poisson Distribution may not be the best method for predicting NHL games, but no method is without its flaws. 
