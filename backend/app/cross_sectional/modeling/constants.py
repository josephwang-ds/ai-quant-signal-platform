"""Phase 3 cross-sectional modeling constants."""

from __future__ import annotations

from app.cross_sectional.constants import RESEARCH_FACTOR_COLUMNS

MODELING_FEATURE_COLUMNS: tuple[str, ...] = RESEARCH_FACTOR_COLUMNS

MODELING_LABELS: dict[str, int] = {
    "forward_return_5d": 5,
    "forward_return_20d": 20,
}

APPROVED_MODELS: tuple[str, ...] = ("ridge", "lightgbm")

DEFAULT_RIDGE_ALPHAS: tuple[float, ...] = (0.1, 1.0, 10.0, 100.0)

DEFAULT_SPLIT_MODE = "expanding_walk_forward"
DEFAULT_MIN_TRAIN_DATES = 40
DEFAULT_VALIDATION_DATES = 15
DEFAULT_PREDICTION_BLOCK_DATES = 15
DEFAULT_MIN_CROSS_SECTION_SIZE = 8
DEFAULT_RANDOM_SEED = 42
DEFAULT_PREDICTION_PREVIEW_LIMIT = 50
MAX_PREDICTION_PREVIEW_LIMIT = 200

# LightGBM small fixed grid (validation-selected).
DEFAULT_LGBM_GRID: tuple[dict[str, object], ...] = (
    {"num_leaves": 15, "learning_rate": 0.05, "n_estimators": 80, "max_depth": 4},
    {"num_leaves": 31, "learning_rate": 0.05, "n_estimators": 120, "max_depth": 5},
)

FEATURE_VERSION = "cs_features_v1"
MODELING_IMPL_VERSION = "cs_modeling_v1"
PREPROCESSING_VERSION = "cs_preprocess_v1"
