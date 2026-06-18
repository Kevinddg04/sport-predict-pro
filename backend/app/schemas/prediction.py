"""Schemas Pydantic — Prediction & Simulation"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class PredictionRequest(BaseModel):
    home_team: str = Field(..., example="Arsenal")
    away_team: str = Field(..., example="Chelsea")
    league: str = Field(default="E0", example="E0")
    season: Optional[str] = Field(default=None, description="Si es None, usa la más reciente")


class ScoreProbability(BaseModel):
    home_goals: int
    away_goals: int
    probability: float


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    league: str

    # Probabilidades 1X2
    home_win: float
    draw: float
    away_win: float

    # Mercados adicionales
    over_2_5: float
    under_2_5: float
    btts: float           # Both Teams To Score

    # λ de Poisson usados
    expected_home_goals: float
    expected_away_goals: float

    # Metadata
    model: str
    confidence: float
    most_likely_scores: List[ScoreProbability]


class SimulationRequest(BaseModel):
    home_team: str = Field(..., example="Real Madrid")
    away_team: str = Field(..., example="Barcelona")
    league: str = Field(default="SP1", example="SP1")
    n_simulations: int = Field(default=10000, ge=1000, le=100000)


class SimulationResponse(BaseModel):
    home_team: str
    away_team: str
    n_simulations: int

    # Resultados de simulación
    home_win_pct: float
    draw_pct: float
    away_win_pct: float
    over_2_5_pct: float
    under_2_5_pct: float
    btts_pct: float

    avg_home_goals: float
    avg_away_goals: float

    most_likely_scores: List[ScoreProbability]
    score_distribution: Dict[str, float]


class EvaluationResponse(BaseModel):
    model_name: str
    accuracy: float
    log_loss: float
    brier_score: float
    n_samples: int
    theoretical_roi: Optional[float] = None
