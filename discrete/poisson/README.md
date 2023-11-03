# Poisson Distribution

Poisson distributions fall under the category of discrete probability distributions. The outcome of the Poisson distribution is the number of times that an event occurs. Poisson distributions can be utilized to predict the number of events occurring within a given time interval.

# Requirements

- Events must happen randomly and independently. The probability of any single event occurring does not and cannot affect the probability of another event occurring. 
- The mean number of events that occur in a given time interval must be known. 

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

# Example

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