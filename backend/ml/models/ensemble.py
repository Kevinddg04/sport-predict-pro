"""
SportPredict Pro — Ensemble de Modelos
Combina Poisson + Random Forest + XGBoost + LightGBM con pesos optimizados.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger


class EnsembleModel:
    """
    Ensemble que combina múltiples modelos mediante weighted average.

    Los pesos se pueden optimizar minimizando el Log Loss en un set de validación,
    o asignar manualmente según el rendimiento histórico de cada modelo.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Args:
            weights: Dict con peso por modelo. Deben sumar ~1.0.
                     Ej: {"poisson": 0.3, "xgboost": 0.4, "lightgbm": 0.3}
        """
        self.models: Dict = {}
        self.weights = weights or {
            "poisson": 0.20,
            "random_forest": 0.20,
            "xgboost": 0.30,
            "lightgbm": 0.30,
        }
        self.poisson_model = None

    def add_model(self, name: str, model) -> "EnsembleModel":
        """Registra un modelo en el ensemble."""
        self.models[name] = model
        if name == "poisson":
            self.poisson_model = model
        logger.info(f"Ensemble: añadido '{name}' (peso={self.weights.get(name, 0):.2f})")
        return self

    def set_weights(self, weights: Dict[str, float]) -> "EnsembleModel":
        """Actualiza los pesos del ensemble."""
        total = sum(weights.values())
        self.weights = {k: v / total for k, v in weights.items()}  # normaliza
        return self

    def predict(
        self,
        home_team: str,
        away_team: str,
        features: Optional[Dict] = None,
        feature_cols: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Genera predicción ensemble para un partido.

        Args:
            home_team: Nombre del equipo local
            away_team: Nombre del equipo visitante
            features: Dict de features para modelos ML
            feature_cols: Lista de columnas de features esperadas

        Returns:
            Dict con probabilidades combinadas
        """
        probas = {}  # name → [p_home, p_draw, p_away]

        # 1. Modelo Poisson
        if "poisson" in self.models and self.weights.get("poisson", 0) > 0:
            try:
                result = self.models["poisson"].predict_proba(home_team, away_team)
                probas["poisson"] = [result["home_win"], result["draw"], result["away_win"]]
                poisson_meta = result  # Guardamos xG y marcadores
            except Exception as e:
                logger.warning(f"Poisson falló: {e}")

        # 2. Modelos ML (necesitan features)
        if features and feature_cols:
            X = pd.DataFrame([features])[feature_cols].fillna(0)
            for name in ["random_forest", "xgboost", "lightgbm"]:
                if name in self.models and self.weights.get(name, 0) > 0:
                    try:
                        proba = self.models[name].predict_proba(X)[0]
                        probas[name] = proba.tolist()
                    except Exception as e:
                        logger.warning(f"{name} falló: {e}")

        if not probas:
            logger.error("Ningún modelo pudo generar predicción")
            return {
                "home_win": 0.45, "draw": 0.27, "away_win": 0.28,
                "model": "fallback", "confidence": 0.0,
            }

        # Weighted average
        active_weights = {k: self.weights.get(k, 0) for k in probas}
        total_w = sum(active_weights.values())
        if total_w == 0:
            total_w = len(probas)
            active_weights = {k: 1 for k in probas}

        combined = np.zeros(3)
        for name, proba in probas.items():
            w = active_weights[name] / total_w
            combined += w * np.array(proba)

        # Normaliza (por si acaso)
        combined = combined / combined.sum()

        # Confianza: inverso de la entropía (más concentrado = más confianza)
        entropy = -np.sum(combined * np.log(combined + 1e-10))
        max_entropy = np.log(3)
        confidence = float(1 - entropy / max_entropy)

        # Obtener metadata de Poisson si está disponible
        poisson_result = (
            self.models["poisson"].predict_proba(home_team, away_team)
            if "poisson" in self.models
            else {}
        )

        return {
            "home_win": round(float(combined[0]), 4),
            "draw": round(float(combined[1]), 4),
            "away_win": round(float(combined[2]), 4),
            "expected_home_goals": poisson_result.get("expected_home_goals", 1.49),
            "expected_away_goals": poisson_result.get("expected_away_goals", 1.22),
            "over_2_5": poisson_result.get("over_2_5", 0.5),
            "under_2_5": poisson_result.get("under_2_5", 0.5),
            "btts": poisson_result.get("btts", 0.5),
            "most_likely_scores": poisson_result.get("most_likely_scores", []),
            "models_used": list(probas.keys()),
            "model": "ensemble",
            "confidence": round(confidence, 4),
        }

    def predict_batch(
        self,
        df: pd.DataFrame,
        feature_cols: List[str],
    ) -> np.ndarray:
        """
        Predicción en lote para evaluación.

        Returns:
            np.ndarray shape (n, 3): probabilidades [home, draw, away]
        """
        all_probas = []

        for name in ["random_forest", "xgboost", "lightgbm"]:
            if name in self.models and self.weights.get(name, 0) > 0:
                X = df[feature_cols].fillna(0)
                proba = self.models[name].predict_proba(X)
                w = self.weights.get(name, 0)
                all_probas.append((proba, w))

        if not all_probas:
            return np.full((len(df), 3), 1 / 3)

        total_w = sum(w for _, w in all_probas)
        combined = sum(p * (w / total_w) for p, w in all_probas)
        return combined
