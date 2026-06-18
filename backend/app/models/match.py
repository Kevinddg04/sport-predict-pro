"""Modelos ORM — Match (Partidos históricos)"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    league = Column(String(10), index=True, nullable=False)   # E0, SP1, D1...
    season = Column(String(10), nullable=False)               # 2324
    date = Column(Date, nullable=False)
    home_team = Column(String(100), nullable=False, index=True)
    away_team = Column(String(100), nullable=False, index=True)

    # Resultado final
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    result = Column(String(1), nullable=False)                # H / D / A

    # Estadísticas de partido (opcionales, no todos los CSV los tienen)
    home_shots = Column(Integer, nullable=True)
    away_shots = Column(Integer, nullable=True)
    home_shots_on_target = Column(Integer, nullable=True)
    away_shots_on_target = Column(Integer, nullable=True)
    home_corners = Column(Integer, nullable=True)
    away_corners = Column(Integer, nullable=True)
    home_fouls = Column(Integer, nullable=True)
    away_fouls = Column(Integer, nullable=True)
    home_yellow = Column(Integer, nullable=True)
    away_yellow = Column(Integer, nullable=True)
    home_red = Column(Integer, nullable=True)
    away_red = Column(Integer, nullable=True)

    # Cuotas de mercado (para ROI teórico)
    odd_home = Column(Float, nullable=True)
    odd_draw = Column(Float, nullable=True)
    odd_away = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Match {self.home_team} vs {self.away_team} ({self.date})>"
