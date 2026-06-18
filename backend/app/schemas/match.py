"""Schemas Pydantic — Match"""
from pydantic import BaseModel
from datetime import date
from typing import Optional


class MatchBase(BaseModel):
    league: str
    season: str
    date: date
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    result: str


class MatchCreate(MatchBase):
    pass


class MatchRead(MatchBase):
    id: int
    odd_home: Optional[float] = None
    odd_draw: Optional[float] = None
    odd_away: Optional[float] = None

    model_config = {"from_attributes": True}


class MatchFilter(BaseModel):
    league: Optional[str] = None
    season: Optional[str] = None
    team: Optional[str] = None
    limit: int = 50
    skip: int = 0
