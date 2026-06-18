"""
Tests unitarios — API FastAPI
Usa TestClient de Starlette para tests de integración.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app


@pytest.fixture
def client():
    """Cliente de test con modelos mockeados."""
    with patch("ml.trainer.load_ensemble") as mock_load:
        mock_ensemble = MagicMock()
        mock_load.return_value = mock_ensemble
        app.state.ensemble = mock_ensemble
        with TestClient(app) as c:
            yield c


class TestHealthCheck:
    def test_health_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "docs" in data


class TestMatchesRouter:
    def test_get_leagues_empty_db(self, client):
        """Test con DB vacía (aún no hay datos cargados)."""
        response = client.get("/matches/leagues")
        assert response.status_code == 200

    def test_get_seasons_empty_db(self, client):
        response = client.get("/matches/seasons")
        assert response.status_code == 200

    def test_get_matches_with_filters(self, client):
        response = client.get("/matches/?league=E0&limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPredictRouter:
    def test_predict_no_model(self, client):
        app.state.ensemble = None  # Simular modelos no cargados
        response = client.post(
            "/predict/",
            json={"home_team": "Arsenal", "away_team": "Chelsea", "league": "E0"},
        )
        assert response.status_code == 503  # Service Unavailable

    def test_predict_invalid_team(self, client):
        with patch("app.routers.predictions.load_processed_data") as mock_df:
            import pandas as pd
            mock_df.return_value = pd.DataFrame(
                {"home_team": ["Arsenal"], "away_team": ["Chelsea"],
                 "home_goals": [1], "away_goals": [0], "league": ["E0"],
                 "date": pd.to_datetime(["2024-01-01"])}
            )
            response = client.post(
                "/predict/",
                json={"home_team": "FakeTeam99", "away_team": "Chelsea", "league": "E0"},
            )
            assert response.status_code == 404
