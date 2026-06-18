"""
SportPredict Pro — Data Collector
Descarga datos históricos de football-data.co.uk
SIN necesidad de API key ni registro.
"""
import os
import requests
import pandas as pd
from io import StringIO
from loguru import logger
from app.config import settings


# Mapeo de ligas a nombres legibles
LEAGUE_NAMES = {
    "E0": "Premier League",
    "E1": "Championship",
    "SP1": "La Liga",
    "SP2": "Segunda División",
    "D1": "Bundesliga",
    "D2": "2. Bundesliga",
    "I1": "Serie A",
    "I2": "Serie B",
    "F1": "Ligue 1",
    "F2": "Ligue 2",
    "B1": "Belgian Pro League",
    "N1": "Eredivisie",
    "P1": "Primeira Liga",
    "T1": "Süper Lig",
    "G1": "Super League Greece",
}

# Columnas que nos interesan y su mapeo
COLUMN_MAP = {
    "Div": "league",
    "Date": "date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HC": "home_corners",
    "AC": "away_corners",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HY": "home_yellow",
    "AY": "away_yellow",
    "HR": "home_red",
    "AR": "away_red",
    "B365H": "odd_home",
    "B365D": "odd_draw",
    "B365A": "odd_away",
}


def build_url(season: str, league: str) -> str:
    """
    Construye la URL de descarga de football-data.co.uk.
    Ej: season='2324', league='E0' → URL del CSV de Premier League 23/24.
    """
    return f"https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"


def download_season(season: str, league: str) -> pd.DataFrame | None:
    """Descarga un CSV de una temporada/liga y lo devuelve como DataFrame."""
    url = build_url(season, league)
    logger.info(f"Descargando {LEAGUE_NAMES.get(league, league)} {season}: {url}")

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), encoding="latin-1", on_bad_lines="skip")

        if df.empty:
            logger.warning(f"CSV vacío para {league} {season}")
            return None

        # Mapear columnas disponibles
        available = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
        df = df[list(available.keys())].rename(columns=available)

        # Limpiar fecha
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["date", "home_team", "away_team", "home_goals", "away_goals"])

        # Añadir metadata
        df["season"] = season
        if "league" not in df.columns:
            df["league"] = league

        # Tipos numéricos
        for col in ["home_goals", "away_goals"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        logger.success(f"  → {len(df)} partidos descargados")
        return df

    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP {e.response.status_code} para {league} {season} — puede no existir aún")
        return None
    except Exception as e:
        logger.error(f"Error descargando {league} {season}: {e}")
        return None


def download_all(
    leagues: list[str] | None = None,
    seasons: list[str] | None = None,
    save_raw: bool = True,
) -> pd.DataFrame:
    """
    Descarga todos los datos históricos según configuración.

    Args:
        leagues: Lista de códigos de liga (E0, SP1, etc.)
        seasons: Lista de temporadas (2122, 2223, 2324)
        save_raw: Si True, guarda cada CSV en data/raw/

    Returns:
        DataFrame consolidado con todos los partidos
    """
    leagues = leagues or settings.leagues_list
    seasons = seasons or settings.seasons_list

    all_dfs = []

    for season in seasons:
        for league in leagues:
            df = download_season(season, league)
            if df is not None and not df.empty:
                if save_raw:
                    raw_path = os.path.join(settings.raw_dir, f"{league}_{season}.csv")
                    df.to_csv(raw_path, index=False)
                    logger.info(f"  Guardado en {raw_path}")
                all_dfs.append(df)

    if not all_dfs:
        logger.error("No se descargaron datos. Verifica conexión o códigos de liga/temporada.")
        return pd.DataFrame()

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)

    # Guardar dataset consolidado
    processed_path = os.path.join(settings.processed_dir, "matches_all.parquet")
    combined.to_parquet(processed_path, index=False)
    logger.success(f"Dataset consolidado: {len(combined)} partidos → {processed_path}")

    return combined


def load_processed_data() -> pd.DataFrame:
    """Carga el dataset procesado desde Parquet (más rápido que CSV)."""
    processed_path = os.path.join(settings.processed_dir, "matches_all.parquet")

    if not os.path.exists(processed_path):
        logger.warning("No hay datos procesados. Ejecuta download_all() primero.")
        return pd.DataFrame()

    df = pd.read_parquet(processed_path)
    logger.info(f"Cargados {len(df)} partidos desde {processed_path}")
    return df


if __name__ == "__main__":
    """Punto de entrada directo: python -m ml.data_collector"""
    logger.info("=== SportPredict Pro — Data Collector ===")
    df = download_all()
    if not df.empty:
        logger.success(f"Total: {len(df)} partidos de {df['league'].nunique()} ligas")
        print(df.head())
