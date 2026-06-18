"""Router — Partidos históricos"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from app.database import get_db
from app.models.match import Match
from app.schemas.match import MatchRead

router = APIRouter()


@router.get("/", response_model=List[MatchRead], summary="Lista de partidos")
def get_matches(
    league: Optional[str] = Query(None, example="E0"),
    season: Optional[str] = Query(None, example="2324"),
    team: Optional[str] = Query(None, description="Nombre del equipo (local o visitante)"),
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retorna partidos históricos con filtros opcionales.

    - **league**: Código de liga (E0=Premier League, SP1=La Liga, D1=Bundesliga)
    - **season**: Temporada en formato YYZZ (Ej: 2324 = 2023/24)
    - **team**: Filtra partidos donde el equipo jugó como local o visitante
    """
    query = db.query(Match)

    if league:
        query = query.filter(Match.league == league)
    if season:
        query = query.filter(Match.season == season)
    if team:
        query = query.filter(
            or_(Match.home_team.ilike(f"%{team}%"), Match.away_team.ilike(f"%{team}%"))
        )

    return query.order_by(Match.date.desc()).offset(skip).limit(limit).all()


@router.get("/leagues", summary="Ligas disponibles")
def get_leagues(db: Session = Depends(get_db)):
    """Retorna todas las ligas con datos en la base de datos."""
    leagues = db.query(Match.league).distinct().all()
    league_names = {
        "E0": "Premier League", "SP1": "La Liga", "D1": "Bundesliga",
        "I1": "Serie A", "F1": "Ligue 1",
    }
    return [
        {"code": l[0], "name": league_names.get(l[0], l[0])}
        for l in leagues
    ]


@router.get("/seasons", summary="Temporadas disponibles")
def get_seasons(db: Session = Depends(get_db)):
    """Retorna todas las temporadas disponibles."""
    seasons = db.query(Match.season).distinct().order_by(Match.season.desc()).all()
    return [s[0] for s in seasons]
