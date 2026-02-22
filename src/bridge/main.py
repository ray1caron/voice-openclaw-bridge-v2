"""Main entry point for Voice-OpenClaw Bridge v2."""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path

import structlog

from bridge.config import AppConfig, get_config, DEFAULT_CONFIG_FILE
from bridge.audio_discovery import run_discovery, print_discovery_report


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def check_first_run() -> bool:
    """Check if this is the first run (no config exists)."""
    return not DEFAULT_CONFIG_FILE.exists()


def run_first_time_setup() -> AppConfig:
    """Run first-time setup with audio discovery."""
    print("\n" + "=" * 60)
    print("🎙️  Voice-OpenClaw Bridge v2 - First Time Setup")
    print("=" * 60 + "\n")
    
    # Run audio discovery
    print("🔍 Discovering audio devices...\n")
    discovery = run_discovery()
    print_discovery_report(discovery)
    
    # Get recommendations
    input_dev = discovery.recommend_input()
    output_dev = discovery.recommend_output()
    
    # Create config with discovered devices
    config = AppConfig()
    
    if input_dev:
        config.audio.input_device = input_dev.name
        logger = structlog.get_logger()
        logger.info("Configured input device", device=input_dev.name)
    
    if output_dev:
        config.audio.output_device = output_dev.name
        logger = structlog.get_logger()
        logger.info("Configured output device", device=output_dev.name)
    
    # Save configuration
    config.save()
    
    print(f"\n✅ Configuration saved to: {DEFAULT_CONFIG_FILE}")
    print("\nYou can:")
    print("  - Edit the config file directly")
    print("  - Set environment variables in ~/.voice-bridge/.env")
    print("  - Changes will be detected automatically (hot-reload enabled)")
    
    return config


async def main():
    """Main entry point for the voice bridge."""
    setup_logging()
    logger = structlog.get_logger()
    
    logger.info("Starting Voice-OpenClaw Bridge v2", version="0.1.0")
    
    # Check for first run
    if check_first_run():
        logger.info("First run detected - running setup")
        config = run_first_time_setup()
    else:
        # Load existing configuration
        try:
            config = get_config()
            logger.info(
                "Configuration loaded",
                config_file=str(DEFAULT_CONFIG_FILE),
                hot_reload=config.bridge.hot_reload,
            )
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            print(f"\n❌ Configuration error: {e}")
            print("\nYou can:")
            print(f"  - Fix the config file: {DEFAULT_CONFIG_FILE}")
            print("  - Delete it to re-run first-time setup")
            sys.exit(1)
    
    # Set log level from config
    setup_logging(config.bridge.log_level)
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler(sig):
        logger.info(f"Received signal {sig.name}, shutting down...")
        # Stop hot-reload watcher
        config.stop_hot_reload()
        # Cancel all tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    
    logger.info("Bridge initialized successfully")
    logger.info("Note: Full implementation in progress - WebSocket, STT, TTS modules pending")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("Bridge shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
