from mrmr import mrmr_classif
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier


def findFeaturesMRMR(dataset, outputs, K=None):
    """Select K features using the MRMR feature selection algorithm.

    :param dataset: Pandas dataframe. The dataframe should NOT include the output column.
    :param outputs: Output column from the original dataset
    :param K: number of features. When None, make a guess at the optimal number of features by 
    using the mean of the relevance scores to find the features.
    """
    _k = K
    if _k is None:
        _k = dataset.shape[1]

        if 0 >= _k > dataset.shape[1]:
            return None

    selected_features, relevance, _ = mrmr_classif(X=dataset, y=outputs, K=_k, return_scores=True)

    if K is not None:
        return selected_features

    # Find the number of values where the relevance is above the mean. These are NOT
    # the values that we will return. Instead, use this number as K
    r = relevance.to_frame(name="relevance")
    m = r['relevance'].mean()
    r.sort_values(by=['relevance'], ascending=False, inplace=True)
    _k = len(r[r.relevance > m].index.tolist())

    return selected_features[:_k]


def findFeaturesF1Scores(dataset, outputs, precision):
    """Attempt to find the optimal features used for training 
    model(s). This is merely an estimation, but the optimal number of features is
    the least amount of features required to meet a F1 Score of `precision`. 

    :param dataset: Pandas dataframe. The dataframe should NOT include the output column.
    :param outputs: Output column from the original dataset
    :param precision: Minimum F1 Score used for calculations. When F1 scores are below this
    value, the optimal number of features has not been achieved.
    """

    # Create a deep copy so that changes are not reflected to the original
    # dataframe.
    df = dataset.copy(True)    

    forest = RandomForestClassifier(n_jobs=1, random_state=42)
    forest.fit(df, outputs)

    f1Scores = []
    feats = []

    while df.shape[1] > 0:
        feature_importances = forest.feature_importances_

        y_pred = forest.predict(df)
        f1 = f1_score(outputs, y_pred)
        f1Scores.append(f1)
        feats.append(df.columns)

        if df.shape[1] == 1:
            break

        least_important_idx = feature_importances.argmin()

        df.drop(df.columns[least_important_idx], axis=1, inplace=True)
        forest.fit(df, outputs)

    # number of features that should be used.
    numFeaturesToUse = 0

    # F1 Values should drop as the number of features is reduced eventually leading 
    # towards 0, reverse this list so that the smallest values are first.
    f1Scores.reverse()

    # get the minimal number of features until we have reached the optimal precision
    for f1s in f1Scores:
        if f1s >= precision:
            break
        numFeaturesToUse += 1

    return feats[-numFeaturesToUse].tolist()


# trainDF = pd.read_excel("/home/barbacbd/personal/NHLScorePrediction/src/nhl_score_prediction/support/ANNDataset-2022-2022.xlsx")
# outputs = pd.Series(trainDF["winner"])
# trainDF.drop(labels=["winner"], axis=1, inplace=True)
# trainDF.drop(labels=["teamName","triCode",],axis=1,inplace=True)
# trainDF.fillna(0, inplace=True)
# _, cols = trainDF.shape
# print(findFeaturesMRMR(trainDF, outputs, K=7))
# print(findFeaturesMRMR(trainDF, outputs))
# print(findFeaturesF1Scores(trainDF, outputs, precision=1.0))