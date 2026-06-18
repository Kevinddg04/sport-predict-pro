"""
SportPredict Pro — Simulación Monte Carlo
Simula 10,000 partidos para obtener distribuciones probabilísticas robustas.
"""
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple
from loguru import logger


class MonteCarloSimulator:
    """
    Simulador Monte Carlo para predicción de fútbol.

    Estrategia:
    1. Usa los λ (lambda) de Poisson predichos por el modelo
    2. Samplea 10,000 (u N) partidos de distribuciones Poisson independientes
    3. Agrega estadísticas: 1X2, Over/Under, BTTS, distribución de marcadores

    Ventaja vs predicción puntual:
    - Captura la incertidumbre nativa del deporte
    - Permite mercados como "gana y anota el delantero X"
    - Más calibrado que un softmax directo
    """

    def __init__(self, n_simulations: int = 10_000, seed: int = 42):
        self.n_simulations = n_simulations
        self.rng = np.random.default_rng(seed)

    def simulate(
        self,
        lambda_home: float,
        lambda_away: float,
        n: int | None = None,
    ) -> Dict:
        """
        Corre N simulaciones de un partido dado sus lambdas de Poisson.

        Args:
            lambda_home: Goles esperados del equipo local
            lambda_away: Goles esperados del equipo visitante
            n: Número de simulaciones (usa self.n_simulations si None)

        Returns:
            Dict con todas las estadísticas de la simulación
        """
        n = n or self.n_simulations
        logger.info(f"Monte Carlo: {n:,} sims | λ_home={lambda_home:.3f}, λ_away={lambda_away:.3f}")

        # Vectorizado: mucho más rápido que un loop Python
        home_goals_sim = self.rng.poisson(lambda_home, size=n)
        away_goals_sim = self.rng.poisson(lambda_away, size=n)

        total_goals = home_goals_sim + away_goals_sim

        # ── Resultados 1X2 ──
        home_wins = np.sum(home_goals_sim > away_goals_sim)
        draws = np.sum(home_goals_sim == away_goals_sim)
        away_wins = np.sum(home_goals_sim < away_goals_sim)

        # ── Over / Under ──
        over_0_5 = np.sum(total_goals > 0)
        over_1_5 = np.sum(total_goals > 1)
        over_2_5 = np.sum(total_goals > 2)
        over_3_5 = np.sum(total_goals > 3)
        over_4_5 = np.sum(total_goals > 4)

        # ── BTTS ──
        btts = np.sum((home_goals_sim > 0) & (away_goals_sim > 0))

        # ── Distribución de marcadores ──
        score_counts: Dict[str, int] = defaultdict(int)
        for hg, ag in zip(home_goals_sim, away_goals_sim):
            if hg <= 8 and ag <= 8:  # Limitamos para no explotar el dict
                score_counts[f"{int(hg)}-{int(ag)}"] += 1

        # Top 10 marcadores más probables
        top_scores = sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_likely_scores = [
            {
                "home_goals": int(s.split("-")[0]),
                "away_goals": int(s.split("-")[1]),
                "probability": round(c / n, 4),
            }
            for s, c in top_scores
        ]

        # Distribución completa de marcadores (para gráficos)
        score_distribution = {k: round(v / n, 5) for k, v in score_counts.items()}

        results = {
            "n_simulations": n,
            "lambda_home": round(lambda_home, 4),
            "lambda_away": round(lambda_away, 4),

            # Probabilidades 1X2
            "home_win_pct": round(home_wins / n, 4),
            "draw_pct": round(draws / n, 4),
            "away_win_pct": round(away_wins / n, 4),

            # Over/Under
            "over_0_5_pct": round(over_0_5 / n, 4),
            "over_1_5_pct": round(over_1_5 / n, 4),
            "over_2_5_pct": round(over_2_5 / n, 4),
            "over_3_5_pct": round(over_3_5 / n, 4),
            "over_4_5_pct": round(over_4_5 / n, 4),
            "under_2_5_pct": round(1 - over_2_5 / n, 4),

            # BTTS
            "btts_pct": round(btts / n, 4),
            "no_btts_pct": round(1 - btts / n, 4),

            # Estadísticas de goles
            "avg_home_goals": round(float(home_goals_sim.mean()), 3),
            "avg_away_goals": round(float(away_goals_sim.mean()), 3),
            "std_home_goals": round(float(home_goals_sim.std()), 3),
            "std_away_goals": round(float(away_goals_sim.std()), 3),

            # Marcadores
            "most_likely_scores": most_likely_scores,
            "score_distribution": score_distribution,
        }

        logger.success(
            f"Sim. completada: {home_wins/n:.1%} local | {draws/n:.1%} empate | {away_wins/n:.1%} visitante"
        )
        return results

    def simulate_season(
        self,
        fixtures: List[Tuple[str, str]],
        lambda_fn,
        n_per_match: int = 1000,
    ) -> Dict:
        """
        Simula una temporada completa de partidos.

        Args:
            fixtures: Lista de (home_team, away_team)
            lambda_fn: Callable(home, away) → (lambda_home, lambda_away)
            n_per_match: Número de simulaciones por partido

        Returns:
            Dict con clasificación simulada
        """
        team_points: Dict[str, List[float]] = defaultdict(list)

        for home, away in fixtures:
            l_home, l_away = lambda_fn(home, away)
            home_s = self.rng.poisson(l_home, size=n_per_match)
            away_s = self.rng.poisson(l_away, size=n_per_match)

            for i in range(n_per_match):
                if home_s[i] > away_s[i]:
                    team_points[home].append(3)
                    team_points[away].append(0)
                elif home_s[i] == away_s[i]:
                    team_points[home].append(1)
                    team_points[away].append(1)
                else:
                    team_points[home].append(0)
                    team_points[away].append(3)

        standings = {
            team: {
                "avg_points": round(np.mean(pts), 2),
                "std_points": round(np.std(pts), 2),
                "win_title_pct": round(np.mean(np.array(pts) == max(pts)), 4),
            }
            for team, pts in team_points.items()
        }

        return {"standings": standings, "n_simulations": n_per_match}
