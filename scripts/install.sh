#!/bin/bash
# Voice Bridge v2 Installation Script

set -e

echo "=== Voice Bridge v2 Installation ==="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

if [[ ! "$PYTHON_VERSION" =~ "3.10"|"3.11"|"3.12" ]]; then
    echo "Error: Python 3.10, 3.11, or 3.12 required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version OK: $PYTHON_VERSION"
echo ""

# Install package
echo "Installing voice-bridge package..."
cd /home/hal/.openclaw/workspace/voice-bridge-v2
pip3 install --break-system-packages -e .
echo "✅ Package installed"
echo ""

# Create config directory
echo "Setting up configuration..."
CONFIG_DIR="$HOME/.config/voice-bridge"
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp config/production.yaml "$CONFIG_DIR/config.yaml"
    echo "✅ Config created at $CONFIG_DIR/config.yaml"
    echo ""
    echo "⚠️  Please review and edit the configuration:"
    echo "   $CONFIG_DIR/config.yaml"
else
    echo "ℹ️  Config already exists at $CONFIG_DIR/config.yaml"
    echo "   Use: cp config/production.yaml $CONFIG_DIR/config.yaml.new"
fi
echo ""

# Create data directory
echo "Creating data directory..."
DATA_DIR="$HOME/.local/share/voice-bridge"
mkdir -p "$DATA_DIR"/{backups,logs}
echo "✅ Data directory created at $DATA_DIR"
echo ""

# Create log directory
LOG_DIR="/var/log/voice-bridge"
if [ ! -d "$LOG_DIR" ]; then
    sudo mkdir -p "$LOG_DIR"
    sudo chown $USER:$USER "$LOG_DIR"
    echo "✅ Log directory created at $LOG_DIR"
else
    echo "ℹ️  Log directory already exists at $LOG_DIR"
fi
echo ""

# Install systemd service
echo "Installing systemd service..."
read -p "Install systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cp voice-bridge.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable voice-bridge
    echo "✅ Systemd service installed and enabled"
    echo "   Start with: sudo systemctl start voice-bridge"
else
    echo "⏭ Skipped systemd service installation"
fi
echo ""

echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit config: $CONFIG_DIR/config.yaml"
echo "2. Start service: sudo systemctl start voice-bridge"
echo "3. Check logs: sudo journalctl -u voice-bridge -f"
echo ""
echo "Or run manually:"
echo "   cd /home/hal/.openclaw/workspace/voice-bridge-v2"
echo "   python3 -m bridge.main"