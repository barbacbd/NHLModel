from json import dumps, loads
import os
from os import mkdir
from os.path import exists, join as path_join
from shutil import rmtree


# Assume that the directory is in this same directory as this script
directory = 'nhl_data/'

# Go through the list of files. Make sure that we have all players (these may
# require some corrections, see Corrections.py for more information). Retrieve
# all of the events from each game too; these will be added to the database. 
i = 1

basePath = "schedules"

if exists(basePath):
    rmtree(basePath)
mkdir(basePath)

for root, dirs, files in os.walk(directory):

    splitPath = root.split("/")
    # skip this is the basic root
    if len(splitPath) == 1:
        continue

    # create the new path for the file that will contain the schedules 
    splitPath[0] = basePath
    newPath = path_join(*splitPath)
    if not exists(newPath):
        mkdir(newPath)
    
    # data to be written to a specific seasonal directory
    seasonalData = []

    for file in files:
        fname = os.path.join(root, file)   
        jsonData = None
        with open(fname) as jsonFile:
            jsonData = loads(jsonFile.read())

        if jsonData:

            localGameData = {}

            gameInfo = jsonData["gameData"]
            localGameData = {
                "gameId": gameInfo["game"]["pk"]
            }
            boxScore = jsonData["liveData"]["boxscore"]

            for x in ("away", "home"):
                localGameData.update({
                    f"{x}TeamId": boxScore["teams"][x]["team"]["id"],
                    f"{x}TeamName": boxScore["teams"][x]["team"]["name"],
                    f"{x}TeamTriCode": boxScore["teams"][x]["team"]["triCode"],
                    f"{x}TeamGoalsActual": boxScore["teams"][x]["teamStats"]["teamSkaterStats"]["goals"]
                })
            
            seasonalData.append(localGameData)
    
    splitPath.append("schedule.json")
    newPath = path_join(*splitPath)
    with open(newPath, "w") as jsonFile:
        jsonFile.write(dumps(seasonalData, indent=2))
