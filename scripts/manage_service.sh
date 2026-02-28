#!/bin/bash
# Voice Bridge v2 - Service Management Script

SERVICE_NAME="voice-bridge"

case "$1" in
    start)
        echo "Starting $SERVICE_NAME..."
        sudo systemctl start $SERVICE_NAME
        echo "✅ $SERVICE_NAME started"
        echo "   Check status: sudo systemctl status $SERVICE_NAME"
        echo "   View logs: sudo journalctl -u $SERVICE_NAME -f"
        ;;
    stop)
        echo "Stopping $SERVICE_NAME..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ $SERVICE_NAME stopped"
        ;;
    restart)
        echo "Restarting $SERVICE_NAME..."
        sudo systemctl restart $SERVICE_NAME
        echo "✅ $SERVICE_NAME restarted"
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "Viewing logs for $SERVICE_NAME (Ctrl+C to exit)..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    logs-tail)
        echo "Last 50 log entries:"
        sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
        ;;
    enable)
        echo "Enabling $SERVICE_NAME (autostart on boot)..."
        sudo systemctl enable $SERVICE_NAME
        echo "✅ $SERVICE_NAME enabled"
        ;;
    disable)
        echo "Disabling $SERVICE_NAME (no autostart on boot)..."
        sudo systemctl disable $SERVICE_NAME
        echo "✅ $SERVICE_NAME disabled"
        ;;
    *)
        echo "Voice Bridge v2 - Service Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|logs-tail|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start       - Start the voice bridge service"
        echo "  stop        - Stop the voice bridge service"
        echo "  restart     - Restart the voice bridge service"
        echo "  status      - Show service status"
        echo "  logs        - View live logs (follow mode)"
        echo "  logs-tail   - Show last 50 log entries"
        echo "  enable      - Enable service to start on boot"
        echo "  disable     - Disable service from starting on boot"
        echo ""
        echo "Examples:"
        echo "  $0 start          # Start the service"
        echo "  $0 logs           # View live logs"
        echo "  $0 status         # Check service status"
        exit 1
        ;;
esac