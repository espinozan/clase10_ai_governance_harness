#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "== Clase 10 AI Governance Harness: instalador Linux =="
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: instalá Python 3.10+ y python3-venv desde el gestor de paquetes." >&2
  exit 1
fi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; echo "Se creó .env. Configurá proveedor y token antes de usar el modelo remoto."; fi
mkdir -p data
echo "Instalación finalizada. Ejecutá ./run.sh"
