from json import loads
import pandas as pd
from pandas import DataFrame as df


with open("NhlYearlyStatistics.json", "rb") as jsonFile:
    jsonData = loads(jsonFile.read())

frames = {}
for year, data in jsonData.items():
    if year != "null":
        frames[year] = df.from_dict(data, orient="columns")

with pd.ExcelWriter('NhlYearlyStatistics.xlsx') as writer:
    for season, frame in frames.items():
        f = frame.transpose()
        f.to_excel(writer, sheet_name=season)
