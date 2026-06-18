"""Tests unitarios — Feature Engineer"""
import numpy as np
import pandas as pd
import pytest
from ml.feature_engineer import compute_rolling_form, compute_team_strengths


@pytest.fixture
def sample_matches():
    """Dataset de ejemplo con 20 partidos."""
    np.random.seed(42)
    n = 30
    teams = ["Arsenal", "Chelsea", "Liverpool", "ManCity"]
    rows = []
    for i in range(n):
        home = teams[i % len(teams)]
        away = teams[(i + 1) % len(teams)]
        hg = np.random.poisson(1.5)
        ag = np.random.poisson(1.2)
        result = "H" if hg > ag else ("D" if hg == ag else "A")
        rows.append({
            "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i * 7),
            "home_team": home,
            "away_team": away,
            "home_goals": hg,
            "away_goals": ag,
            "result": result,
            "league": "E0",
            "season": "2324",
        })
    return pd.DataFrame(rows)


class TestRollingForm:

    def test_form_returns_dict(self, sample_matches):
        as_of = pd.Timestamp("2024-06-01")
        form = compute_rolling_form(sample_matches, "Arsenal", as_of, n=5)
        assert isinstance(form, dict)
        assert "form_points" in form
        assert "form_goals_scored" in form

    def test_form_points_range(self, sample_matches):
        as_of = pd.Timestamp("2024-06-01")
        form = compute_rolling_form(sample_matches, "Arsenal", as_of, n=5)
        assert 0.0 <= form["form_points"] <= 1.0

    def test_form_empty_before_first_match(self, sample_matches):
        """Antes del primer partido, la forma debe ser 0."""
        as_of = pd.Timestamp("2020-01-01")
        form = compute_rolling_form(sample_matches, "Arsenal", as_of, n=5)
        assert form["form_n"] == 0

    def test_form_home_only(self, sample_matches):
        as_of = pd.Timestamp("2024-06-01")
        form_home = compute_rolling_form(sample_matches, "Arsenal", as_of, n=5, is_home=True)
        assert form_home["form_n"] <= 5
        assert 0.0 <= form_home["form_points"] <= 1.0


class TestTeamStrengths:

    def test_returns_dataframe(self, sample_matches):
        strengths = compute_team_strengths(sample_matches)
        assert isinstance(strengths, pd.DataFrame)

    def test_all_teams_present(self, sample_matches):
        strengths = compute_team_strengths(sample_matches)
        teams = set(sample_matches["home_team"].unique()) | set(sample_matches["away_team"].unique())
        for team in teams:
            assert team in strengths.index

    def test_attack_strength_positive(self, sample_matches):
        strengths = compute_team_strengths(sample_matches)
        assert (strengths["attack_strength"] > 0).all()

    def test_defense_strength_positive(self, sample_matches):
        strengths = compute_team_strengths(sample_matches)
        assert (strengths["defense_strength"] > 0).all()
