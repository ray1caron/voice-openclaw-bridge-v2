#!/bin/bash
# Voice Bridge v2 - Uninstallation Script

set -e

echo "=== Voice Bridge v2 Uninstallation ==="
echo ""

# Stop service if running
if systemctl is-active --quiet voice-bridge; then
    echo "Stopping voice-bridge service..."
    sudo systemctl stop voice-bridge
    echo "✅ Service stopped"
fi

# Disable service
if systemctl is-enabled --quiet voice-bridge; then
    echo "Disabling voice-bridge service..."
    sudo systemctl disable voice-bridge
    echo "✅ Service disabled"
fi

# Remove systemd service file
echo "Removing systemd service..."
if [ -f /etc/systemd/system/voice-bridge.service ]; then
    sudo rm /etc/systemd/system/voice-bridge.service
    sudo systemctl daemon-reload
    echo "✅ Systemd service removed"
else
    echo "ℹ️  No systemd service found"
fi

# Uninstall package
echo "Uninstalling voice-bridge package..."
cd /home/hal/.openclaw/workspace/voice-bridge-v2
pip3 uninstall --break-system-packages -y voice-openclaw-bridge
echo "✅ Package uninstalled"
echo ""

# Ask about data deletion
echo ""
read -p "Delete configuration and data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting configuration..."
    if [ -d "$HOME/.config/voice-bridge" ]; then
        rm -rf "$HOME/.config/voice-bridge"
        echo "✅ Configuration deleted"
    fi

    echo "Deleting data..."
    if [ -d "$HOME/.local/share/voice-bridge" ]; then
        rm -rf "$HOME/.local/share/voice-bridge"
        echo "✅ Data directory deleted"
    fi

    echo "Deleting logs..."
    if [ -d "/var/log/voice-bridge" ]; then
        sudo rm -rf /var/log/voice-bridge
        echo "✅ Logs deleted"
    fi
else
    echo "ℹ️  Configuration and data preserved"
    echo "   Config: $HOME/.config/voice-bridge"
    echo "   Data: $HOME/.local/share/voice-bridge"
    echo "   Logs: /var/log/voice-bridge"
fi

echo ""
echo "=== Uninstallation Complete ==="