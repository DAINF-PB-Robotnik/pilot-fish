#!/usr/bin/env bash
# install.sh - Pilot-Fish Unified Installer (contour or yolo mode)
#
# This script sets up everything you need:
#   1. Installs system packages
#   2. Creates a dedicated Python virtualenv
#   3. Installs Python dependencies
#   4. Generates and enables a systemd service (fish.service)
#   5. Optionally generates requirements.txt if missing or on request
#
# Usage:
#   sudo ./install.sh <contour|yolo> [generate-requirements]
# Example:
#   sudo ./install.sh contour
#   sudo ./install.sh yolo generate-requirements

set -euo pipefail

### Helper functions ###
log()   { echo -e "\n[INFO]   $1"; }
error() { echo -e "\n[ERROR]  $1" >&2; exit 1; }

### Usage check ###
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: sudo $0 <contour|yolo> [generate-requirements]"
  exit 1
fi
MODE=$1
gen_req=false
if [[ $# -eq 2 ]]; then
  if [[ $2 == "generate-requirements" ]]; then
    gen_req=true
  else
    error "Unknown option: $2"
  fi
fi

if [[ "$MODE" != "contour" && "$MODE" != "yolo" ]]; then
  error "Invalid mode '$MODE'. Choose 'contour' or 'yolo'."
fi
if [[ $EUID -ne 0 ]]; then
  error "This script must be run as root. Use 'sudo $0 $MODE'"
fi

### Paths and users ###
APP_USER=${SUDO_USER:-$(whoami)}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR="$PROJECT_ROOT/.venv_$MODE"
REQ_FILE="$PROJECT_ROOT/code/$MODE/requirements.txt"
PYTHON_BIN="$VENV_DIR/bin/python"
MAIN_SCRIPT="$PROJECT_ROOT/code/$MODE/main.py"
SERVICE_NAME="fish.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

log "Mode: $MODE"
log "Project root: $PROJECT_ROOT"
log "User: $APP_USER"

### 1) Install system packages ###
log "Updating apt cache..."
apt-get update -qq || error "apt update failed"

log "Installing system dependencies..."
apt-get install -y \
  python3-venv python3-pip python3-opencv libcamera-utils \
  libatlas-base-dev libhdf5-serial libqtgui4 libqt4-test \
  >/dev/null || error "System package installation failed"

### 2) Requirements generation check ###
if [[ ! -f "$REQ_FILE" ]]; then
  log "Requirements file missing for $MODE, generating..."
  # Activate existing venv if availableor v in .venv_contour .venv_yolo .venv; do
    if [[ -d "$v" ]]; then
      source "$v/bin/activate"
      log "Activated venv: $v"
      break
    fi
  done
  pip freeze > "$REQ_FILE" || error "Failed to generate requirements"
  deactivate || true
elif [[ "$gen_req" == true ]]; then
  log "generate-requirements flag set, regenerating $REQ_FILE"
  source "$VENV_DIR/bin/activate" 2>/dev/null || true
  pip freeze > "$REQ_FILE" || error "Failed to regenerate requirements"
  deactivate || true
fi

### 3) Create Python virtualenv ###
if [[ -d "$VENV_DIR" ]]; then
  log "Removing existing venv at $VENV_DIR"
  rm -rf "$VENV_DIR"
fi
log "Creating venv at $VENV_DIR"
python3 -m venv "$VENV_DIR" || error "venv creation failed"

### 4) Install Python dependencies ###
log "Installing Python packages from $REQ_FILE"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null || error "pip upgrade failed"
pip install -r "$REQ_FILE" >/dev/null || error "pip install failed"
deactivate

### 5) Configure systemd service ###
log "Writing service file to $SERVICE_PATH"
cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Pilot-Fish Robot (${MODE^} mode)
After=graphical.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$APP_USER/.Xauthority
WorkingDirectory=$PROJECT_ROOT/code/$MODE
ExecStart=$PYTHON_BIN $MAIN_SCRIPT
Restart=always
RestartSec=10s

[Install]
WantedBy=graphical.target
EOF
chmod 644 "$SERVICE_PATH"

### 6) Enable & start service ###
log "Reloading systemd daemon"
systemctl daemon-reload || error "systemd reload failed"

log "Enabling $SERVICE_NAME"
systemctl enable "$SERVICE_NAME" >/dev/null || error "service enable failed"

log "Restarting $SERVICE_NAME"
systemctl restart "$SERVICE_NAME" || error "service start failed"

### 7) Final output ###
log "Installation complete for $MODE mode."
echo "Next: systemctl status $SERVICE_NAME"
