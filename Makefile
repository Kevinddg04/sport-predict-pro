.PHONY: help install train dev test lint docker-up docker-down clean

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Setup ----
install:  ## Instala dependencias de Python y Node
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ---- Data & Training ----
download:  ## Descarga datos históricos de football-data.co.uk
	cd backend && python -m ml.data_collector

train:  ## Entrena todos los modelos ML
	cd backend && python -m ml.trainer

# ---- Desarrollo ----
dev-backend:  ## Inicia el backend FastAPI con hot-reload
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:  ## Inicia el frontend React con Vite
	cd frontend && npm run dev

# ---- Tests ----
test:  ## Ejecuta todos los tests con cobertura
	cd backend && pytest tests/ -v --cov=app --cov=ml --cov-report=term-missing

test-fast:  ## Tests sin cobertura (más rápido)
	cd backend && pytest tests/ -v

# ---- Calidad de Código ----
lint:  ## Lint con ruff y black
	cd backend && ruff check . && black --check .

format:  ## Formatea el código con black
	cd backend && black .

# ---- Docker ----
docker-up:  ## Levanta todos los servicios con Docker
	docker-compose up --build -d

docker-down:  ## Detiene todos los servicios Docker
	docker-compose down

docker-logs:  ## Muestra logs de los servicios
	docker-compose logs -f

# ---- Limpieza ----
clean:  ## Limpia archivos generados
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/.pytest_cache backend/htmlcov backend/.coverage
