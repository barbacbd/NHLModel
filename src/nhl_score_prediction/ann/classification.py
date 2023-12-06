
import pandas as pd
from mrmr import mrmr_classif



trainDF = pd.read_excel("/home/barbacbd/personal/NHLScorePrediction/src/nhl_score_prediction/support/ANNDataset.xlsx")
outputs = pd.Series(trainDF["winner"])
trainDF.drop(labels=["winner"], axis=1, inplace=True)
trainDF.drop(labels=["teamName","triCode",],axis=1,inplace=True)

_, cols = trainDF.shape

for i in range(cols):
    selected_features = mrmr_classif(X=trainDF, y=outputs, K=i+1)
    print(f"Selection of {i+1} features: {selected_features}")
