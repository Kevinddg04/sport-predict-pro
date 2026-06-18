"""Router — Simulación Monte Carlo"""
from fastapi import APIRouter, Request, HTTPException
from app.schemas.prediction import SimulationRequest, SimulationResponse
from app.config import settings
from ml.monte_carlo import MonteCarloSimulator
from ml.data_collector import load_processed_data
from ml.feature_engineer import compute_team_strengths

router = APIRouter()

# Singleton del simulador (evita re-crear el RNG)
_simulator = MonteCarloSimulator(n_simulations=settings.monte_carlo_simulations)


@router.post("/", response_model=SimulationResponse, summary="Simulación Monte Carlo")
async def run_simulation(request_data: SimulationRequest, request: Request):
    """
    Simula N partidos usando distribuciones de Poisson para obtener
    probabilidades robustas. Por defecto 10,000 iteraciones.

    Retorna:
    - **1X2**: % victorias local/empate/visitante en las simulaciones
    - **Over/Under 0.5 a 4.5**: Mercados de totales
    - **BTTS**: Ambos anotan %
    - **Marcadores más probables**: Top 10
    - **Distribución completa** de marcadores simulados
    """
    ensemble = request.app.state.ensemble
    if ensemble is None:
        raise HTTPException(status_code=503, detail="Modelos no cargados.")

    df = load_processed_data()
    if df.empty:
        raise HTTPException(status_code=503, detail="No hay datos históricos.")

    if request_data.league:
        df_league = df[df["league"] == request_data.league]
        if df_league.empty:
            df_league = df
    else:
        df_league = df

    # Obtener λ del modelo Poisson
    poisson_model = ensemble.models.get("poisson")
    if poisson_model:
        lambda_home, lambda_away = poisson_model.predict_goals(
            request_data.home_team, request_data.away_team
        )
    else:
        # Fallback: promedios de liga
        lambda_home = df_league["home_goals"].mean()
        lambda_away = df_league["away_goals"].mean()

    # Correr simulación
    sim_result = _simulator.simulate(lambda_home, lambda_away, n=request_data.n_simulations)

    from app.schemas.prediction import ScoreProbability
    most_likely = [ScoreProbability(**s) for s in sim_result["most_likely_scores"]]

    return SimulationResponse(
        home_team=request_data.home_team,
        away_team=request_data.away_team,
        n_simulations=sim_result["n_simulations"],
        home_win_pct=sim_result["home_win_pct"],
        draw_pct=sim_result["draw_pct"],
        away_win_pct=sim_result["away_win_pct"],
        over_2_5_pct=sim_result["over_2_5_pct"],
        under_2_5_pct=sim_result["under_2_5_pct"],
        btts_pct=sim_result["btts_pct"],
        avg_home_goals=sim_result["avg_home_goals"],
        avg_away_goals=sim_result["avg_away_goals"],
        most_likely_scores=most_likely,
        score_distribution=sim_result["score_distribution"],
    )
