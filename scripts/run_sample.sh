#!/usr/bin/env bash
# Ejecuta el MVP de extremo a extremo (Linux/macOS).
# Uso: ./scripts/run_sample.sh
set -euo pipefail
cd "$(dirname "$0")/.."

PDF="${1:-sample_data/pdfs/permiso_ejemplo.pdf}"

echo ">> Generando insumos de ejemplo (si faltan)..."
python scripts/generate_sample_pdf.py

echo ">> Procesando: ${PDF}"
python -m permits.presentation.cli.main process --pdf "${PDF}"
