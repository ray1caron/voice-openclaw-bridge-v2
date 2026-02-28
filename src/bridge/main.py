"""
Voice Bridge v2 - Main Entry Point

This is the main entry point for the voice assistant.
Run with: python3 -m bridge.main
"""

import asyncio
import sys
import signal
import structlog

from bridge.config import get_config
from bridge.voice_orchestrator import VoiceOrchestrator

logger = structlog.get_logger()


async def main():
    """Main entry point for voice assistant."""
    logger = structlog.get_logger()
    logger.info("Voice Bridge v2 starting")

    # Load configuration
    config = get_config()
    logger.info("Configuration loaded")

    # Create orchestrator
    orchestrator = VoiceOrchestrator(config=config)
    logger.info("Voice Orchestrator created")

    # Setup signal handlers
    shutdown_event = asyncio.Event()

    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown requested", signal=signum)
        shutdown_event.set()
        orchestrator.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Run orchestrator
        logger.info("Starting voice assistant event loop")
        await orchestrator.run()

        # Wait for shutdown
        await shutdown_event.wait()

    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1

    finally:
        logger.info("Shutting down...")
        orchestrator.stop()

    return 0


def main_sync():
    """Synchronous entry point."""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main_sync()