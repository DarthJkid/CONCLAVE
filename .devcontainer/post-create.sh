#!/usr/bin/env bash
# Runs once, on first creation of the codespace.
# Subsequent stops/starts do NOT rerun this — that's why we make it idempotent.

set -euo pipefail

echo "==> Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH for THIS script and for future shells.
export PATH="$HOME/.local/bin:$PATH"
if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc"; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "==> Installing Python 3.11..."
uv python install 3.11

echo "==> Syncing project dependencies..."
if [ -f pyproject.toml ]; then
  uv sync --all-extras
fi

echo "==> Installing pre-commit hooks..."
if [ -f .pre-commit-config.yaml ]; then
  uv run pre-commit install || echo "(pre-commit install skipped — no hooks file yet)"
fi

echo "==> Setup complete."
