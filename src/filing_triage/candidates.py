"""Model families to compare, and the preprocessing that must stay inside a fold.

The shipped estimator is deliberately unremarkable, and the project's argument
rests on that: swapping it moves the metric by a rounding error while swapping
the validation scheme moves it by 0.220. A claim like that is worth checking
rather than asserting, which is what this registry is for.

**Every candidate is a Pipeline, and that is a leakage decision.** Two of these
families cannot take a NaN, and the obvious fix -- impute the whole feature frame
once, before splitting -- fits the imputer on data from every fold, so a median
computed partly from the test period leaks into training. It is the same shape as
a TF-IDF fitted over the whole corpus, and it is easy to miss because imputation
does not feel like fitting. A Pipeline fits its steps inside each fold, on that
fold's training rows only, so the leak cannot happen by construction.

`hist_gbdt` needs no imputer at all, because HistGradientBoosting learns a
default direction for missing values from the training split. It is wrapped in a
Pipeline anyway so the candidates differ only in their estimator.
"""

from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 7


def _shipped() -> Pipeline:
    """Gradient-boosted trees. The default until 2026-08-27, kept as a candidate.

    It is the only family here that needs no imputer, because
    HistGradientBoosting learns a direction for missing values from the training
    split. That is a real advantage on these features, several of which are
    missing for a reason -- and it still lost, narrowly, to a forest handed
    median-imputed columns instead.
    """
    return Pipeline([
        ("clf", HistGradientBoostingClassifier(
            max_depth=4, max_iter=200, learning_rate=0.06,
            min_samples_leaf=30, l2_regularization=1.0,
            random_state=RANDOM_STATE,
        )),
    ])


def _logistic() -> Pipeline:
    """A linear baseline, and the question it answers.

    If the gradient-boosted trees cannot beat a regularised linear model on the
    same features, the non-linearity is not buying anything and the extra
    machinery is decoration. Scaled because the features span log dollar volume
    and binary item flags, and an unscaled penalty would fall almost entirely on
    whichever column happens to be largest.
    """
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, C=1.0, random_state=RANDOM_STATE)),
    ])


def _random_forest() -> Pipeline:
    """A different bias-variance trade-off on the same trees.

    Bagged deep trees rather than boosted shallow ones. Included because if the
    two agree, the result is a property of the features; if they diverge, it is a
    property of the fitting procedure, and that is worth knowing before quoting
    either.
    """
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clf", RandomForestClassifier(
            n_estimators=300, max_depth=12, min_samples_leaf=20,
            n_jobs=-1, random_state=RANDOM_STATE,
        )),
    ])


def _stratified_dummy() -> Pipeline:
    """Scores at the base rate by construction. The floor, kept honest.

    Not a serious candidate. It is here because a comparison table with no floor
    invites reading the spread between real models as though it were the whole
    range available, and because an average precision that fails to beat this has
    a bug behind it rather than a modelling problem.
    """
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("clf", DummyClassifier(strategy="stratified", random_state=RANDOM_STATE)),
    ])


CANDIDATES = {
    "hist_gbdt": _shipped,
    "logistic": _logistic,
    "random_forest": _random_forest,
    "stratified_dummy": _stratified_dummy,
}

# Which settings to perturb when asking whether a headline depends on the
# estimator's constants. Per family, because the question is only meaningful in
# that family's own parameter space -- a `learning_rate` sweep says nothing about
# a forest, and leaving the grid pointed at the previous default is how a
# sensitivity study silently stops testing anything.
SENSITIVITY_GRIDS: dict[str, list[dict]] = {
    "hist_gbdt": [
        {}, {"max_depth": 3}, {"max_depth": 6}, {"max_iter": 100},
        {"max_iter": 400}, {"learning_rate": 0.03}, {"learning_rate": 0.12},
        {"min_samples_leaf": 10}, {"min_samples_leaf": 60},
        {"l2_regularization": 0.0}, {"l2_regularization": 5.0},
    ],
    "random_forest": [
        {}, {"n_estimators": 150}, {"n_estimators": 600},
        {"max_depth": 8}, {"max_depth": 20}, {"max_depth": None},
        {"min_samples_leaf": 5}, {"min_samples_leaf": 50},
        {"max_features": "sqrt"}, {"max_features": 0.5},
    ],
    "logistic": [
        {}, {"C": 0.01}, {"C": 0.1}, {"C": 10.0}, {"C": 100.0},
    ],
    "stratified_dummy": [{}],
}


def sensitivity_grid(name: str) -> list[dict]:
    """A deliberately coarse grid around one family's defaults. Never a search."""
    return SENSITIVITY_GRIDS.get(name, [{}])


def build(name: str) -> Pipeline:
    """A fresh, unfitted pipeline. Fresh matters: reusing one across folds would
    carry the previous fold's fitted imputer and estimator into the next."""
    try:
        return CANDIDATES[name]()
    except KeyError:
        raise KeyError(
            f"unknown candidate {name!r}; known: {sorted(CANDIDATES)}"
        ) from None
