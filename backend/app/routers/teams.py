"""Router — Equipos y estadísticas"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ml.data_collector import load_processed_data
from ml.feature_engineer import compute_team_strengths, compute_rolling_form

router = APIRouter()


@router.get("/", summary="Lista todos los equipos")
def get_teams(league: Optional[str] = Query(None, example="E0")):
    """Retorna lista de equipos con estadísticas de temporada."""
    df = load_processed_data()
    if df.empty:
        raise HTTPException(status_code=503, detail="No hay datos disponibles.")

    if league:
        df = df[df["league"] == league]

    all_teams = sorted(set(df["home_team"].unique()) | set(df["away_team"].unique()))
    return {"teams": all_teams, "total": len(all_teams)}


@router.get("/{team_name}", summary="Estadísticas de un equipo")
def get_team_stats(team_name: str, league: Optional[str] = Query(None)):
    """Retorna estadísticas detalladas de un equipo específico."""
    df = load_processed_data()
    if df.empty:
        raise HTTPException(status_code=503, detail="No hay datos disponibles.")

    if league:
        df = df[df["league"] == league]

    home = df[df["home_team"] == team_name]
    away = df[df["away_team"] == team_name]

    if home.empty and away.empty:
        raise HTTPException(status_code=404, detail=f"Equipo '{team_name}' no encontrado.")

    # Cálculo de estadísticas
    home_wins = len(home[home["result"] == "H"])
    home_draws = len(home[home["result"] == "D"])
    home_losses = len(home[home["result"] == "A"])

    away_wins = len(away[away["result"] == "A"])
    away_draws = len(away[away["result"] == "D"])
    away_losses = len(away[away["result"] == "H"])

    total_matches = len(home) + len(away)
    total_wins = home_wins + away_wins
    total_draws = home_draws + away_draws
    total_goals_for = home["home_goals"].sum() + away["away_goals"].sum()
    total_goals_against = home["away_goals"].sum() + away["home_goals"].sum()

    # Forma reciente (últimos 5 partidos)
    as_of = df["date"].max()
    form = compute_rolling_form(df, team_name, as_of, n=5)

    # Strengths
    strengths = compute_team_strengths(df)
    team_str = strengths.loc[team_name].to_dict() if team_name in strengths.index else {}

    return {
        "team": team_name,
        "league": league or "all",
        "total_matches": int(total_matches),
        "wins": int(total_wins),
        "draws": int(total_draws),
        "losses": int(total_matches - total_wins - total_draws),
        "goals_scored": int(total_goals_for),
        "goals_conceded": int(total_goals_against),
        "goal_diff": int(total_goals_for - total_goals_against),
        "points": int(total_wins * 3 + total_draws),
        "home": {
            "played": int(len(home)),
            "wins": int(home_wins),
            "draws": int(home_draws),
            "losses": int(home_losses),
            "goals_scored": int(home["home_goals"].sum()),
            "goals_conceded": int(home["away_goals"].sum()),
        },
        "away": {
            "played": int(len(away)),
            "wins": int(away_wins),
            "draws": int(away_draws),
            "losses": int(away_losses),
            "goals_scored": int(away["away_goals"].sum()),
            "goals_conceded": int(away["home_goals"].sum()),
        },
        "recent_form": form,
        "strengths": {k: round(float(v), 4) for k, v in team_str.items() if isinstance(v, float)},
    }
