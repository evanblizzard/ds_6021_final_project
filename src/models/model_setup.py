from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import sklearn.tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_fscore_support
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import OrdinalEncoder

SEED = 6021
ROOT = Path(__file__).resolve().parents[2] # src/models/model_setup.py -> repo root
DATA = ROOT / "data" / "processed"

OUTCOME_NAMES = {1: "died", 2: "passed chamber", 3: "law"}

pd.set_option("display.max_columns", 50)


df = pd.read_csv(DATA / "model_ready_billz.csv")


TARGET = "outcome"

NUM = [
    "n_original_cosponsors", "days_left_in_congress",
    "nominate_dim1", "nominate_dim2", "abs_nominate_dim1",
    "seniority", "vote_share", "delegation_size", "lagged_les",
    "dist_from_median", "n_original_bipartisan", "title_n_words"
]

CAT = ["type", "origin_chamber", "sponsor_party", "policy_area"]

BIN = [
    "commemorative", "sponsor_majority", "freshman", "chair", "subchair",
    "power_cmte", "maj_leader", "min_leader", "state_leg", "lagged_les_missing",
    "leadership_number", "has_cosponsors", "early_intro", "is_bipartisan",
    "t_amend", "t_reauth", "t_approp", "t_extend", "t_establish", "t_prohibit",
    "t_require", "t_repeal", "t_tax", "t_veterans", "t_designate", "t_constitution",
    "t_disapproval", "t_relief", "has_short_title", "title_intro_missing",
    "unified_gov", "sponsor_pres_party", "other_chamber_same_party", "sponsor_trifecta"
]

# identifiers
DROP = [
    "bill_id", "congress", "introduced_date", "title",
    "sponsor_bioguide_id", "sponsor_state", "icpsr", "title_intro",
    "n_short_titles_intro"
]

FEATURES = NUM + CAT + BIN

TRAIN_CONGRESSES = list(range(109, 118))
TEST_CONGRESS = 118

train = df[df['congress'].isin(TRAIN_CONGRESSES)].reset_index(drop=True)
test = df[df['congress'] == TEST_CONGRESS].reset_index(drop=True)

X_train, y_train = train[FEATURES], train[TARGET]
groups_train = train['sponsor_bioguide_id']

X_test, y_test = test[FEATURES], test[TARGET]

N_SPLITS = 5
cv = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
# check that every validation fold has enough of each class (especialy 3 = law)

SCORING = {"f1_macro": "f1_macro", "bal_acc": "balanced_accuracy", "acc": "accuracy"}

results = []

def evaluate(name, model, prep, notes="", n_jobs=None): # clone to give each model it's own copy of the pipeline
    """Cross-valiate prep + model; log mean/std test scores and mean train F1
    n_jobs is None by default because random forest already using n_jobs = -1"""
    pipe = Pipeline([("prep", clone(prep)), ("clf", model)])
    scores = cross_validate( # fit clone on four folds, score on 5th
        pipe, X_train, y_train, groups=groups_train,
        cv=cv, scoring=SCORING, n_jobs=-1,
        return_train_score=True, # -1 runs jobs in parallel across CPU cores
    )
    # scores will be a dict of arrays containing fit time, score time, test_f1, test_bal_acc, and acc

    row = {"model": name, "notes": notes}

    for metric in SCORING:
        s = scores[f"test_{metric}"]
        row[f"{metric}_mean"] = round(s.mean(), 4)
        row[f"{metric}_std"] = round(s.std(), 4)
    row['fit_sec'] = round(scores['fit_time'].mean(), 2)

    results[:] = [r for r in results if r["model"] != name] # results[:] replaces contents of existing global results list in place
    # list comprehension removes any row with same name
    results.append(row)
    return pipe

def show_results(sort_by="f1_macro_mean"):
    # turn list of dicts into dataframe
    return pd.DataFrame(results).sort_values(sort_by, ascending=False).reset_index(drop=True)


prep_tree = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20), CAT),
    ("rest", "passthrough", NUM + BIN)
])

prep_logit = ColumnTransformer(
    [

    ("num", StandardScaler(), NUM),
    # rare policy areas (<20 train bills) pooled into one "infrequent" column
    # categories never seen in training will map there too instead of erroring
    # claude used to figure that out ^
    ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20), CAT),
    ("bin", "passthrough", BIN)
    ],
    remainder="drop",
)

prep_hgb = ColumnTransformer([
    ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                           encoded_missing_value=-1), CAT),
    ("rest", "passthrough", NUM + BIN),
])

from sklearn.model_selection import GridSearchCV

SHORT = {1: "died", 2: "passed", 3: "law"}
CLASSES = np.array(sorted(SHORT))

def ap_law(est, X, y):
    """Scorer: average precision for 'became law' (ranking quality for the rarest class)."""
    proba = est.predict_proba(X)
    return average_precision_score(y == 3, proba[:, list(est.classes_).index(3)])

SCORING = {"f1_macro": "f1_macro", "bal_acc": "balanced_accuracy", "acc": "accuracy", "ap_law": ap_law}