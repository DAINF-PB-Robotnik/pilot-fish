#!/usr/bin/env bash
#
# install.sh
# Pilot-Fish Unified Installer (contour or yolo mode)
#
# This script sets up everything you need:
#   1. Installs system packages
#   2. Creates a dedicated Python virtualenv
#   3. Installs Python dependencies
#   4. Generates and enables a systemd service (fish.service)
#
# Usage: sudo ./install.sh <contour|yolo>
# Example: sudo ./install.sh contour

set -euo pipefail

### Helper functions ###
log()   { echo -e "\n[INFO]    $1"; }
error() { echo -e "\n[ERROR]   $1" >&2; exit 1; }

### 1) Validate input & environment ###
if [[ $# -ne 1 ]]; then
  echo "Usage: sudo $0 <contour|yolo>"
  exit 1
fi

MODE=$1
if [[ "$MODE" != "contour" && "$MODE" != "yolo" ]]; then
  error "Invalid mode '$MODE'. Choose 'contour' or 'yolo'."
fi

if [[ "$EUID" -ne 0 ]]; then
  error "This script must be run as root. Use 'sudo ./install.sh $MODE'"
fi

### 2) Determine users and paths ###
APP_USER=${SUDO_USER:-$(whoami)}
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR="$PROJECT_ROOT/.venv_$MODE"
REQ_FILE="$PROJECT_ROOT/code/$MODE/requirements.txt"
PYTHON_BIN="$VENV_DIR/bin/python"
MAIN_SCRIPT="$PROJECT_ROOT/code/$MODE/main.py"
SERVICE_NAME="fish.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

log "Mode selected: '$MODE'"
log "Project root: $PROJECT_ROOT"
log "Application user: $APP_USER"

### 3) Install system packages ###
log "Updating system package lists..."
apt-get update -qq || error "Failed to update apt cache."

log "Installing required system packages..."
apt-get install -y \
  python3-venv python3-pip python3-opencv libcamera-utils \
  libatlas-base-dev libhdf5-serial libqtgui4 libqt4-test \
  >/dev/null || error "Failed to install system packages."

### 4) Verify requirements file ###
if [[ ! -f "$REQ_FILE" ]]; then
  error "Requirements file not found: $REQ_FILE"
fi

### 5) Create or recreate virtual environment ###
if [[ -d "$VENV_DIR" ]]; then
  log "Removing existing virtualenv at $VENV_DIR for a clean install..."
  rm -rf "$VENV_DIR"
fi

log "Creating Python virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment."

### 6) Install Python dependencies ###
log "Activating virtual environment and installing Python packages..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null || error "Failed to upgrade pip."
pip install -r "$REQ_FILE" >/dev/null || error "Failed to install Python dependencies."
deactivate

### 7) Generate systemd service unit ###
log "Writing systemd service file to $SERVICE_PATH..."
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

### 8) Enable and start service ###
log "Reloading systemd daemon..."
systemctl daemon-reload || error "Failed to reload systemd."

log "Enabling service '$SERVICE_NAME' to start on boot..."
systemctl enable "$SERVICE_NAME" >/dev/null || error "Failed to enable service."

log "Starting (or restarting) '$SERVICE_NAME'..."
systemctl restart "$SERVICE_NAME" || error "Failed to start service."

### 9) Final messages ###
log "✅ Installation complete for '$MODE' mode!"
echo -e "\nNext steps:"
echo "  • Check service status:   systemctl status $SERVICE_NAME"
echo "  • View live logs:         journalctl -u $SERVICE_NAME -f"
echo "  • Manage service manually:"
echo "      sudo systemctl stop  $SERVICE_NAME"
echo "      sudo systemctl start $SERVICE_NAME"
