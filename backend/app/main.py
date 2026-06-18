"""
SportPredict Pro — FastAPI Application
Punto de entrada principal de la API REST.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import create_tables
from app.routers import matches, predictions, simulations, teams


# ── Lifespan: ejecuta código al iniciar/detener la app ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup y shutdown de la aplicación."""
    logger.info(f"🚀 Iniciando {settings.app_name} v{settings.app_version}")
    create_tables()

    # Cargar modelo al iniciar (evita latencia en primera petición)
    try:
        from ml.trainer import load_ensemble
        app.state.ensemble = load_ensemble()
        logger.success("Ensemble cargado correctamente")
    except FileNotFoundError:
        logger.warning(
            "Modelos no encontrados. Ejecuta 'python -m ml.trainer' para entrenarlos."
        )
        app.state.ensemble = None

    yield  # La app está corriendo

    logger.info("Apagando SportPredict Pro...")


# ── FastAPI instance ──
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## SportPredict Pro API

Plataforma de predicción deportiva con Machine Learning y simulación Monte Carlo.

### Características:
- 🤖 **Ensemble ML**: Poisson + Random Forest + XGBoost + LightGBM
- 🎲 **Monte Carlo**: 10,000 simulaciones por partido
- 📊 **Mercados**: 1X2, Over/Under 2.5, BTTS, marcadores exactos
- 🔍 **Evaluación**: Accuracy, Log Loss, Brier Score, ROI teórico

### Fuente de datos:
[football-data.co.uk](https://football-data.co.uk) — Sin API key requerida.
    """,
    contact={
        "name": "SportPredict Pro",
        "url": "https://github.com/tu-usuario/sport-predict-pro",
    },
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(matches.router, prefix="/matches", tags=["Partidos"])
app.include_router(predictions.router, prefix="/predict", tags=["Predicciones"])
app.include_router(simulations.router, prefix="/simulate", tags=["Monte Carlo"])
app.include_router(teams.router, prefix="/teams", tags=["Equipos"])


# ── Health check ──
@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica que la API está activa."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "model_loaded": app.state.ensemble is not None,
    }


@app.get("/", tags=["Sistema"])
async def root():
    """Muestra información básica de la API."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }
