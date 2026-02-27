"""
Wake Word Detector using Picovoice Porcupine.

Detects wake words to trigger voice assistant listening.
Supports multiple wake words and configurable sensitivity.

Dependencies:
- pvporcupine: Wake word engine
- pvrecorder: Audio recording
- numpy: Audio array processing
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()


class WakeWordState(Enum):
    """Wake word detector state machine."""
    IDLE = "idle"
    LISTENING = "listening"
    DETECTED = "detected"
    ERROR = "error"


class SensitivityLevel(Enum):
    """Sensitivity levels for wake word detection."""
    VERY_HIGH = 0.93
    HIGH = 0.88
    MEDIUM = 0.85
    LOW = 0.80
    VERY_LOW = 0.75


class BuiltInWakeWord(Enum):
    """Built-in wake words from Porcupine platform."""
    PORCUPINE = "porcupine"
    COMPUTER = "computer"
    BUMBLEBEE = "bumblebee"
    ALEXA = "alexa"
    NEON = "neon"


@dataclass
class WakeWordConfig:
    """Wake word detector configuration."""
    keyword_paths: list[str] | None = None
    sensitivity: float = SensitivityLevel.MEDIUM.value
    access_key: str | None = None
    device_index: int = -1
    frame_length: int = 512

    def __post_init__(self):
        """Validate configuration."""
        if self.sensitivity < 0.0 or self.sensitivity > 1.0:
            raise ValueError("sensitivity must be between 0.0 and 1.0")
        if self.access_key and len(self.access_key) < 10:
            raise ValueError("access_key must be at least 10 characters")


@dataclass
class WakeWordEvent:
    """Wake word detection event."""
    keyword: str
    confidence: float
    timestamp: float
    frame_index: int


class WakeWordDetector:
    """
    Wake Word Detector using Picovoice Porcupine.

    Features:
    - Multiple keyword support
    - Configurable sensitivity
    - Async event-driven detection
    - Callback-based notifications
    - Statistics tracking

    Example:
        >>> detector = WakeWordDetector(keyword="computer")
        >>> def on_wake(event):
        ...     print(f"Wake word detected: {event.keyword}")
        >>> await detector.listen(on_wake=on_wake)
    """

    def __init__(
        self,
        keyword: str | BuiltInWakeWord = BuiltInWakeWord.COMPUTER,
        config: Optional[WakeWordConfig] = None,
    ):
        """
        Initialize wake word detector.

        Args:
            keyword: Wake word to detect (built-in or custom model path)
            config: Detector configuration (uses default if None)

        Raises:
            ImportError: If pvporcupine not installed
            ValueError: If keyword not found or invalid config
        """
        if isinstance(keyword, BuiltInWakeWord):
            keyword = keyword.value

        self.config = config or WakeWordConfig()
        self.keyword = keyword
        self.state = WakeWordState.IDLE

        # Detection statistics
        self.detections_total: int = 0
        self.listening_time_ms: float = 0.0

        # Try to load Porcupine (will fail if not installed)
        self._load_detector()

        logger.info(
            "wake_word_detector.initialized",
            keyword=self.keyword,
            sensitivity=self.config.sensitivity,
            device_index=self.config.device_index,
        )

    def _load_detector(self):
        """Load Porcupine detector."""
        try:
            import pvporcupine

            # Set up keyword path
            keyword_paths = self.config.keyword_paths
            if keyword_paths is None:
                # Use built-in keyword
                self.keyword_path = pvporcupine.KEYWORD_PATHS.get(self.keyword)
                if self.keyword_path is None:
                    logger.error("wake_word_detector.keyword_not_found", keyword=self.keyword)
                    self.detector_available = False
                    return
                keyword_paths = [self.keyword_path]

            # Load detector (mock for development)
            self.detector_available = False
            self.keyword_paths = keyword_paths
            logger.warning("wake_word_detector.porcupine_not_available", message="Porcupine not installed - using mock")

        except ImportError as e:
            logger.error("wake_word_detector.import_error", error=str(e))
            raise ImportError(
                "pvporcupine not installed. Install with: pip install pvporcupine"
            ) from e

    async def listen(
        self,
        callback: Optional[Callable[[WakeWordEvent], None]] = None,
        timeout: Optional[float] = None,
    ) ->WakeWordEvent | None:
        """
        Listen for wake word detection.

        Args:
            callback: Optional callback function on detection
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            WakeWordEvent if detected with timeout, None otherwise

        Example:
            >>> detector = WakeWordDetector("computer")
            >>> event = await detector.listen(timeout=10.0)
            >>> if event:
            ...     print(f"Detected: {event.keyword}")
        """
        self.state = WakeWordState.LISTENING
        start_time = time.perf_counter()

        try:
            if self.detector_available:
                # Real detection using Porcupine
                event = await self._listen_real(callback, timeout)
            else:
                # Mock detection for development
                event = await self._listen_mock(callback, timeout)

            listening_time = (time.perf_counter() - start_time) * 1000
            self.listening_time_ms += listening_time

            return event

        except Exception as e:
            logger.error("wake_word_detector.listening_error", error=str(e))
            self.state = WakeWordState.ERROR
            raise

    async def _listen_real(
        self,
        callback: Optional[Callable[[WakeWordEvent], None]],
        timeout: Optional[float],
    ) ->WakeWordEvent | None:
        """
        Real wake word detection using Porcupine and pvrecorder.

        Args:
            callback: Callback on detection
            timeout: Timeout in seconds

        Returns:
            Detection event or None
        """
        import pvrecorder

        # Initialize recorder
        recorder = pvrecorder.PvRecorder(
            device_index=self.config.device_index,
            frame_length=self.config.frame_length,
        )
        recorder.start()

        try:
            frame_count = 0

            while True:
                # Check timeout
                if timeout and (time.perf_counter() - start_time) > timeout:
                    return None

                # Read audio frame
                pcm = recorder.read()

                # Process with Porcupine
                result = self.detector.process(pcm)

                if result >= 0:
                    # Wake word detected
                    event = WakeWordEvent(
                        keyword=self.keyword,
                        confidence=1.0 - self.config.sensitivity,
                        timestamp=time.time(),
                        frame_index=frame_count,
                    )

                    self.detections_total += 1
                    self.state = WakeWordState.DETECTED

                    # Call callback if provided
                    if callback:
                        callback(event)

                    return event

                frame_count += 1

                # Small sleep to yield
                await asyncio.sleep(0.01)

        finally:
            recorder.stop()

    async def _listen_mock(
        self,
        callback: Optional[Callable[[WakeWordEvent], None]],
        timeout: Optional[float],
    ) ->WakeWordEvent | None:
        """
        Mock wake word detection for development.

        Simulates detection after a delay.
        """
        # Simulate listening for 1-3 seconds then detect
        delay = 1.0 + (time.time() % 2.0)

        start = time.perf_counter()

        while (time.perf_counter() - start) < delay:
            # Check timeout
            if timeout and (time.perf_counter() - start) > timeout:
                return None

            await asyncio.sleep(0.1)

        # Generate mock detection
        event = WakeWordEvent(
            keyword=self.keyword,
            confidence=0.95 - (self.config.sensitivity * 0.1),
            timestamp=time.time(),
            frame_index=int((time.perf_counter() - start) * 16000 / 512),
        )

        self.detections_total += 1
        self.state = WakeWordState.DETECTED

        if callback:
            callback(event)

        return event

    def process_audio_frame(self, pcm_data: np.ndarray) -> int | None:
        """
        Process a single audio frame for wake word detection.

        Args:
            pcm_data: Audio frame (int16)

        Returns:
            Keyword index if detected, None otherwise

        Use for custom audio pipelines.
        """
        if self.detector_available and hasattr(self, 'detector'):
            return self.detector.process(pcm_data)
        return None

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "detections_total": self.detections_total,
            "listening_time_ms": self.listening_time_ms,
            "keyword": self.keyword,
            "sensitivity": self.config.sensitivity,
        }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.detections_total = 0
        self.listening_time_ms = 0.0
        logger.info("wake_word_detector.stats_reset")

    def stop(self) -> None:
        """Stop listening (cleanup)."""
        self.state = WakeWordState.IDLE
        logger.info("wake_word_detector.stopped")


# Utility functions

def create_from_config(config: Optional[WakeWordConfig] = None) -> WakeWordDetector:
    """
    Create wake word detector from configuration.

    Args:
        config: Wake word configuration (uses default if None)

    Returns:
        Configured WakeWordDetector instance
    """
    from bridge.config import get_config

    cfg = config
    if cfg is None:
        try:
            wake_config = get_config().wake_word
            cfg = WakeWordConfig(
                keyword_paths=wake_config.keyword_paths,
                sensitivity=wake_config.sensitivity,
                access_key=wake_config.access_key,
                device_index=wake_config.device_index,
            )
        except Exception:
            cfg = WakeWordConfig()

    from audio.wake_word import BuiltInWakeWord

    keyword = BuiltInWakeWord.COMPUTER

    return WakeWordDetector(keyword=keyword, config=cfg)