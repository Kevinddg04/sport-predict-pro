# SportPredict Pro — Arquitectura del Sistema

## Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO FINAL                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP (puerto 5173)
┌──────────────────────────────▼──────────────────────────────────┐
│                    FRONTEND (React 18 + Vite)                   │
│                                                                  │
│  /             → Página de inicio con stats y ligas            │
│  /predictions  → Formulario + Gráficos de predicciones         │
│  /simulation   → Monte Carlo con heatmap de marcadores         │
│  /analytics    → Comparación de modelos y métricas             │
│                                                                  │
│  Librerías: Recharts · Framer Motion · React Router · Axios    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST (puerto 8000)
┌──────────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI + uvicorn)                   │
│                                                                  │
│  GET  /health         → Estado de la API                       │
│  GET  /matches/       → Histórico de partidos                  │
│  GET  /matches/leagues → Ligas disponibles                     │
│  GET  /teams/         → Lista de equipos                       │
│  GET  /teams/{name}   → Estadísticas de un equipo             │
│  POST /predict/       → Predicción con ensemble ML             │
│  GET  /predict/evaluate → Métricas de evaluación              │
│  POST /simulate/      → Simulación Monte Carlo                 │
│                                                                  │
│  Middleware: CORS · Lifespan (carga modelos al inicio)         │
└───────────────┬───────────────────────────┬─────────────────────┘
                │                           │
    ┌───────────▼──────────┐    ┌───────────▼──────────────────┐
    │   BASE DE DATOS      │    │       ML ENGINE               │
    │   SQLite / PostgreSQL│    │                              │
    │   SQLAlchemy ORM     │    │  1. PoissonModel             │
    │                      │    │     λ_home = att_h × def_a × avg│
    │   Tablas:            │    │     Score matrix (10×10)     │
    │   - matches          │    │                              │
    │   - teams            │    │  2. RandomForestModel        │
    │                      │    │     n_estimators=200         │
    │                      │    │                              │
    │                      │    │  3. XGBoostModel             │
    │                      │    │     n_estimators=300, lr=0.05│
    │                      │    │                              │
    │                      │    │  4. LightGBMModel            │
    │                      │    │     n_estimators=300, lr=0.05│
    │                      │    │                              │
    │                      │    │  5. EnsembleModel            │
    │                      │    │     Weighted avg: 20/20/30/30│
    │                      │    │                              │
    │                      │    │  6. MonteCarloSimulator      │
    │                      │    │     N=10,000 Poisson samples │
    └──────────────────────┘    └──────────────────────────────┘
                │
    ┌───────────▼──────────────────────────────────────────────────┐
    │                    DATA PIPELINE                             │
    │                                                              │
    │  Source: football-data.co.uk (CSV, sin API key)             │
    │  URL: mmz4281/{season}/{league}.csv                         │
    │                                                              │
    │  Pipeline:                                                   │
    │  1. download_all()    → data/raw/{league}_{season}.csv     │
    │  2. build_feature_matrix() → data/processed/features.parquet│
    │  3. train_all()       → data/models/{model}.pkl            │
    │                                                              │
    │  Features generadas:                                         │
    │  - form_pts, form_gf, form_ga (últimos N games)            │
    │  - attack_strength, defense_strength (Dixon-Coles style)   │
    │  - lambda_home, lambda_away (xG esperados)                 │
    │  - implied_probs desde cuotas (Bet365)                     │
    └──────────────────────────────────────────────────────────────┘
```

## Flujo de Predicción

```
Usuario → POST /predict {home:"Arsenal", away:"Chelsea", league:"E0"}
    │
    ▼ Router predictions.py
    │
    ├─ load_processed_data() → Carga Parquet
    ├─ compute_team_strengths() → λ_home, λ_away
    ├─ compute_rolling_form() → últimos 5 partidos
    │
    ├─ EnsembleModel.predict()
    │   ├─ PoissonModel.predict_proba() → score matrix → 1X2 + Over/BTTS
    │   ├─ RandomForest.predict_proba() → [P_home, P_draw, P_away]
    │   ├─ XGBoost.predict_proba()     → [P_home, P_draw, P_away]
    │   ├─ LightGBM.predict_proba()    → [P_home, P_draw, P_away]
    │   └─ Weighted average (20/20/30/30) → probabilidades finales
    │
    └─ Response → home_win=0.48, draw=0.26, away_win=0.26, over_2_5=0.61...
```

## Flujo de Simulación Monte Carlo

```
Usuario → POST /simulate {home:"Real Madrid", away:"Barcelona", n:10000}
    │
    ▼ Router simulations.py
    │
    ├─ PoissonModel.predict_goals() → (λ_home=1.8, λ_away=1.4)
    │
    ├─ MonteCarloSimulator.simulate(λ_home, λ_away, n=10000)
    │   ├─ home_goals = rng.poisson(1.8, 10000) → [2,0,1,3,1,2,...]
    │   ├─ away_goals = rng.poisson(1.4, 10000) → [1,2,0,1,3,1,...]
    │   ├─ Calcular: H/D/A, Over/Under, BTTS
    │   └─ Contabilizar frecuencia de cada marcador
    │
    └─ Response → home_win=0.52, draw=0.24, over_2_5=0.71, scores:{2-1:0.14...}
```

## Ingeniería de Características

```
Feature              │ Descripción                          │ Fuente
─────────────────────┼──────────────────────────────────────┼────────────
form_pts             │ Puntos últimos N partidos (normaliz.) │ Calculado
form_gf              │ Goles anotados / partido (últimos N) │ Calculado
form_ga              │ Goles recibidos / partido (últimos N)│ Calculado
home_form_pts        │ Forma solo como local                │ Calculado
away_form_pts        │ Forma solo como visitante            │ Calculado
attack_home          │ Fuerza ofensiva local vs liga        │ Dixon-Coles
attack_away          │ Fuerza ofensiva visitante vs liga    │ Dixon-Coles
defense_home         │ Fuerza defensiva local vs liga       │ Dixon-Coles
defense_away         │ Fuerza defensiva visitante vs liga   │ Dixon-Coles
lambda_home          │ λ Poisson home (xG esperados)       │ Calculado
lambda_away          │ λ Poisson away (xG esperados)       │ Calculado
attack_diff          │ Diferencia de ataque (H-A)          │ Derivado
defense_diff         │ Diferencia de defensa (H-A)         │ Derivado
```

## Decisiones de Diseño

### ¿Por qué split temporal y no aleatorio?
Los partidos son series de tiempo. Un split aleatorio causaría **data leakage**: el modelo podría "ver" partidos futuros al entrenar con datos del mismo período. El split temporal garantiza que el set de evaluación son siempre partidos posteriores al training.

### ¿Por qué Monte Carlo sobre Poisson directo?
La matriz de Poisson asume independencia de goles (home y away independientes). Monte Carlo permite en el futuro añadir correlaciones entre goles (efecto Dixon-Coles ρ) sin cambiar la interfaz.

### ¿Por qué Ensemble?
Ningún modelo captura toda la varianza. XGBoost/LightGBM son buenos en patrones tabulares de features, Poisson es bueno modelando la distribución de goles. El ensemble reduce la varianza del predictor final.
