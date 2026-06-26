#!/usr/bin/env bash
# Rigor CLI Wrapper - Legacy compatibility layer
# All functionality moved to Python CLI. Run: pip install -e . && rigor --help
exec python3 -m rigor.cli "$@"
