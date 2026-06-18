"""
SportPredict Pro — Feature Engineer
Ingeniería de características avanzada para predicción de fútbol.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional


def compute_rolling_form(
    df: pd.DataFrame,
    team: str,
    as_of_date,
    n: int = 5,
    is_home: Optional[bool] = None,
) -> dict:
    """
    Calcula la forma de un equipo en los últimos N partidos.

    Args:
        df: DataFrame con todos los partidos (ordenado por fecha)
        team: Nombre del equipo
        as_of_date: Fecha de corte (solo usar partidos anteriores)
        n: Número de partidos a considerar
        is_home: Si True, solo local; si False, solo visitante; None = todos

    Returns:
        Dict con métricas de forma
    """
    past = df[df["date"] < as_of_date].copy()

    home_matches = past[past["home_team"] == team].copy()
    away_matches = past[past["away_team"] == team].copy()

    if is_home is True:
        matches = home_matches.tail(n)
    elif is_home is False:
        matches = away_matches.tail(n)
    else:
        home_matches["is_home"] = True
        away_matches["is_home"] = False
        combined = pd.concat([home_matches, away_matches]).sort_values("date")
        matches = combined.tail(n)

    if len(matches) == 0:
        return {
            "form_points": 0, "form_goals_scored": 0, "form_goals_conceded": 0,
            "form_wins": 0, "form_draws": 0, "form_losses": 0, "form_n": 0,
        }

    points = 0
    goals_scored = 0
    goals_conceded = 0
    wins = draws = losses = 0

    for _, row in matches.iterrows():
        if row["home_team"] == team:
            gs, gc = row["home_goals"], row["away_goals"]
        else:
            gs, gc = row["away_goals"], row["home_goals"]

        goals_scored += gs
        goals_conceded += gc

        if gs > gc:
            points += 3
            wins += 1
        elif gs == gc:
            points += 1
            draws += 1
        else:
            losses += 1

    n_played = len(matches)
    return {
        "form_points": points / (n_played * 3),  # Normalizado 0-1
        "form_goals_scored": goals_scored / n_played,
        "form_goals_conceded": goals_conceded / n_played,
        "form_wins": wins / n_played,
        "form_draws": draws / n_played,
        "form_losses": losses / n_played,
        "form_n": n_played,
    }


def compute_team_strengths(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula fuerza ofensiva y defensiva relativa a la liga (estilo Dixon-Coles).
    Devuelve DataFrame con columnas: team, attack_strength, defense_strength.
    """
    league_avg_home = df["home_goals"].mean()
    league_avg_away = df["away_goals"].mean()

    teams = set(df["home_team"].unique()) | set(df["away_team"].unique())
    records = []

    for team in teams:
        home = df[df["home_team"] == team]
        away = df[df["away_team"] == team]

        avg_home_scored = home["home_goals"].mean() if len(home) > 0 else league_avg_home
        avg_away_scored = away["away_goals"].mean() if len(away) > 0 else league_avg_away
        avg_home_conceded = home["away_goals"].mean() if len(home) > 0 else league_avg_home
        avg_away_conceded = away["home_goals"].mean() if len(away) > 0 else league_avg_away

        # Fuerza ofensiva = cuánto más/menos anota respecto al promedio de liga
        attack_home = avg_home_scored / league_avg_home if league_avg_home > 0 else 1.0
        attack_away = avg_away_scored / league_avg_away if league_avg_away > 0 else 1.0

        # Fuerza defensiva = cuánto más/menos concede (menor es mejor)
        defense_home = avg_home_conceded / league_avg_away if league_avg_away > 0 else 1.0
        defense_away = avg_away_conceded / league_avg_home if league_avg_home > 0 else 1.0

        records.append({
            "team": team,
            "attack_home": attack_home,
            "attack_away": attack_away,
            "defense_home": defense_home,
            "defense_away": defense_away,
            "attack_strength": (attack_home + attack_away) / 2,
            "defense_strength": (defense_home + defense_away) / 2,
            "avg_home_scored": avg_home_scored,
            "avg_away_scored": avg_away_scored,
            "avg_home_conceded": avg_home_conceded,
            "avg_away_conceded": avg_away_conceded,
            "n_home": len(home),
            "n_away": len(away),
        })

    return pd.DataFrame(records).set_index("team")


def build_feature_matrix(df: pd.DataFrame, n_form: int = 5) -> pd.DataFrame:
    """
    Construye la matriz de features para entrenamiento de modelos ML.
    IMPORTANTE: Usa solo datos PASADOS para evitar data leakage.

    Args:
        df: DataFrame con partidos (ordenado por fecha)
        n_form: Número de partidos para calcular forma

    Returns:
        DataFrame con features + target (result: 0=H, 1=D, 2=A)
    """
    df = df.sort_values("date").reset_index(drop=True)
    logger.info(f"Construyendo features para {len(df)} partidos (n_form={n_form})...")

    all_rows = []

    # Pre-calcular strengths del dataset completo (para referencia de liga)
    strengths = compute_team_strengths(df)

    for idx, row in df.iterrows():
        if idx < 20:  # Necesitamos partidos previos suficientes
            continue

        past_data = df.iloc[:idx]  # Solo datos anteriores al partido actual

        home_form = compute_rolling_form(past_data, row["home_team"], row["date"], n_form)
        away_form = compute_rolling_form(past_data, row["away_team"], row["date"], n_form)
        home_home_form = compute_rolling_form(past_data, row["home_team"], row["date"], n_form, is_home=True)
        away_away_form = compute_rolling_form(past_data, row["away_team"], row["date"], n_form, is_home=False)

        # Calcular strengths solo con datos previos
        home_str = strengths.loc[row["home_team"]] if row["home_team"] in strengths.index else None
        away_str = strengths.loc[row["away_team"]] if row["away_team"] in strengths.index else None

        feature = {
            # Identificadores
            "match_id": idx,
            "date": row["date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "league": row["league"],
            "season": row["season"],

            # Forma general (últimos N)
            "home_form_pts": home_form["form_points"],
            "away_form_pts": away_form["form_points"],
            "home_form_gf": home_form["form_goals_scored"],
            "away_form_gf": away_form["form_goals_scored"],
            "home_form_ga": home_form["form_goals_conceded"],
            "away_form_ga": away_form["form_goals_conceded"],

            # Forma como local/visitante
            "home_home_form_pts": home_home_form["form_points"],
            "away_away_form_pts": away_away_form["form_points"],

            # Diferencias de forma
            "form_diff": home_form["form_points"] - away_form["form_points"],
            "gf_diff": home_form["form_goals_scored"] - away_form["form_goals_scored"],
            "ga_diff": home_form["form_goals_conceded"] - away_form["form_goals_conceded"],

            # Fuerza de equipo
            "home_attack": home_str["attack_home"] if home_str is not None else 1.0,
            "away_attack": away_str["attack_away"] if away_str is not None else 1.0,
            "home_defense": home_str["defense_home"] if home_str is not None else 1.0,
            "away_defense": away_str["defense_away"] if away_str is not None else 1.0,
            "attack_diff": (home_str["attack_strength"] if home_str is not None else 1.0) -
                           (away_str["attack_strength"] if away_str is not None else 1.0),
            "defense_diff": (home_str["defense_strength"] if home_str is not None else 1.0) -
                            (away_str["defense_strength"] if away_str is not None else 1.0),

            # Lambda esperado de Poisson (corazón del modelo)
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

            # Target
            "target": 0 if row["result"] == "H" else (1 if row["result"] == "D" else 2),
            "home_goals": row["home_goals"],
            "away_goals": row["away_goals"],
        }

        # Cuotas (si están disponibles) → ventaja informativa
        if "odd_home" in row and pd.notna(row.get("odd_home")):
            feature["implied_home"] = 1 / row["odd_home"]
            feature["implied_draw"] = 1 / row["odd_draw"]
            feature["implied_away"] = 1 / row["odd_away"]
        else:
            feature["implied_home"] = None
            feature["implied_draw"] = None
            feature["implied_away"] = None

        all_rows.append(feature)

    features_df = pd.DataFrame(all_rows)
    logger.success(f"Matriz de features: {features_df.shape}")
    return features_df


def get_feature_columns() -> list[str]:
    """Retorna la lista de columnas usadas como features de entrada al modelo."""
    return [
        "home_form_pts", "away_form_pts",
        "home_form_gf", "away_form_gf",
        "home_form_ga", "away_form_ga",
        "home_home_form_pts", "away_away_form_pts",
        "form_diff", "gf_diff", "ga_diff",
        "home_attack", "away_attack",
        "home_defense", "away_defense",
        "attack_diff", "defense_diff",
        "lambda_home", "lambda_away",
    ]
