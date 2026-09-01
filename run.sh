#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d .venv ] || [ ! -d node_modules ] || [ ! -e piggybank/.git ]; then
  echo "Dependencies not installed yet, running install.sh..."
  ./install.sh
fi

exec uv run python run.py
