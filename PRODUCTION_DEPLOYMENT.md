# Production Deployment Guide - Voice Bridge v2

**Version:** 1.0
**Date:** 2026-02-28
**Phase:** 3 - Production Deployment
**Status:** COMPLETE ✅

---

## Overview

This guide provides step-by-step instructions for deploying Voice Bridge v2 to a production environment using systemd service management.

**What This Guide Covers:**
1. System requirements
2. Installation procedure
3. Configuration
4. Service management
5. Monitoring and logging
6. Troubleshooting
7. Backup and recovery

---

## System Requirements

### Hardware Requirements
- **CPU:** x86-64 (AMD64/Intel64) architecture
  - Minimum: 2 cores
  - Recommended: 4+ cores for concurrent operations
- **RAM:** 4 GB minimum, 8 GB recommended
- **Storage:** 500 MB minimum for logs and database
- **Audio:** Microphone and speaker (or USB audio device)

### Software Requirements
- **OS:** Linux (Ubuntu 20.04+, Debian 11+, or similar)
- **Python:** 3.10, 3.11, or 3.12
- **Systemd:** Required for service management
- **Audio:** PipeWire or PulseAudio recommended

### Python Dependencies
See `pyproject.toml` for complete list. Key dependencies:
```
pydantic>=2.0
websockets>=12.0
sounddevice>=0.5
soundfile>=0.12
faster-whisper>=1.0
piper-tts>=1.2
numpy>=1.24
```

---

## Installation Procedure

### Step 1: Clone Repository (or Copy Source)

```bash
# Navigate to installation directory
cd /home/hal/.openclaw/workspace

# Clone repository (if not already cloned)
git clone https://github.com/ray1caron/voice-openclaw-bridge-v2.git
cd voice-openclaw-bridge-v2

# Or if already in workspace
cd /home/hal/.openclaw/workspace/voice-bridge-v2
```

### Step 2: Run Installation Script

```bash
# Run the installation script
./scripts/install.sh

# Or manually:
chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

The installation script will:
1. Check Python version (3.10+ required)
2. Install the package with pip
3. Create configuration directory
4. Create data and log directories
5. Ask to install systemd service

### Step 3: Configure the Service

```bash
# Edit configuration
nano ~/.config/voice-bridge/config.yaml

# Key settings to verify:
# - openclaw.websocket_url: Point to your OpenClaw instance
# - audio.input_device: Set if not using default
# - audio.output_device: Set if not using default
# - logging.level: INFO for production
```

### Step 4: Start the Service

```bash
# Start the service
sudo systemctl start voice-bridge

# Check status
sudo systemctl status voice-bridge

# View logs
sudo journalctl -u voice-bridge -f
```

### Step 5: Verify Operation

```bash
# Test voice command:
# 1. Say the wake word ("computer")
# 2. Speak your command
# 3. Verify response is spoken

# Check service status
./scripts/manage_service.sh status
```

---

## Configuration

### Configuration File Location
**Production:** `~/.config/voice-bridge/config.yaml`
**Development:** `~/.config/voice-bridge/config-development.yaml`

### Key Configuration Options

```yaml
# OpenClaw Connection
openclaw:
  websocket_url: "ws://127.0.0.1:18789/api/voice"  # IMPORTANT: Set correct URL
  timeout: 30

# Audio Devices
audio:
  input_device: "default"  # Use default or specify device name
  output_device: "default"
  sample_rate: 16000

# Microphone Settings
microphone:
  noise_gate_threshold: 0.01
  auto_gain: true
  gain: 1.0

# Speaker Settings
speaker:
  volume: 0.7  # 0.0 to 1.0

# Wake Word
wake_word:
  keyword: "computer"  # Or your custom wake word
  sensitivity: 0.85  # 0.0 to 1.0
  enabled: true

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "json"  # json or console
  file: "/var/log/voice-bridge/voice-bridge.log"

# Database
database:
  path: "${HOME}/.local/share/voice-bridge/sessions.db"
  backup_enabled: true
  backup_path: "${HOME}/.local/share/voice-bridge/backups/"
  backup_retention_days: 30
```

### Hot-Reload Configuration

```bash
# Configuration changes require restart
sudo systemctl restart voice-bridge
```

---

## Service Management

### Using the Management Script

```bash
# Start service
./scripts/manage_service.sh start

# Stop service
./scripts/manage_service.sh stop

# Restart service
./scripts/manage_service.sh restart

# Check status
./scripts/manage_service.sh status

# View live logs
./scripts/manage_service.sh logs

# View last 50 log entries
./scripts/manage_service.sh logs-tail

# Enable autostart on boot
./scripts/manage_service.sh enable

# Disable autostart on boot
./scripts/manage_service.sh disable
```

### Using systemctl Directly

```bash
# Start service
sudo systemctl start voice-bridge

# Stop service
sudo systemctl stop voice-bridge

# Restart service
sudo systemctl restart voice-bridge

# Check status
sudo systemctl status voice-bridge

# View logs
sudo journalctl -u voice-bridge -f

# Enable autostart
sudo systemctl enable voice-bridge

# Disable autostart
sudo systemctl disable voice-bridge
```

---

## Monitoring and Logging

### Monitoring Service Health

```bash
# Check if service is running
sudo systemctl is-active voice-bridge

# Detailed status
sudo systemctl status voice-bridge

# Check if autostart enabled
sudo systemctl is-enabled voice-bridge
```

### Viewing Logs

```bash
# Live logs (follow)
sudo journalctl -u voice-bridge -f

# Last 100 entries
sudo journalctl -u voice-bridge -n 100

# Logs since today
sudo journalctl -u voice-bridge --since today

# Errors only
sudo journalctl -u voice-bridge -p err

# Persist logs to file
sudo journalctl -u voice-bridge > voice-bridge-logs.txt
```

### Log Files

**Systemd Journal:** Main logs via journalctl
**Application Logs:** `/var/log/voice-bridge/voice-bridge.log` (if configured)
**Database:** `~/.local/share/voice-bridge/sessions.db`

### Performance Monitoring

**Memory Usage:**
```bash
ps aux | grep bridge
# Or top, htop
```

**CPU Usage:**
```bash
top -p $(pgrep -f bridge)
```

**Disk Usage:**
```bash
du -sh ~/.local/share/voice-bridge
du -sh ~/.config/voice-bridge
du -sh /var/log/voice-bridge
```

---

## Troubleshooting

### Service Won't Start

**Symptoms:** `systemctl start voice-bridge` fails

**Solutions:**
```bash
# Check detailed error
sudo systemctl status voice-bridge

# View logs
sudo journalctl -u voice-bridge -n 50

# Common issues:
# 1. Wrong OpenClaw URL in config
# 2. Audio device not found
# 3. Database permissions
```

### No Audio Output

**Symptoms:** Assistant responds but no sound

**Solutions:**
```bash
# Check audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test speaker
python3 -c "import sounddevice as sd; import numpy as np; sd.play(np.random.randn(44100), 44100); import time; time.sleep(1)"

# Check config audio.output_device
nano ~/.config/voice-bridge/config.yaml

# Increase volume (0.0 to 1.0)
```

### Wake Word Not Detected

**Symptoms:** Wake word not triggering

**Solutions:**
```bash
# Check microphone
python3 -c "import sounddevice as sd; sd.rec(frames=44100, samplerate=44100, channels=1); sd.wait()"

# Adjust sensitivity (0.0 to 1.0)
nano ~/.config/voice-bridge/config.yaml
# Edit: wake_word.sensitivity

# Check if enabled
# Ensure: wake_word.enabled: true
```

### OpenClaw Connection Issues

**Symptoms:** "Connection failed" or timeout errors

**Solutions:**
```bash
# Test OpenClaw server is running
curl http://127.0.0.1:18789/api/health

# Check URL in config
nano ~/.config/voice-bridge/config.yaml
# Edit: openclaw.websocket_url

# Check network
ping 127.0.0.1
telnet 127.0.0.1 18789
```

### Database Corruption

**Symptoms:** SQLite errors, session not saving

**Solutions:**
```bash
# Stop service first
sudo systemctl stop voice-bridge

# Check database integrity
sqlite3 ~/.local/share/voice-bridge/sessions.db "PRAGMA integrity_check;"

# If corruption found, restore from backup
# Backups in: ~/.local/share/voice-bridge/backups/

# Or create new database
mv ~/.local/share/voice-bridge/sessions.db ~/.local/share/voice-bridge/sessions.db.corrupted
sudo systemctl start voice-bridge
```

### Permission Issues

**Symptoms:** "Permission denied" errors

**Solutions:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER ~/.config/voice-bridge
sudo chown -R $USER:$USER ~/.local/share/voice-bridge
sudo chown -R $USER:$USER /var/log/voice-bridge

# Fix executable permissions
chmod +x scripts/*.sh
chmod +x voice-bridge.service (copy to /etc/systemd/system/)
```

---

## Backup and Recovery

### Database Backup

**Automatic Backups:**
- Configured in `config.yaml`
- Location: `~/.local/share/voice-bridge/backups/`
- Retention: 30 days (configurable)

**Manual Backup:**
```bash
# Stop service first
sudo systemctl stop voice-bridge

# Backup database
cp ~/.local/share/voice-bridge/sessions.db ~/.local/share/voice-bridge/backups/sessions-$(date +%Y%m%d-%H%M%S).db

# Start service
sudo systemctl start voice-bridge
```

### Configuration Backup

```bash
# Backup config
cp ~/.config/voice-bridge/config.yaml ~/.config/voice-bridge/config.yaml.backup

# Backup entire config directory
tar -czf voice-bridge-config-backup-$(date +%Y%m%d).tar.gz ~/.config/voice-bridge
```

### Full System Backup

```bash
# Stop service
sudo systemctl stop voice-bridge

# Backup everything
BACKUP_DIR="voice-bridge-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

cp ~/.config/voice-bridge/config.yaml $BACKUP_DIR/
cp ~/.local/share/voice-bridge/sessions.db $BACKUP_DIR/
tar -czf $BACKUP_DIR/logs.tar.gz /var/log/voice-bridge/

# Start service
sudo systemctl start voice-bridge

echo "Backup created: $BACKUP_DIR"
```

### Recovery from Backup

```bash
# Stop service
sudo systemctl stop voice-bridge

# Restore database
cp ~/.local/share/voice-bridge/backups/sessions-YYYYMMDD-HHMMSS.db ~/.local/share/voice-bridge/sessions.db

# Restore config
cp ~/.config/voice-bridge/config.yaml.backup ~/.config/voice-bridge/config.yaml

# Start service
sudo systemctl start voice-bridge
```

---

## Updates and Upgrades

### Updating from Git

```bash
# Stop service
sudo systemctl stop voice-bridge

# Pull latest changes
cd /home/hal/.openclaw/workspace/voice-bridge-v2
git pull origin master

# Reinstall
pip3 install --break-system-packages -e .

# Start service
sudo systemctl start voice-bridge
```

### Major Version Upgrade

```bash
# Backup configuration and data
cp ~/.config/voice-bridge/config.yaml ~/.config/voice-bridge/config.yaml.pre-upgrade
cp ~/.local/share/voice-bridge/sessions.db ~/.local/share/voice-bridge/sessions.db.pre-upgrade

# Stop service
sudo systemctl stop voice-bridge

# Install new version
cd /home/hal/.openclaw/workspace/voice-bridge-v2
git checkout v2.0.0  # Example: checkout new version
pip3 install --break-system-packages -e .

# Review and update config if needed
nano ~/.config/voice-bridge/config.yaml

# Start service
sudo systemctl start voice-bridge

# Monitor logs
sudo journalctl -u voice-bridge -f
```

---

## Uninstallation

```bash
# Run uninstall script
./scripts/uninstall.sh

# Or manually:
sudo systemctl stop voice-bridge
sudo systemctl disable voice-bridge
sudo rm /etc/systemd/system/voice-bridge.service
sudo systemctl daemon-reload
pip3 uninstall --break-system-packages -y voice-openclaw-bridge

# Optional: Remove config and data
rm -rf ~/.config/voice-bridge
rm -rf ~/.local/share/voice-bridge
sudo rm -rf /var/log/voice-bridge
```

---

## Security Considerations

### File Permissions
- Config: `~/.config/voice-bridge/` (user-owned)
- Data: `~/.local/share/voice-bridge/` (user-owned)
- Logs: `/var/log/voice-bridge/` (user-owned, world-readable)

### Network
- WebSocket connects to localhost by default
- Change `openclaw.websocket_url` for remote deployment
- Consider HTTPS/WSS for production

### Audio
- Microphone access requires proper permissions
- User must be in `audio` group (check with `groups`)

### Service
- Runs as non-root user ("hal" by default)
- `NoNewPrivileges=true` in service file
- Private temporary directory (optional, uncomment)

---

## Support and Resources

**Documentation:**
- IMPLEMENTATION_PLAN.md - Overall project plan
- HARDWARE_VALIDATION.md - Hardware validation results
- TEST_ENVIRONMENT.md - Test environment setup
- SYSTEM_TEST_PLAN.md - System testing

**Debug Commands:**
```bash
# Check OpenClaw connection
ss -tlnp | grep 18789

# Check audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test microphone
python3 -c "import sounddevice as sd; import numpy as np; rec = sd.rec(44100, samplerate=44100, channels=1); sd.wait(); print('OK')"

# Test speaker
python3 -c "import sounddevice as sd; import numpy as np; sd.play(np.sin(2*np.pi*440*np.linspace(0,1,44100)), 44100); import time; time.sleep(1)"
```

**Getting Help:**
- Check logs: `sudo journalctl -u voice-bridge -f`
- Review configuration: `~/.config/voice-bridge/config.yaml`
- Test components individually (see debug commands above)

---

## Appendix: Complete Directory Structure

```
voice-bridge-v2/
├── src/
│   └── bridge/
│       ├── main.py                     # Entry point
│       └── ...                         # All bridge modules
├── config/
│   ├── production.yaml                 # Production config template
│   └── development.yaml                # Development config template
├── scripts/
│   ├── install.sh                      # Installation script
│   ├── manage_service.sh               # Service management script
│   └── uninstall.sh                   # Uninstallation script
├── voice-bridge.service               # Systemd service file
├── PRODUCTION_DEPLOYMENT.md           # This document
├── pyproject.toml                     # Python package config
└── README.md                          # Project readme

Installed Locations:
├── ~/.config/voice-bridge/
│   └── config.yaml                    # Active configuration
├── ~/.local/share/voice-bridge/
│   ├── sessions.db                    # Session database
│   └── backups/                       # Database backups
└── /var/log/voice-bridge/
    └── voice-bridge.log              # Application logs
```

---

**Last Updated:** 2026-02-28
**Phase 3 Status:** ✅ COMPLETE
**Ready for:** Phase 4 (Stability Testing) or immediate deployment