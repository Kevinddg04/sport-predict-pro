"""
SportPredict Pro — Configuración de la aplicación
Usa Pydantic Settings para leer variables de entorno de forma segura.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    # App
    app_name: str = "SportPredict Pro"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./data/sportpredict.db"

    # Security
    secret_key: str = "change_me_in_production"

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # ML
    monte_carlo_simulations: int = 10000
    leagues: str = "E0,SP1,D1"
    seasons: str = "2122,2223,2324"

    # Paths
    data_dir: str = os.path.join(os.path.dirname(__file__), "..", "data")
    models_dir: str = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    raw_dir: str = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir: str = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def leagues_list(self) -> List[str]:
        return [l.strip() for l in self.leagues.split(",")]

    @property
    def seasons_list(self) -> List[str]:
        return [s.strip() for s in self.seasons.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


# Singleton
settings = Settings()

# Asegura que los directorios existen
for _dir in [settings.data_dir, settings.models_dir, settings.raw_dir, settings.processed_dir]:
    os.makedirs(_dir, exist_ok=True)
