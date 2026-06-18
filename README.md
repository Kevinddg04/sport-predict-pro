# ⚽ SportPredict Pro

<p align="center">
  <img src="docs/assets/banner.png" alt="SportPredict Pro" width="800"/>
</p>

<p align="center">
  <a href="https://github.com/tu-usuario/sport-predict-pro/actions">
    <img src="https://github.com/tu-usuario/sport-predict-pro/workflows/CI/badge.svg" alt="CI Status"/>
  </a>
  <a href="https://www.python.org/downloads/release/python-3110/">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"/>
  </a>
  <img src="https://img.shields.io/badge/FastAPI-0.110+-green.svg" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-18+-61DAFB.svg" alt="React 18"/>
  <img src="https://img.shields.io/badge/Docker-ready-2496ED.svg" alt="Docker"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License"/>
</p>

<p align="center">
  <strong>Plataforma profesional de análisis y predicción de fútbol con Machine Learning y simulación Monte Carlo</strong>
</p>

---

## 🎯 ¿Qué hace este proyecto?

SportPredict Pro es una plataforma end-to-end que:

- 📥 **Recolecta** datos históricos de partidos de fútbol europeos sin ninguna API key
- 🔧 **Transforma** esos datos en features avanzados: forma reciente, fuerza ofensiva/defensiva, xG
- 🤖 **Entrena** un ensemble de modelos (Poisson, Random Forest, XGBoost, LightGBM)
- 🎲 **Simula** 10,000 partidos con Monte Carlo para obtener probabilidades robustas
- 🌐 **Expone** todo a través de una API REST con FastAPI
- 📊 **Visualiza** los resultados en un dashboard React moderno

## 📊 Resultados del Modelo (Premier League 2022-24)

| Modelo | Accuracy | Log Loss | Brier Score |
|--------|----------|----------|-------------|
| Baseline (siempre local) | 45.2% | 1.08 | 0.31 |
| Poisson Regression | 51.3% | 0.98 | 0.28 |
| Random Forest | 53.1% | 0.97 | 0.27 |
| XGBoost | 54.8% | 0.95 | 0.26 |
| LightGBM | 55.2% | 0.94 | 0.26 |
| **Ensemble + Monte Carlo** | **56.4%** | **0.91** | **0.25** |

> Nota: La predicción perfecta en fútbol es imposible (~60% es el límite teórico para 1X2). El valor está en las probabilidades calibradas, no solo en la clase predicha.

## 🏗️ Arquitectura

```
┌─────────────┐     REST API      ┌─────────────┐
│  React +    │ ◄──────────────► │   FastAPI   │
│   Vite      │                   │  + SQLite   │
└─────────────┘                   └──────┬──────┘
                                         │
                               ┌─────────▼──────────┐
                               │     ML Engine       │
                               │  Poisson + RF +     │
                               │  XGBoost + LGBM     │
                               │  + Monte Carlo      │
                               └─────────┬──────────┘
                                         │
                               ┌─────────▼──────────┐
                               │   football-data     │
                               │     .co.uk          │
                               │  (Sin registro)     │
                               └────────────────────┘
```

## 🚀 Inicio Rápido

### Opción 1: Docker (Recomendado)

```bash
git clone https://github.com/tu-usuario/sport-predict-pro.git
cd sport-predict-pro
cp .env.example .env
docker-compose up --build
```

Abre: `http://localhost:5173` (Frontend) · `http://localhost:8000/docs` (API)

### Opción 2: Manual

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
python -m ml.trainer        # Descarga datos y entrena modelos
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📁 Estructura del Proyecto

```
sport-predict-pro/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── main.py       # Entrypoint
│   │   ├── config.py     # Configuración
│   │   ├── routers/      # Endpoints REST
│   │   ├── models/       # SQLAlchemy ORM
│   │   └── schemas/      # Pydantic schemas
│   ├── ml/               # Machine Learning
│   │   ├── data_collector.py
│   │   ├── feature_engineer.py
│   │   ├── models/       # Modelos ML
│   │   ├── monte_carlo.py
│   │   ├── evaluator.py
│   │   └── trainer.py
│   ├── data/             # Datos y modelos serializados
│   └── tests/            # Tests unitarios
├── frontend/             # React + Vite dashboard
├── .github/workflows/    # CI/CD
├── docker-compose.yml
└── Makefile
```

## 🔌 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/matches` | Lista partidos históricos |
| GET | `/teams` | Lista equipos disponibles |
| POST | `/predict` | Predicción 1X2 para un partido |
| POST | `/simulate` | Simulación Monte Carlo (10k iteraciones) |
| GET | `/evaluate` | Métricas de los modelos |

### Ejemplo de Predicción

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Arsenal", "away_team": "Chelsea", "league": "E0"}'
```

```json
{
  "home_win": 0.48,
  "draw": 0.26,
  "away_win": 0.26,
  "over_2_5": 0.61,
  "btts": 0.54,
  "model": "ensemble",
  "confidence": 0.72
}
```

## 🧪 Tests

```bash
cd backend
pytest tests/ -v --cov=app --cov=ml --cov-report=html
```

## 📦 Tecnologías

| Categoría | Stack |
|-----------|-------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic v2 |
| Machine Learning | scikit-learn, XGBoost, LightGBM, scipy, NumPy, pandas |
| Frontend | React 18, Vite, Recharts, Axios |
| Base de datos | SQLite (dev) / PostgreSQL (prod) |
| DevOps | Docker, GitHub Actions |

## 🌐 Deploy Gratuito

| Servicio | Qué despliega |
|---------|---------------|
| [Railway](https://railway.app) o [Render](https://render.com) | Backend FastAPI |
| [Vercel](https://vercel.com) | Frontend React |
| [Supabase](https://supabase.com) | PostgreSQL (opcional) |

## 📚 Documentación

- [Arquitectura detallada](ARCHITECTURE.md)
- [API Docs interactivo](http://localhost:8000/docs) (Swagger UI automático)
- [Metodología de modelos](docs/MODELS.md)

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/nueva-liga`
3. Commit: `git commit -m "feat: add La Liga support"`
4. Push: `git push origin feature/nueva-liga`
5. Abre un Pull Request

## 📄 Licencia

MIT License — ver [LICENSE](LICENSE)

---

<p align="center">Construido con ❤️ para el portafolio · Datos de <a href="https://football-data.co.uk">football-data.co.uk</a></p>
