# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar dependencias instaladas del stage anterior
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copiar código fuente
COPY . .

# Asegurar permisos sobre carpetas de datos
RUN mkdir -p data/models data/processed && \
    chown -R appuser:appuser /app

USER appuser

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check para SRE
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE 8000

# Usamos Gunicorn con workers de Uvicorn para producción
CMD gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT}
