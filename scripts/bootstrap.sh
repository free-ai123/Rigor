#!/usr/bin/env bash
# Rigor one-command bootstrap.
#
# Usage:
#   bash scripts/bootstrap.sh
#   bash scripts/bootstrap.sh --skip-hermes
#   bash scripts/bootstrap.sh --prod --no-check
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT_SOURCE" ]; do
  SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_SOURCE")" && pwd)"
  SCRIPT_SOURCE="$(readlink "$SCRIPT_SOURCE")"
  case "$SCRIPT_SOURCE" in
    /*) ;;
    *) SCRIPT_SOURCE="$SCRIPT_DIR/$SCRIPT_SOURCE" ;;
  esac
done
REPO_ROOT="$(cd -P "$(dirname "$SCRIPT_SOURCE")/.." && pwd)"

VENV_DIR="$REPO_ROOT/.venv"
INSTALL_SPEC=".[security]"
RUN_HERMES=1
RUN_CHECK=1
FULL_CHECK=0
INSTALL_PRE_COMMIT=0

log_info() { printf "%b[INFO]%b %s\n" "$BLUE" "$NC" "$1"; }
log_ok() { printf "%b[OK]%b   %s\n" "$GREEN" "$NC" "$1"; }
log_warn() { printf "%b[WARN]%b %s\n" "$YELLOW" "$NC" "$1"; }
log_error() { printf "%b[ERROR]%b %s\n" "$RED" "$NC" "$1"; }

usage() {
  cat <<'EOF'
Rigor bootstrap

Creates a local .venv, installs Rigor, optionally deploys Hermes expert
profiles, and runs a smoke check.

Options:
  --prod          Install runtime + security extras (default)
  --dev           Install development/test extras and pre-commit hooks
  --minimal       Install only the runtime package
  --skip-hermes   Do not run scripts/setup-expert-team.sh
  --no-check      Skip smoke checks
  --full-check    Run the full local gate after installation
  --no-pre-commit Do not install the git pre-commit hook
  --venv PATH     Use a custom virtualenv directory
  -h, --help      Show this help
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prod)
      INSTALL_SPEC=".[security]"
      ;;
    --dev)
      INSTALL_SPEC=".[dev,security]"
      INSTALL_PRE_COMMIT=1
      ;;
    --minimal)
      INSTALL_SPEC="."
      ;;
    --skip-hermes)
      RUN_HERMES=0
      ;;
    --no-check)
      RUN_CHECK=0
      ;;
    --full-check)
      FULL_CHECK=1
      ;;
    --no-pre-commit)
      INSTALL_PRE_COMMIT=0
      ;;
    --venv)
      if [ "$#" -lt 2 ]; then
        log_error "--venv requires a path"
        exit 2
      fi
      VENV_DIR="$2"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      usage
      exit 2
      ;;
  esac
  shift
done

if [ "$FULL_CHECK" -eq 1 ] && [ "$INSTALL_SPEC" != ".[dev,security]" ]; then
  log_warn "--full-check requires development dependencies; using .[dev,security]"
  INSTALL_SPEC=".[dev,security]"
fi

find_python() {
  if [ -n "${PYTHON:-}" ] && command -v "$PYTHON" >/dev/null 2>&1; then
    printf "%s\n" "$PYTHON"
    return 0
  fi

  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
      then
        printf "%s\n" "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

run_smoke_check() {
  local venv_python="$1"
  local rigor_bin="$VENV_DIR/bin/rigor"

  log_info "Running smoke checks"
  "$venv_python" -m pip check

  if [ -x "$rigor_bin" ]; then
    "$rigor_bin" --help >/dev/null
  else
    "$venv_python" -m rigor.cli --help >/dev/null
  fi
  log_ok "Rigor CLI starts successfully"

  if [ "$FULL_CHECK" -eq 1 ]; then
    log_info "Running full local gate"
    (cd "$REPO_ROOT" && PYTHON="$venv_python" make check)
  fi
}

main() {
  cd "$REPO_ROOT"

  printf "\n%bRigor one-command bootstrap%b\n\n" "$BOLD" "$NC"

  local python_bin
  if ! python_bin="$(find_python)"; then
    log_error "Python 3.10+ is required. Install Python first, then rerun this script."
    exit 1
  fi
  log_ok "Python detected: $("$python_bin" -c 'import sys; print(sys.version.split()[0])')"

  if [ ! -x "$VENV_DIR/bin/python" ]; then
    log_info "Creating virtualenv: $VENV_DIR"
    "$python_bin" -m venv "$VENV_DIR"
  else
    log_ok "Reusing virtualenv: $VENV_DIR"
  fi

  local venv_python="$VENV_DIR/bin/python"
  log_info "Upgrading packaging tools"
  "$venv_python" -m pip install --upgrade pip setuptools wheel

  log_info "Installing Rigor: pip install -e \"$INSTALL_SPEC\""
  "$venv_python" -m pip install -e "$INSTALL_SPEC"
  log_ok "Rigor installed"

  if [ "$INSTALL_PRE_COMMIT" -eq 1 ] && [ -d "$REPO_ROOT/.git" ]; then
    if "$venv_python" -m pre_commit --version >/dev/null 2>&1; then
      "$venv_python" -m pre_commit install || log_warn "pre-commit hook install failed; continuing"
    elif [ "$INSTALL_SPEC" != "." ]; then
      log_warn "pre-commit is not available; continuing"
    fi
  fi

  if [ "$RUN_HERMES" -eq 1 ]; then
    log_info "Running Hermes expert-team setup"
    bash "$REPO_ROOT/scripts/setup-expert-team.sh"
  else
    log_warn "Skipping Hermes expert-team setup"
  fi

  if [ "$RUN_CHECK" -eq 1 ]; then
    run_smoke_check "$venv_python"
  fi

  printf "\n%bBootstrap complete.%b\n" "$GREEN" "$NC"
  printf "The plain 'rigor' command is available after activating the virtualenv:\n"
  printf "  source %s/bin/activate\n" "$VENV_DIR"
  printf "  rigor chat\n\n"
  printf "Without activation, use the repo wrapper:\n"
  printf "  ./scripts/rigor.sh chat\n\n"
}

main
