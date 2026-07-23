# =====================================================================
# Motor de procesamiento de permisos — imagen del API (FastAPI + uvicorn)
# Build:  docker compose build      Run:  docker compose up -d
# =====================================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero (capa cacheable independiente del código)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Código y metadatos del paquete
COPY pyproject.toml README.md LICENSE config.yaml ./
COPY src/ src/
COPY templates/ templates/
RUN pip install --no-deps -e .

# Usuario sin privilegios (uid 1000 = usuario típico del host: los volúmenes
# montados de data/ y logs/ quedan escribibles sin trucos de permisos).
RUN useradd --uid 1000 --create-home appuser \
    && mkdir -p data logs sample_data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "permits.presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
