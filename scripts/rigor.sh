#!/usr/bin/env bash
# Rigor CLI Wrapper - Legacy compatibility layer
# All functionality moved to Python CLI. Run: bash scripts/bootstrap.sh
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  case "$SOURCE" in
    /*) ;;
    *) SOURCE="$DIR/$SOURCE" ;;
  esac
done
REPO_ROOT="$(cd -P "$(dirname "$SOURCE")/.." && pwd)"

PYTHON_BIN="${RIGOR_PYTHON:-$REPO_ROOT/.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="${PYTHON:-python3}"
fi

exec "$PYTHON_BIN" -m rigor.cli "$@"
