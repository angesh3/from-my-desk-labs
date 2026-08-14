#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"
exec python -m uvicorn from_my_desk.main:app --reload --host 127.0.0.1 --port "${PORT:-8080}"
