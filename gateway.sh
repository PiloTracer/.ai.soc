#!/usr/bin/env bash
set -euo pipefail

# Modified from Strix original. See NOTICE and LICENSE for details.

APP=".ai.soc"
MIN_PYTHON="3.12"
SOC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MUTED='\033[0;2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

gateway_cleanup() {
  if [ -n "${UV_TMPDIR:-}" ] && [ -d "$UV_TMPDIR" ]; then
    rm -rf "$UV_TMPDIR" 2>/dev/null || true
  fi
}
trap gateway_cleanup EXIT

info()  { echo -e "${MUTED}$1${NC}"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; exit 1; }

banner() {
  echo ""
  echo -e "${CYAN}        █████╗ ██╗    ███████╗ ██████╗  ██████╗${NC}"
  echo -e "${CYAN}       ██╔══██╗██║    ██╔════╝██╔═══██╗██╔════╝${NC}"
  echo -e "${CYAN}       ███████║██║    ███████╗██║   ██║██║     ${NC}"
  echo -e "${CYAN}       ██╔══██║██║    ╚════██║██║   ██║██║     ${NC}"
  echo -e "${CYAN}       ██║  ██║██║    ███████║╚██████╔╝╚██████╗${NC}"
  echo -e "${CYAN}       ╚═╝  ╚═╝╚═╝    ╚══════╝ ╚═════╝  ╚═════╝${NC}"
  echo -e "${MUTED}           Security OS  •  gateway${NC}"
  echo ""
}

check_python() {
  if command -v python3 &>/dev/null; then
    local pyver
    pyver="$(python3 --version 2>&1 | grep -oP '\d+\.\d+')"
    if printf '%s\n' "$MIN_PYTHON" "$pyver" | sort --check=quiet --version-sort 2>/dev/null; then
      PYTHON_BIN="python3"
      ok "Python $pyver"
      return
    fi
    warn "System Python $pyver is too old ($MIN_PYTHON+ needed)"
  else
    warn "Python 3 not found on system"
  fi

  ensure_uv
  PYTHON_BIN="$("$UV_BIN" python find "$MIN_PYTHON" 2>/dev/null || true)"
  if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
    info "Installing Python $MIN_PYTHON+ via uv (sandboxed, no system changes)..."
    "$UV_BIN" python install "$MIN_PYTHON" 2>&1 || true
    PYTHON_BIN="$("$UV_BIN" python find "$MIN_PYTHON" 2>/dev/null || true)"
  fi
  if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
    fail "Could not acquire Python $MIN_PYTHON. Install it manually: https://python.org"
  fi
  local installed_ver
  installed_ver="$("$PYTHON_BIN" --version 2>&1 | grep -oP '\d+\.\d+')"
  ok "Python $installed_ver (via uv)"
}

check_docker() {
  if ! command -v docker &>/dev/null; then
    fail "Docker CLI not found. Install Docker: https://docs.docker.com/get-docker/"
  fi
  if ! docker info &>/dev/null; then
    fail "Docker daemon not running. Start Docker and try again."
  fi
  ok "Docker"
}

ensure_uv() {
  if [ -n "${UV_BIN:-}" ] && [ -x "$UV_BIN" ]; then
    return
  fi
  if command -v uv &>/dev/null; then
    UV_BIN="uv"
    ok "uv $(uv --version 2>/dev/null | head -1 || true)"
    return
  fi
  warn "uv not found — installing to temp directory (no system changes)"
  UV_TMPDIR="$(mktemp -d)"
  export UV_TMPDIR
  local uv_installer
  uv_installer="$(mktemp)"
  curl -fsSL https://astral.sh/uv/install.sh -o "$uv_installer"
  chmod +x "$uv_installer"
  env UV_INSTALL_DIR="$UV_TMPDIR" \
    UV_UNMANAGED_INSTALL="$UV_TMPDIR" \
    bash "$uv_installer" >/dev/null 2>&1
  rm -f "$uv_installer"
  UV_BIN="$UV_TMPDIR/uv"
  if [ ! -x "$UV_BIN" ]; then
    UV_BIN="$UV_TMPDIR/uv/uv"
  fi
  if [ ! -x "$UV_BIN" ]; then
    UV_BIN="$(find "$UV_TMPDIR" -name uv -type f 2>/dev/null | head -1)"
  fi
  if [ ! -x "$UV_BIN" ]; then
    fail "Failed to install uv. Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi
  ok "uv (installed to temp)"
}

check_env() {
  local missing=0
  if [ -z "${STRIX_LLM:-}" ]; then
    warn "STRIX_LLM not set (e.g. STRIX_LLM=openai/gpt-5.4)"
    missing=1
  fi
  if [ -z "${LLM_API_KEY:-}" ] && [ -z "${LLM_API_BASE:-}" ]; then
    warn "LLM_API_KEY not set (omit only for local/Ollama models with LLM_API_BASE)"
  fi
  if [ "$missing" -eq 1 ]; then
    echo ""
    info "Set required variables:"
    info "  export STRIX_LLM='openai/gpt-5.4'"
    info "  export LLM_API_KEY='your-api-key'"
    echo ""
  fi
  ok "Environment check"
}

usage() {
  echo "Usage: $0 -t|--target <path|url> [soc options...]"
  echo ""
  echo "Audit a local repo without installing .ai.soc:"
  echo "  $0 -t /path/to/repo-to-audit"
  echo "  $0 -t https://github.com/user/repo"
  echo "  $0 -t /path/to/repo --scan-mode quick -n"
  echo ""
  echo "All CLI flags are supported:"
  echo "  -t, --target PATH/URL     Target to audit (repeatable)"
  echo "  --mount PATH              Bind-mount large dirs (read-only)"
  echo "  -m, --scan-mode MODE      quick | standard | deep (default: deep)"
  echo "  -n, --non-interactive     Headless / CI mode"
  echo "  --instruction TEXT        Custom pentest instructions"
  echo "  --max-budget-usd NUM      LLM cost limit"
  echo "  --resume RUN_NAME         Resume a prior scan"
  echo "  -v, --version             Show version"
  echo "  --help                    This help"
  echo ""
  info "Env:  STRIX_LLM, LLM_API_KEY"
  info "Dir:  results go to \$PWD/strix_runs/<run-name/>"
}

load_env() {
  local env_file="$SOC_ROOT/.env"
  if [ -f "$env_file" ]; then
    set -a
    . "$env_file"
    set +a
    info "Loaded $(grep -c '=' "$env_file" 2>/dev/null || echo 0) vars from .env"
  fi
}

main() {
  load_env
  banner

  check_python
  check_docker
  ensure_uv
  check_env

  echo ""
  info "━━━ Running $APP from source (no installation) ━━━"
  echo ""

  exec "$UV_BIN" run \
    --directory "$SOC_ROOT" \
    --frozen \
    soc \
    "$@"
}

if [ $# -eq 0 ]; then
  usage
  exit 0
fi

case "${1:-}" in
  -h|--help|help) usage; exit 0 ;;
  -v|--version)
    load_env
    check_python
    ensure_uv
    echo ""
    "$UV_BIN" run --directory "$SOC_ROOT" --frozen soc --version
    exit 0
    ;;
esac

main "$@"
