'''
Checks whether the agreeableness trait is cleanly separable
from the OTHER profile fields, using a Decision Tree Classifier.

INTERPRETATION CAVEAT: this script predicts agreeableness bucket FROM the other fields
(checking it is not just accidentally correlated with something else like age or occupation)
This is not a check of whether all 12 personas are generally distinct from each other - 
doesn;t fit a classifier well with only 1 example per persona.

METHOD: Leave one out cross validation. Train on 11 test on 1 repeated 12 times.
The standard practical choice for a sample this small, since a normal train/test split 
would leave almost nothing to test.

CAVEAT: n=12 very small. any accuracy given here is statistically fragile.
'''

import pandas as pd
import ast
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import OneHotEncoder

def _parse_trait_label(value):
    if isinstance(value, dict):
        return value.get("label")
    if isinstance(value, str):
        try:
            return ast.literal_eval(value).get("label")
        except (ValueError, SyntaxError):
            return "unknown"
    return "unknown"

'''
Target: agreeableness bucket - matches high/low split used when sampling.
But cross checks if any other value was accidentally included.
'''
def main():
    df = pd.read_csv("persona_sample_12.csv")
    df["agree_label"] = df["agreeableness"].apply(_parse_trait_label)
    df["agree_bucket"] = df["agree_label"].apply(lambda l: "low" if l in ("very low", "low") else ("high" if l in ("very high", "high") else "OTHER"))
    if (df["agree_bucket"] == "OTHER").any():
        print("WARNING: found agreeableness lables outside high/low - check the sample:")
        print(df[df["agree_bucket"] == "OTHER"][["uuid", "agree_label"]])

    # Features: everything except agreeableness itself.
    feature_cols = ["sex", "age", "marital_status", "education_level", "occupation"]
    for trait in ["openness", "conscientiousness", "extraversion", "neuroticism"]:
        df[f"{trait}_label"] = df[trait].apply(_parse_trait_label)
        feature_cols.append(f"{trait}_label")

    X_raw = df[feature_cols].copy()
    y = df["agree_bucket"]

    # One hot encoding for categorical values as age is the only numeric one in dataset.
    categorical_cols = [c for c in feature_cols if c!= "age"]
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_cat = encoder.fit_transform(X_raw[categorical_cols])
    X = pd.DataFrame(X_cat, columns=encoder.get_feature_names_out(categorical_cols))
    X["age"] = X_raw["age"].values


    # Leave one out cross validation
    loo = LeaveOneOut()
    correct = 0
    predictions = []

    for train_idx, test_idx in loo.split(X):
        clf = DecisionTreeClassifier(max_depth=3, random_state=42)
        clf.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = clf.predict(X.iloc[test_idx])[0]
        actual = y.iloc[test_idx].values[0]
        predictions.append({"uuid": df.iloc[test_idx[0]]["uuid"], "actual": actual, "predicted": pred})
        if pred == actual:
            correct += 1

    accuracy = correct / len(y)
    # Accuracy from always guessing the majority class
    chance_baseline = max(y.value_counts()) / len(y)

    print(f"Leave one out accuracy: {accuracy:.2f} ({correct}/{len(y)})")
    print(f"Chance baseline (always guess majority class): {chance_baseline:.2f}")

    print()

    '''
    Fit 1 final tree on all 12 for interpretability.
    Which fields the tree actually split on - NOT a validated result on its own
    Given it is fit on the full sample it is evaluated on, jsut descriptive.
    '''
    print("Per-persona predictions:")
    for p in predictions:
        marker = "correct" if p["actual"] == p["predicted"] else "WRONG"
        print(f"    {p['uuid'][:8]}...  actual={p['actual']:5s}  predicted={p['predicted']:5s}  [{marker}]")

    print()
    print("Feature importances (descriptive only, fit on all 12):")
    full_clf = DecisionTreeClassifier(max_depth=3, random_state=42)
    full_clf.fit(X, y)
    importances = sorted(zip(X.columns, full_clf.feature_importances_), key=lambda x: -x[1])
    for feature, importance in importances[:10]:
        if importance > 0:
            print(f"    {feature}: {importance:.3f}")


if __name__ == "__main__":
    main()