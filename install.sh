#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "Installing Python dependencies with uv..."
uv sync --all-extras

echo "Fetching piggybank submodule..."
git submodule update --init --recursive

if command -v npm >/dev/null 2>&1; then
  echo "Installing Node dependencies..."
  npm install
else
  echo "Warning: npm not found, skipping. Install Node.js for live-reload during development." >&2
fi

if [ ! -f .env ]; then
  echo "Creating .env with defaults..."
  cp .env.example .env
fi

echo "Done! Run ./run.sh to start piggy."
