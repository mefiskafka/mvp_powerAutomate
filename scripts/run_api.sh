#!/usr/bin/env bash
# Arranca el API FastAPI (Linux/macOS).
# Uso: ./scripts/run_api.sh [puerto]
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${1:-8000}"
echo ">> API disponible en http://127.0.0.1:${PORT}/docs"
uvicorn permits.presentation.api.app:app --host 127.0.0.1 --port "${PORT}"
