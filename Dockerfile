# Dockerfile para Hugging Face Spaces (Raiz)
FROM python:3.11-slim as builder

WORKDIR /build
# Copiamos desde la subcarpeta backend
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copiamos todo el contenido de backend a la raiz de la imagen
COPY backend/ .

RUN mkdir -p data/models data/processed && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:7860", "app.main:app"]
