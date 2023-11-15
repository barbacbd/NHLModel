# Poisson Distribution

Poisson distributions fall under the category of discrete probability distributions. The outcome of the Poisson distribution is the number of times that an event occurs. Poisson distributions can be utilized to predict the number of events occurring within a given time interval.

# Requirements

- Events must happen randomly and independently. The probability of any single event occurring does not and cannot affect the probability of another event occurring. 
- The mean number of events that occur in a given time interval must be known. 

# Law of Averages

The Poisson distribution makes use of the law of averages. The more data points in the analysis, it is more likely that the predicted scores and predicted winners will tend towards the mean. Simply, the more data points, the more likely we can predict the winner. Seems like an obvious observation, but given the only value that the poisson distribution uses is the mean (mu), this may be simpler said than done.

# Limitations

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

# Predicting Scores

The goal will be to predict the score of a hockey game. There are multiple sides to every hockey game. The home team and away team as well as the number of goals scored and given up given the game location. 

  * Home Team
    * Number of goals scored 
    * Number of goals given up
  * Away Team
    * Number of goals scored
    * Number of goals given up

The ability to predict the score of an NHL game requires a distribution for all four topics above. 

# Cumulative Distribution Function (CDF)

The CDF provides the probability that a random variable will take a value less than or equal to the random variable value. 

# Probability Density Function (PDF)

The PDF provides the probability that a random variable will take on the exact value of the random variable. For the purpose of predicting scores, the PDF or Probability Mass Function (PMF) will be used since the prediction looks at the exact number of goals.

# Functionality

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

# Example of theoretical game

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


# Predicting the scores for a season

The original study was to find the win percentage for the home and away teams given a hypothetical game. In the original study I proposed a game between the
St. Louis Blues and the Boston Bruins. That does not mean that the Blues and Bruins played or would play. The original study also performed the calculation for
the entire season and then performed the calculations as though the next game in the schedule was between the Blues and Bruins. 

The study/analysis has been adjusted to predict the scores/winners for all games of previous seasons. When no data has been set for the current season (first games home and away for each team), the cumulative data from the previous season is used for the calculations. By performing this data we are minimizing the dependence on the previous season data as there are so many factors that change. 

# Example of season prediction

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