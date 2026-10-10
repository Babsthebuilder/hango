#!/usr/bin/env bash
set -euo pipefail

HANGO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HANGO_ROOT"

HANGO_PYTHON="${HANGO_PYTHON:-python}"

echo "[1/4] Validating synthetic fixtures"
"$HANGO_PYTHON" -m app.fixtures.validate data/fixtures

echo "[2/4] Running Python lint checks"
"$HANGO_PYTHON" -m ruff check apps/api scripts/benchmark.py

echo "[3/4] Running Python tests"
"$HANGO_PYTHON" -m pytest

echo "[4/4] Type-checking and building frontend"
npm --prefix apps/web run build

echo "HANGO verification passed"
