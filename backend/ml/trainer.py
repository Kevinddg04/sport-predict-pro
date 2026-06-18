"""
SportPredict Pro — Pipeline de Entrenamiento
Orquesta: descarga → features → entrenamiento → evaluación → serialización.
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from loguru import logger
from sklearn.model_selection import TimeSeriesSplit

from app.config import settings
from ml.data_collector import download_all, load_processed_data
from ml.feature_engineer import build_feature_matrix, compute_team_strengths, get_feature_columns
from ml.models.poisson_model import PoissonModel
from ml.models.classifiers import RandomForestModel, XGBoostModel, LightGBMModel
from ml.models.ensemble import EnsembleModel
from ml.evaluator import evaluate_model, compare_models


FEATURE_COLS = get_feature_columns()


def load_or_download_data(force_download: bool = False) -> pd.DataFrame:
    """Carga datos procesados o los descarga si no existen."""
    processed_path = os.path.join(settings.processed_dir, "matches_all.parquet")

    if not os.path.exists(processed_path) or force_download:
        logger.info("Descargando datos históricos...")
        df = download_all()
    else:
        logger.info("Cargando datos procesados desde disco...")
        df = load_processed_data()

    if df.empty:
        raise ValueError("No hay datos disponibles. Verifica la conexión a internet.")

    return df


def train_all(force_download: bool = False, save: bool = True):
    """
    Pipeline completo de entrenamiento.

    1. Descarga/carga datos
    2. Calcula features
    3. Split temporal (80% train / 20% test)
    4. Entrena todos los modelos
    5. Evalúa y compara
    6. Serializa los mejores modelos
    """
    logger.info("=" * 60)
    logger.info("SportPredict Pro — Pipeline de Entrenamiento")
    logger.info("=" * 60)

    # ── 1. Datos ──
    df = load_or_download_data(force_download)
    logger.info(f"Dataset: {len(df)} partidos | {df['league'].nunique()} ligas")

    # ── 2. Features ──
    features_path = os.path.join(settings.processed_dir, "features.parquet")

    if os.path.exists(features_path) and not force_download:
        logger.info("Cargando features precalculados...")
        features_df = pd.read_parquet(features_path)
    else:
        logger.info("Calculando features (esto puede tardar unos minutos)...")
        features_df = build_feature_matrix(df, n_form=5)
        features_df.to_parquet(features_path, index=False)

    # Eliminar filas con NaN en columnas críticas
    features_df = features_df.dropna(subset=FEATURE_COLS + ["target"])
    logger.info(f"Features listas: {features_df.shape}")

    # ── 3. Split temporal (NUNCA aleatorio para series de tiempo) ──
    split_idx = int(len(features_df) * 0.80)
    train_df = features_df.iloc[:split_idx]
    test_df = features_df.iloc[split_idx:]

    X_train = train_df[FEATURE_COLS]
    y_train = train_df["target"]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df["target"]

    logger.info(f"Train: {len(train_df)} | Test: {len(test_df)}")

    # ── 4. Calcular strengths para Poisson ──
    team_strengths = compute_team_strengths(df[df["date"] < test_df["date"].min()])

    # ── 5. Entrenar modelos ──
    evaluation_results = []

    models_to_train = {
        "random_forest": RandomForestModel(),
        "xgboost": XGBoostModel(),
        "lightgbm": LightGBMModel(),
    }

    trained_models = {}
    for name, model in models_to_train.items():
        logger.info(f"Entrenando {name}...")
        model.fit(X_train, y_train)
        trained_models[name] = model

        # Evaluar
        proba = model.predict_proba(X_test)
        result = evaluate_model(y_test.values, proba, model_name=name)
        evaluation_results.append(result)

    # ── 6. Poisson ──
    logger.info("Ajustando modelo Poisson...")
    poisson = PoissonModel()
    poisson.fit(df.iloc[:split_idx], team_strengths)

    # Evaluar Poisson con los partidos del test set
    poisson_probas = []
    for _, row in test_df.iterrows():
        pred = poisson.predict_proba(row["home_team"], row["away_team"])
        poisson_probas.append([pred["home_win"], pred["draw"], pred["away_win"]])

    poisson_result = evaluate_model(
        y_test.values,
        np.array(poisson_probas),
        model_name="poisson",
        odds=test_df[["odd_home", "odd_draw", "odd_away"]] if "odd_home" in test_df.columns else None,
    )
    evaluation_results.append(poisson_result)

    # ── 7. Ensemble ──
    logger.info("Configurando ensemble...")
    ensemble = EnsembleModel()
    ensemble.add_model("poisson", poisson)
    for name, model in trained_models.items():
        ensemble.add_model(name, model)

    ensemble_probas = ensemble.predict_batch(test_df, FEATURE_COLS)
    ensemble_result = evaluate_model(
        y_test.values,
        ensemble_probas,
        model_name="ensemble",
        odds=test_df[["odd_home", "odd_draw", "odd_away"]] if "odd_home" in test_df.columns else None,
    )
    evaluation_results.append(ensemble_result)

    # ── 8. Comparación ──
    comparison = compare_models(evaluation_results)
    logger.info("\n" + comparison.to_string(index=False))

    # ── 9. Guardar modelos ──
    if save:
        logger.info("Serializando modelos...")
        joblib.dump(ensemble, os.path.join(settings.models_dir, "ensemble.pkl"))
        joblib.dump(poisson, os.path.join(settings.models_dir, "poisson.pkl"))
        for name, model in trained_models.items():
            joblib.dump(model, os.path.join(settings.models_dir, f"{name}.pkl"))
        joblib.dump(team_strengths, os.path.join(settings.models_dir, "team_strengths.pkl"))

        # Guardar métricas como JSON
        eval_path = os.path.join(settings.models_dir, "evaluation.json")
        with open(eval_path, "w") as f:
            json.dump(evaluation_results, f, indent=2, default=str)

        logger.success(f"Modelos guardados en {settings.models_dir}")

    logger.success("Pipeline de entrenamiento completado exitosamente ✓")
    return ensemble, evaluation_results


def load_ensemble() -> EnsembleModel:
    """Carga el ensemble serializado desde disco."""
    model_path = os.path.join(settings.models_dir, "ensemble.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No se encontró el modelo en {model_path}. "
            "Ejecuta 'python -m ml.trainer' primero."
        )
    return joblib.load(model_path)


if __name__ == "__main__":
    """Punto de entrada: python -m ml.trainer"""
    train_all(force_download=False, save=True)
