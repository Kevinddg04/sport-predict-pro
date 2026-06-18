"""
SportPredict Pro — Modelo de Regresión de Poisson
El modelo más clásico para predicción de fútbol.
"""
import numpy as np
from scipy.stats import poisson
from typing import Tuple, Dict
from loguru import logger


class PoissonModel:
    """
    Modelo de Regresión de Poisson para predicción de goles.

    Fundamento matemático:
    - Los goles en fútbol siguen aproximadamente una distribución de Poisson
    - λ_home = attack_home × defense_away × avg_home_goals_league
    - λ_away = attack_away × defense_home × avg_away_goals_league
    - P(home=i, away=j) = Poisson(i; λ_home) × Poisson(j; λ_away)
    """

    def __init__(self, max_goals: int = 10):
        self.max_goals = max_goals
        self.league_avg_home: float = 1.49  # Valores por defecto (Premier League)
        self.league_avg_away: float = 1.22
        self.team_params: Dict = {}
        self.is_fitted = False

    def fit(self, df, team_strengths) -> "PoissonModel":
        """
        Ajusta los parámetros del modelo a los datos históricos.

        Args:
            df: DataFrame con partidos históricos
            team_strengths: DataFrame con attack/defense_strength por equipo
        """
        self.league_avg_home = df["home_goals"].mean()
        self.league_avg_away = df["away_goals"].mean()
        self.team_params = team_strengths.to_dict("index")
        self.is_fitted = True
        logger.info(
            f"PoissonModel ajustado: λ_home={self.league_avg_home:.2f}, λ_away={self.league_avg_away:.2f}"
        )
        return self

    def predict_goals(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """
        Predice los goles esperados (λ) para cada equipo.

        Returns:
            (lambda_home, lambda_away) — parámetros de Poisson
        """
        home_params = self.team_params.get(home_team, {"attack_home": 1.0, "defense_home": 1.0})
        away_params = self.team_params.get(away_team, {"attack_away": 1.0, "defense_away": 1.0})

        lambda_home = (
            home_params.get("attack_home", 1.0)
            * away_params.get("defense_away", 1.0)
            * self.league_avg_home
        )
        lambda_away = (
            away_params.get("attack_away", 1.0)
            * home_params.get("defense_home", 1.0)
            * self.league_avg_away
        )

        # Clamp para evitar valores degenerados
        lambda_home = max(0.1, min(lambda_home, 6.0))
        lambda_away = max(0.1, min(lambda_away, 6.0))

        return lambda_home, lambda_away

    def score_matrix(self, lambda_home: float, lambda_away: float) -> np.ndarray:
        """
        Calcula la matriz de probabilidades de marcador.
        Fila i = probabilidad de que home anote i goles.
        Columna j = probabilidad de que away anote j goles.

        Returns:
            matriz (max_goals+1) × (max_goals+1)
        """
        probs = np.outer(
            poisson.pmf(range(self.max_goals + 1), lambda_home),
            poisson.pmf(range(self.max_goals + 1), lambda_away),
        )
        return probs

    def predict_proba(self, home_team: str, away_team: str) -> Dict[str, float]:
        """
        Predicción completa de probabilidades para un partido.

        Returns:
            Dict con home_win, draw, away_win, over_2_5, btts, etc.
        """
        lambda_home, lambda_away = self.predict_goals(home_team, away_team)
        matrix = self.score_matrix(lambda_home, lambda_away)

        home_win = float(np.sum(np.tril(matrix, -1)))
        draw = float(np.sum(np.diag(matrix)))
        away_win = float(np.sum(np.triu(matrix, 1)))

        # Over/Under 2.5
        over_2_5 = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if i + j > 2:
                    over_2_5 += matrix[i, j]

        # BTTS (Both Teams To Score)
        btts = float(1 - matrix[0, :].sum() - matrix[:, 0].sum() + matrix[0, 0])

        # Marcadores más probables
        most_likely = []
        flat_probs = [(i, j, matrix[i, j]) for i in range(6) for j in range(6)]
        flat_probs.sort(key=lambda x: x[2], reverse=True)
        for i, j, p in flat_probs[:5]:
            most_likely.append({"home_goals": i, "away_goals": j, "probability": round(p, 4)})

        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
            "over_2_5": round(over_2_5, 4),
            "under_2_5": round(1 - over_2_5, 4),
            "btts": round(btts, 4),
            "expected_home_goals": round(lambda_home, 3),
            "expected_away_goals": round(lambda_away, 3),
            "most_likely_scores": most_likely,
            "model": "poisson",
        }
