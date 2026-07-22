# Arranca el API FastAPI (Windows PowerShell).
# Uso: .\scripts\run_api.ps1 [-Port 8000]
param(
    [int]$Port = 8000
)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host ">> API disponible en http://127.0.0.1:$Port/docs"
uvicorn permits.presentation.api.app:app --host 127.0.0.1 --port $Port
