"""
SportPredict Pro — Modelos de Clasificación (RF, XGBoost, LightGBM)
Envuelve scikit-learn, XGBoost y LightGBM en una interfaz uniforme.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import lightgbm as lgb
from loguru import logger
from typing import Dict, List


class BaseMLModel:
    """Interfaz común para todos los modelos de clasificación."""

    MODEL_NAME = "base"

    def __init__(self):
        self.model = None
        self.feature_cols: List[str] = []
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseMLModel":
        raise NotImplementedError

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Retorna array (n_samples, 3): [P(home_win), P(draw), P(away_win)]"""
        raise NotImplementedError

    def predict_match(self, features: dict) -> Dict[str, float]:
        """Retorna probabilidades de un partido en formato estándar."""
        df = pd.DataFrame([features])[self.feature_cols]
        df = df.fillna(df.mean())
        proba = self.predict_proba(df)[0]
        return {
            "home_win": round(float(proba[0]), 4),
            "draw": round(float(proba[1]), 4),
            "away_win": round(float(proba[2]), 4),
            "model": self.MODEL_NAME,
        }

    def feature_importance(self) -> Dict[str, float]:
        """Retorna importancia de features (si el modelo lo soporta)."""
        if not hasattr(self.model, "feature_importances_"):
            return {}
        return dict(zip(self.feature_cols, self.model.feature_importances_.tolist()))


# ──────────────────────────────────────────────────────────────
# Random Forest
# ──────────────────────────────────────────────────────────────

class RandomForestModel(BaseMLModel):
    MODEL_NAME = "random_forest"

    def __init__(self, n_estimators: int = 200, max_depth: int = 8, random_state: int = 42):
        super().__init__()
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=random_state,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RandomForestModel":
        self.feature_cols = X.columns.tolist()
        X_clean = X.fillna(X.mean())
        self.model.fit(X_clean, y)
        self.is_fitted = True
        logger.info(f"RandomForest entrenado con {X.shape[0]} muestras y {X.shape[1]} features")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = X[self.feature_cols].fillna(0)
        return self.model.predict_proba(X_clean)


# ──────────────────────────────────────────────────────────────
# XGBoost
# ──────────────────────────────────────────────────────────────

class XGBoostModel(BaseMLModel):
    MODEL_NAME = "xgboost"

    def __init__(self, n_estimators: int = 300, max_depth: int = 5, learning_rate: float = 0.05):
        super().__init__()
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            objective="multi:softprob",
            num_class=3,
            n_jobs=-1,
            random_state=42,
        )
        self.label_map = {0: 0, 1: 1, 2: 2}  # H=0, D=1, A=2

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "XGBoostModel":
        self.feature_cols = X.columns.tolist()
        X_clean = X.fillna(X.mean())
        self.model.fit(X_clean, y, verbose=False)
        self.is_fitted = True
        logger.info(f"XGBoost entrenado con {X.shape[0]} muestras")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = X[self.feature_cols].fillna(0)
        return self.model.predict_proba(X_clean)


# ──────────────────────────────────────────────────────────────
# LightGBM
# ──────────────────────────────────────────────────────────────

class LightGBMModel(BaseMLModel):
    MODEL_NAME = "lightgbm"

    def __init__(self, n_estimators: int = 300, max_depth: int = 6, learning_rate: float = 0.05):
        super().__init__()
        self.model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multiclass",
            num_class=3,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42,
            verbose=-1,
        )

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "LightGBMModel":
        self.feature_cols = X.columns.tolist()
        X_clean = X.fillna(X.mean())
        self.model.fit(X_clean, y)
        self.is_fitted = True
        logger.info(f"LightGBM entrenado con {X.shape[0]} muestras")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        X_clean = X[self.feature_cols].fillna(0)
        return self.model.predict_proba(X_clean)
