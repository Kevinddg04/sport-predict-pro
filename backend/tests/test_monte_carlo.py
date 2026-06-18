"""Tests unitarios — Monte Carlo Simulator"""
import numpy as np
import pytest
from ml.monte_carlo import MonteCarloSimulator


@pytest.fixture
def simulator():
    return MonteCarloSimulator(n_simulations=1000, seed=42)


class TestMonteCarloSimulator:

    def test_probabilities_sum_to_one(self, simulator):
        result = simulator.simulate(lambda_home=1.5, lambda_away=1.2)
        total = result["home_win_pct"] + result["draw_pct"] + result["away_win_pct"]
        assert abs(total - 1.0) < 0.01, f"Probs suman {total}, deberían ser ~1.0"

    def test_over_under_complement(self, simulator):
        result = simulator.simulate(1.5, 1.2)
        assert abs(result["over_2_5_pct"] + result["under_2_5_pct"] - 1.0) < 0.01

    def test_home_advantage_reflected(self, simulator):
        """Con lambda_home >> lambda_away, local debe ganar más."""
        result = simulator.simulate(lambda_home=3.0, lambda_away=0.5)
        assert result["home_win_pct"] > 0.70, "Con lambda_home=3.0, local debería ganar >70%"

    def test_equal_teams_near_symmetric(self, simulator):
        """Con lambdas iguales, home y away deben ser similares."""
        result = simulator.simulate(lambda_home=1.4, lambda_away=1.4, n=5000)
        diff = abs(result["home_win_pct"] - result["away_win_pct"])
        assert diff < 0.10, f"Con equipos iguales, diferencia es {diff:.2f}"

    def test_most_likely_scores_ordered(self, simulator):
        result = simulator.simulate(1.5, 1.2)
        scores = result["most_likely_scores"]
        assert len(scores) > 0
        # Verificar que están ordenados por probabilidad (mayor primero)
        probs = [s["probability"] for s in scores]
        assert probs == sorted(probs, reverse=True)

    def test_n_simulations_respected(self, simulator):
        result = simulator.simulate(1.5, 1.2, n=500)
        assert result["n_simulations"] == 500

    def test_high_lambda_over_2_5(self, simulator):
        """Con muchos goles esperados, Over 2.5 debe ser muy probable."""
        result = simulator.simulate(lambda_home=2.5, lambda_away=2.5)
        assert result["over_2_5_pct"] > 0.80

    def test_low_lambda_under_2_5(self, simulator):
        """Con pocos goles esperados, Under 2.5 debe ser muy probable."""
        result = simulator.simulate(lambda_home=0.6, lambda_away=0.6)
        assert result["under_2_5_pct"] > 0.60

    def test_btts_with_zero_lambda(self, simulator):
        """Si un equipo tiene lambda=0, BTTS debe ser ~0."""
        result = simulator.simulate(lambda_home=0.01, lambda_away=1.5, n=2000)
        assert result["btts_pct"] < 0.05

    def test_score_distribution_keys(self, simulator):
        result = simulator.simulate(1.5, 1.2)
        dist = result["score_distribution"]
        assert isinstance(dist, dict)
        assert "1-0" in dist or "0-0" in dist or len(dist) > 0
