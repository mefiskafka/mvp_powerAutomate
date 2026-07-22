# Ejecuta el MVP de extremo a extremo (Windows PowerShell).
# Uso: .\scripts\run_sample.ps1  [ruta_pdf]
param(
    [string]$Pdf = "sample_data\pdfs\permiso_ejemplo.pdf"
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host ">> Generando insumos de ejemplo (si faltan)..."
python scripts\generate_sample_pdf.py

Write-Host ">> Procesando: $Pdf"
python -m permits.presentation.cli.main process --pdf $Pdf
