$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "== Clase 10 AI Governance Harness: instalador Windows ==" -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "No se encontró Python. Instalá Python 3.11 o 3.12 desde https://www.python.org/downloads/ y activá 'Add Python to PATH'."
    exit 1
}
python -c "import sys; print('Python', sys.version)"
if (-not (Test-Path ".venv")) { python -m venv .venv }
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "Se creó .env desde .env.example. Configurá tu proveedor y token." -ForegroundColor Yellow }
New-Item -ItemType Directory -Force -Path "data" | Out-Null
Write-Host "Instalación finalizada. Ejecutá .\run.ps1" -ForegroundColor Green
