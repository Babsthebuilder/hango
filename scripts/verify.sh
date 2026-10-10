#!/usr/bin/env bash
set -euo pipefail

HANGO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HANGO_ROOT"

HANGO_PYTHON="${HANGO_PYTHON:-python}"

echo "[1/5] Validating synthetic fixtures"
"$HANGO_PYTHON" -m app.fixtures.validate data/fixtures

echo "[2/5] Running Python lint checks"
"$HANGO_PYTHON" -m ruff check apps/api scripts/benchmark.py

echo "[3/5] Running Python tests"
"$HANGO_PYTHON" -m pytest

echo "[4/5] Running frontend component and interaction tests"
npm --prefix apps/web test

echo "[5/5] Type-checking and building frontend"
npm --prefix apps/web run build

echo "HANGO verification passed"
