"""
SportPredict Pro — Evaluador de Modelos
Calcula métricas estándar de Machine Learning y ROI teórico.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    brier_score_loss,
    classification_report,
)
from typing import Dict, List, Optional
from loguru import logger


def evaluate_model(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    model_name: str = "model",
    odds: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Evalúa un modelo de predicción de resultados de fútbol.

    Args:
        y_true: Etiquetas reales (0=H, 1=D, 2=A) array de ints
        y_pred_proba: Probabilidades predichas (n, 3)
        model_name: Nombre del modelo para el reporte
        odds: DataFrame con cuotas [odd_home, odd_draw, odd_away] para ROI

    Returns:
        Dict con todas las métricas
    """
    y_pred_class = np.argmax(y_pred_proba, axis=1)

    # ── Accuracy ──
    acc = accuracy_score(y_true, y_pred_class)

    # ── Log Loss (cuanto más bajo mejor, 0 = perfecto) ──
    ll = log_loss(y_true, y_pred_proba, labels=[0, 1, 2])

    # ── Brier Score (para cada clase, luego promedio) ──
    from sklearn.preprocessing import label_binarize
    y_bin = label_binarize(y_true, classes=[0, 1, 2])
    brier = np.mean([
        brier_score_loss(y_bin[:, i], y_pred_proba[:, i])
        for i in range(3)
    ])

    # ── Baseline: siempre predecir local gana ──
    baseline_proba = np.tile([0.45, 0.27, 0.28], (len(y_true), 1))
    baseline_acc = accuracy_score(y_true, np.zeros(len(y_true), dtype=int))
    baseline_ll = log_loss(y_true, baseline_proba, labels=[0, 1, 2])

    # ── Skill Score (mejora respecto a baseline) ──
    skill_score = (ll - baseline_ll) / baseline_ll  # Negativo = mejor

    # ── ROI Teórico (si hay cuotas) ──
    theoretical_roi = None
    if odds is not None and not odds.empty:
        theoretical_roi = compute_theoretical_roi(y_true, y_pred_proba, odds)

    result = {
        "model_name": model_name,
        "n_samples": int(len(y_true)),
        "accuracy": round(float(acc), 4),
        "baseline_accuracy": round(float(baseline_acc), 4),
        "accuracy_lift": round(float(acc - baseline_acc), 4),
        "log_loss": round(float(ll), 4),
        "baseline_log_loss": round(float(baseline_ll), 4),
        "brier_score": round(float(brier), 4),
        "skill_score": round(float(skill_score), 4),
        "theoretical_roi": theoretical_roi,
    }

    # Reporte por clase
    report = classification_report(y_true, y_pred_class, labels=[0, 1, 2],
                                   target_names=["Home Win", "Draw", "Away Win"],
                                   output_dict=True)
    result["per_class"] = {
        k: {m: round(v[m], 4) for m in ["precision", "recall", "f1-score"]}
        for k, v in report.items()
        if k in ["Home Win", "Draw", "Away Win"]
    }

    logger.info(
        f"[{model_name}] Accuracy={acc:.3f} | LogLoss={ll:.3f} | Brier={brier:.3f}"
    )
    return result


def compute_theoretical_roi(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    odds: pd.DataFrame,
    stake: float = 1.0,
    edge_threshold: float = 0.05,
) -> float:
    """
    Calcula el ROI teórico apostando cuando el modelo tiene ventaja sobre las cuotas.

    Estrategia: apostar cuando P_modelo > P_implícita × (1 + edge_threshold)

    Args:
        y_true: Resultados reales
        y_pred_proba: Probabilidades del modelo
        odds: [odd_home, odd_draw, odd_away]
        stake: Monto apostado por partido
        edge_threshold: Mínima ventaja para apostar (ej: 0.05 = 5%)

    Returns:
        ROI como porcentaje
    """
    total_staked = 0.0
    total_profit = 0.0
    bets_placed = 0

    for i, (true_class, pred) in enumerate(zip(y_true, y_pred_proba)):
        row_odds = odds.iloc[i]

        for outcome_idx, odd_col in enumerate(["odd_home", "odd_draw", "odd_away"]):
            if odd_col not in row_odds or pd.isna(row_odds[odd_col]):
                continue

            odd = float(row_odds[odd_col])
            if odd <= 0:
                continue

            implied_prob = 1 / odd
            model_prob = pred[outcome_idx]

            # Solo apostar si el modelo da ventaja
            if model_prob > implied_prob * (1 + edge_threshold):
                total_staked += stake
                bets_placed += 1
                if true_class == outcome_idx:
                    total_profit += (odd - 1) * stake
                else:
                    total_profit -= stake

    if total_staked == 0:
        logger.warning("ROI: no se realizaron apuestas con la estrategia actual")
        return 0.0

    roi = (total_profit / total_staked) * 100
    logger.info(f"ROI Teórico: {roi:.2f}% ({bets_placed} apuestas de {len(y_true)} partidos)")
    return round(float(roi), 2)


def compare_models(results: List[Dict]) -> pd.DataFrame:
    """
    Genera tabla comparativa de modelos para el README.

    Args:
        results: Lista de dicts retornados por evaluate_model()

    Returns:
        DataFrame formateado para mostrar
    """
    rows = []
    for r in results:
        rows.append({
            "Modelo": r["model_name"],
            "Accuracy": f"{r['accuracy']:.1%}",
            "Log Loss": f"{r['log_loss']:.3f}",
            "Brier Score": f"{r['brier_score']:.3f}",
            "ROI Teórico": f"{r['theoretical_roi']:.1f}%" if r.get("theoretical_roi") else "N/A",
            "Muestras": r["n_samples"],
        })
    return pd.DataFrame(rows)
