from mrmr import mrmr_classif
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier


def findFeaturesMRMR(dataset, outputs, K=None, **kwargs):
    """Select K features using the MRMR (Maximum Relevance Minimum Redundancy) algorithm.

    MRMR selects features that are highly relevant to the target while being minimally
    redundant with already selected features.

    Args:
        dataset: Pandas DataFrame containing feature columns (should NOT include output)
        outputs: Target/output column from the original dataset
        K: Number of features to select. If None or <= 0, automatically determines K
           by selecting features with above-average relevance scores
        **kwargs: Additional arguments (unused, for compatibility)

    Returns:
        List of selected feature names, or None if invalid K provided
    """
    _k = K
    if _k is None or _k <= 0:
        _k = dataset.shape[1]

        if 0 >= _k > dataset.shape[1]:
            return None

    selected_features, relevance, _ = mrmr_classif(X=dataset, y=outputs, K=_k, return_scores=True)

    if K is not None and K > 0:
        return selected_features

    # Find the number of values where the relevance is above the mean. These are NOT
    # the values that we will return. Instead, use this number as K
    r = relevance.to_frame(name="relevance")
    m = r['relevance'].mean()
    r.sort_values(by=['relevance'], ascending=False, inplace=True)
    _k = len(r[r.relevance > m].index.tolist())

    return selected_features[:_k]


def findFeaturesF1Scores(dataset, outputs, precision=1.0, **kwargs):
    """Find optimal features using Random Forest and F1 scores.

    Uses iterative feature elimination with Random Forest classifier to determine
    the minimum set of features needed to achieve the target F1 score.

    Args:
        dataset: Pandas DataFrame containing feature columns (should NOT include output)
        outputs: Target/output column from the original dataset
        precision: Target F1 score threshold (0.0 to 1.0). The algorithm finds the
                  minimum number of features needed to achieve this score
        **kwargs: Additional arguments (unused, for compatibility)

    Returns:
        List of selected feature names that achieve the target precision
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
        f1 = f1_score(outputs, y_pred, average='micro')
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
