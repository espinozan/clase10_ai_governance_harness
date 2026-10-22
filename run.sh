#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then echo "Ejecutá ./install.sh primero" >&2; exit 1; fi
exec .venv/bin/python -m streamlit run app.py
