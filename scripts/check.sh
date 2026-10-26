#!/usr/bin/env bash
# Deterministic guardrails: format check, lint, tests. Fails (exit != 0) on the first problem.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-}"
if [ -z "$PY" ]; then if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=python3; fi; fi
echo "==> black --check";  "$PY" -m black --check .
echo "==> ruff check";     "$PY" -m ruff check .
echo "==> pytest";         "$PY" -m pytest -q
echo "ALL CHECKS PASSED"
