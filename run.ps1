$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv\Scripts\python.exe")) { Write-Error "No existe el entorno virtual. Ejecutá primero .\install.ps1"; exit 1 }
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
