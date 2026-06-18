"""Router — Predicciones con Ensemble ML"""
import json
import os
from fastapi import APIRouter, Request, HTTPException
from loguru import logger

from app.config import settings
from app.schemas.prediction import PredictionRequest, PredictionResponse, EvaluationResponse
from ml.feature_engineer import compute_team_strengths
from ml.data_collector import load_processed_data

router = APIRouter()


def _get_features_for_match(home_team: str, away_team: str, df) -> dict:
    """Extrae features para un partido dado el dataset histórico."""
    from ml.feature_engineer import compute_rolling_form, get_feature_columns
    import pandas as pd

    as_of = df["date"].max()
    strengths = compute_team_strengths(df)

    home_form = compute_rolling_form(df, home_team, as_of, n=5)
    away_form = compute_rolling_form(df, away_team, as_of, n=5)
    home_home_form = compute_rolling_form(df, home_team, as_of, n=5, is_home=True)
    away_away_form = compute_rolling_form(df, away_team, as_of, n=5, is_home=False)

    home_str = strengths.loc[home_team] if home_team in strengths.index else None
    away_str = strengths.loc[away_team] if away_team in strengths.index else None

    return {
        "home_form_pts": home_form["form_points"],
        "away_form_pts": away_form["form_points"],
        "home_form_gf": home_form["form_goals_scored"],
        "away_form_gf": away_form["form_goals_scored"],
        "home_form_ga": home_form["form_goals_conceded"],
        "away_form_ga": away_form["form_goals_conceded"],
        "home_home_form_pts": home_home_form["form_points"],
        "away_away_form_pts": away_away_form["form_points"],
        "form_diff": home_form["form_points"] - away_form["form_points"],
        "gf_diff": home_form["form_goals_scored"] - away_form["form_goals_scored"],
        "ga_diff": home_form["form_goals_conceded"] - away_form["form_goals_conceded"],
        "home_attack": home_str["attack_home"] if home_str is not None else 1.0,
        "away_attack": away_str["attack_away"] if away_str is not None else 1.0,
        "home_defense": home_str["defense_home"] if home_str is not None else 1.0,
        "away_defense": away_str["defense_away"] if away_str is not None else 1.0,
        "attack_diff": (home_str["attack_strength"] if home_str is not None else 1.0) -
                       (away_str["attack_strength"] if away_str is not None else 1.0),
        "defense_diff": (home_str["defense_strength"] if home_str is not None else 1.0) -
                        (away_str["defense_strength"] if away_str is not None else 1.0),
        "lambda_home": (
            (home_str["attack_home"] if home_str is not None else 1.0) *
            (away_str["defense_away"] if away_str is not None else 1.0) *
            df["home_goals"].mean()
        ),
        "lambda_away": (
            (away_str["attack_away"] if away_str is not None else 1.0) *
            (home_str["defense_home"] if home_str is not None else 1.0) *
            df["away_goals"].mean()
        ),
    }


@router.post("/", response_model=PredictionResponse, summary="Predecir resultado de partido")
async def predict_match(request_data: PredictionRequest, request: Request):
    """
    Genera una predicción completa para un partido usando el ensemble de modelos.

    Retorna probabilidades de:
    - **1X2**: Victoria local, empate, victoria visitante
    - **Over/Under 2.5**: Mercado de goles totales
    - **BTTS**: Ambos equipos anotan
    - **Marcadores más probables**: Top 5

    El ensemble combina: Poisson + Random Forest + XGBoost + LightGBM
    """
    ensemble = request.app.state.ensemble
    if ensemble is None:
        raise HTTPException(
            status_code=503,
            detail="Modelos no cargados. Ejecuta 'python -m ml.trainer' para entrenar.",
        )

    # Cargar datos históricos para calcular features
    df = load_processed_data()
    if df.empty:
        raise HTTPException(status_code=503, detail="No hay datos históricos disponibles.")

    # Filtrar por liga si se especifica
    if request_data.league:
        df_league = df[df["league"] == request_data.league]
        if df_league.empty:
            df_league = df  # Fallback al dataset completo
    else:
        df_league = df

    # Verificar que los equipos existen
    all_teams = set(df_league["home_team"].unique()) | set(df_league["away_team"].unique())
    if request_data.home_team not in all_teams:
        raise HTTPException(
            status_code=404,
            detail=f"Equipo '{request_data.home_team}' no encontrado. Equipos disponibles: {sorted(all_teams)[:20]}...",
        )
    if request_data.away_team not in all_teams:
        raise HTTPException(
            status_code=404,
            detail=f"Equipo '{request_data.away_team}' no encontrado.",
        )

    # Extraer features
    features = _get_features_for_match(request_data.home_team, request_data.away_team, df_league)

    from ml.feature_engineer import get_feature_columns
    feature_cols = get_feature_columns()

    # Predicción del ensemble
    result = ensemble.predict(
        home_team=request_data.home_team,
        away_team=request_data.away_team,
        features=features,
        feature_cols=feature_cols,
    )

    from app.schemas.prediction import ScoreProbability
    most_likely = [ScoreProbability(**s) for s in result.get("most_likely_scores", [])]

    return PredictionResponse(
        home_team=request_data.home_team,
        away_team=request_data.away_team,
        league=request_data.league or "all",
        home_win=result["home_win"],
        draw=result["draw"],
        away_win=result["away_win"],
        over_2_5=result.get("over_2_5", 0.5),
        under_2_5=result.get("under_2_5", 0.5),
        btts=result.get("btts", 0.5),
        expected_home_goals=result.get("expected_home_goals", 1.5),
        expected_away_goals=result.get("expected_away_goals", 1.2),
        model=result["model"],
        confidence=result["confidence"],
        most_likely_scores=most_likely,
    )


@router.get("/evaluate", response_model=list, summary="Métricas de evaluación de modelos")
async def get_evaluation():
    """Retorna las métricas de evaluación del último entrenamiento."""
    eval_path = os.path.join(settings.models_dir, "evaluation.json")
    if not os.path.exists(eval_path):
        raise HTTPException(
            status_code=404,
            detail="No hay resultados de evaluación. Ejecuta 'python -m ml.trainer' primero.",
        )
    with open(eval_path) as f:
        return json.load(f)
