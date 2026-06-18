"""Modelos ORM — Team (Estadísticas de equipo por temporada)"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    league = Column(String(10), nullable=False)
    season = Column(String(10), nullable=False)

    # Estadísticas de temporada
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_scored = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)

    # Features calculadas
    avg_goals_scored_home = Column(Float, nullable=True)
    avg_goals_scored_away = Column(Float, nullable=True)
    avg_goals_conceded_home = Column(Float, nullable=True)
    avg_goals_conceded_away = Column(Float, nullable=True)
    attack_strength = Column(Float, nullable=True)
    defense_strength = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Team {self.name} ({self.league} {self.season})>"
