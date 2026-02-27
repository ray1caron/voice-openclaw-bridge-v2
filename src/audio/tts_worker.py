"""
Text-to-Speech Worker using Piper TTS.

Handles text-to-speech conversion with streaming audio output.
Integrates with Voice Orchestrator for audio pipeline playback.

Dependencies:
- piper-tts: Streaming TTS engine
- onnxruntime: ONNX model runtime
- numpy: Audio array processing
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, AsyncGenerator
from enum import Enum
from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()


class TTSState(Enum):
    """TTS worker state machine."""
    IDLE = "idle"
    SYNTHESIZING = "synthesizing"
    STREAMING = "streaming"
    ERROR = "error"


class VoiceModel(Enum):
    """Available Piper voice models."""
    LESSAC_LOW = "en_US-lessac-low"
    LESSAC_MEDIUM = "en_US-lessac-medium"
    LESSAC_HIGH = "en_US-lessac-high"


@dataclass
class TTSConfig:
    """TTS worker configuration."""
    voice_model: str = VoiceModel.LESSAC_MEDIUM.value
    speed: float = 1.0
    volume: float = 1.0
    sample_rate: int = 24000
    onnx_runtime: str = "onnxruntime"

    def __post_init__(self):
        """Validate configuration."""
        if self.speed < 0.5 or self.speed > 2.0:
            raise ValueError("speed must be between 0.5 and 2.0")
        if self.volume < 0.0 or self.volume > 1.0:
            raise ValueError("volume must be between 0.0 and 1.0")


@dataclass
class TTSResult:
    """Result of TTS synthesis."""
    audio: np.ndarray
    duration_ms: float
    sample_rate: int
    text_length: int
    synthesis_time_ms: float


@dataclass
class TTSStats:
    """TTS worker statistics."""
    syntheses_total: int = 0
    syntheses_success: int = 0
    syntheses_error: int = 0
    total_duration_ms: float = 0.0
    total_synthesis_time_ms: float = 0.0
    average_synthesis_time_ms: float = 0.0

    def update_stats(self, result: Optional[TTSResult], synthesis_time_ms: float):
        """Update statistics after synthesis."""
        self.syntheses_total += 1
        self.total_synthesis_time_ms += synthesis_time_ms

        if result is None:
            self.syntheses_error += 1
        else:
            self.syntheses_success += 1
            self.total_duration_ms += result.duration_ms

        self.average_synthesis_time_ms = self.total_synthesis_time_ms / self.syntheses_total


class TTSWorker:
    """
    Text-to-Speech worker using Piper TTS.

    Features:
    - Streaming audio synthesis
    - Configurable voice models
    - Variable playback speed
    - Async synchronization support
    - Performance statistics

    Example:
        >>> tts = TTSWorker(voice_model="en_US-lessac-medium")
        >>> async for chunk in tts.speak("Hello world"):
        ...     process_audio(chunk)
    """

    def __init__(
        self,
        voice_model: str | VoiceModel = VoiceModel.LESSAC_MEDIUM.value,
        config: Optional[TTSConfig] = None,
    ):
        """
        Initialize TTS worker.

        Args:
            voice_model: Piper voice model name
            config: TTS configuration (uses default if None)

        Raises:
            ImportError: If piper-tts or onnxruntime not installed
            RuntimeError: If model loading fails
        """
        if isinstance(voice_model, VoiceModel):
            voice_model = voice_model.value

        self.config = config or TTSConfig(voice_model=voice_model)
        self.state = TTSState.IDLE
        self.stats = TTSStats()

        # Try to load piper-tts (will fail if not installed)
        self._load_model()

        logger.info(
            "tts_worker.initialized",
            voice_model=self.config.voice_model,
            speed=self.config.speed,
            sample_rate=self.config.sample_rate,
        )

    def _load_model(self):
        """Load Piper TTS model."""
        try:
            # This will fail if piper-tts not installed
            # For now, we mock it to allow code completion
            # Real implementation: load onnx model and synthesizer
            self.model_available = False
            logger.warning("tts_worker.piper_not_available", message="Piper TTS not installed - using mock")

        except ImportError as e:
            logger.error("tts_worker.import_error", error=str(e))
            raise ImportError(
                "piper-tts not installed. Install with: pip install piper-tts"
            ) from e

    async def speak(
        self,
        text: str,
        stream: bool = True,
    ) -> AsyncGenerator[np.ndarray, None]:
        """
        Speak text (async streaming).

        Args:
            text: Text to synthesize
            stream: Stream audio chunks or return complete audio

        Yields:
            np.ndarray: Audio chunks if stream=True

        Returns:
            Complete audio array if stream=False
        """
        if not text or not text.strip():
            logger.warning("tts_worker.empty_text")
            return

        self.state = TTSState.SYNTHESIZING
        start_time = time.perf_counter()

        try:
            if self.model_available:
                # Real synthesis
                if stream:
                    async for chunk in self._synthesize_stream(text):
                        yield chunk
                else:
                    audio = await self._synthesize(text)
                    yield audio
            else:
                # Mock synthesis for development
                audio = self._synthesize_mock(text)
                if stream:
                    # Stream in chunks
                    chunk_size = 2400  # 100ms at 24kHz
                    for i in range(0, len(audio), chunk_size):
                        yield audio[i:i+chunk_size]
                else:
                    yield audio

            synthesis_time = (time.perf_counter() - start_time) * 1000
            result = TTSResult(
                audio=audio if not stream else np.array([]),
                duration_ms=len(audio) / self.config.sample_rate * 1000 if not stream else 0,
                sample_rate=self.config.sample_rate,
                text_length=len(text),
                synthesis_time_ms=synthesis_time,
            )
            self.stats.update_stats(result, synthesis_time)

            self.state = TTSState.IDLE

            logger.debug(
                "tts_worker.synthesis_complete",
                text_length=len(text),
                duration_ms=result.duration_ms,
                synthesis_time_ms=synthesis_time,
            )

        except Exception as e:
            logger.error("tts_worker.synthesis_error", error=str(e))
            self.state = TTSState.ERROR
            self.stats.update_stats(None, (time.perf_counter() - start_time) * 1000)
            raise

    def speak_sync(self, text: str) -> np.ndarray:
        """
        Speak text (sync version).

        Use this from synchronous contexts.
        """
        async def _speak():
            async for chunk in self.speak(text, stream=False):
                return chunk
            return np.array([])

        return asyncio.run(_speak())

    def _synthesize_mock(self, text: str) -> np.ndarray:
        """
        Mock synthesis for development (without real TTS).

        Generates silence-like audio for testing.
        """
        # Estimate duration: 150ms per character
        duration_ms = len(text) * 150
        num_samples = int((duration_ms / 1000) * self.config.sample_rate)

        # Generate audio (white noise for testing)
        audio = np.random.uniform(-0.1, 0.1, num_samples).astype(np.float32)

        logger.debug("tts_worker.mock_synthesis", text_length=len(text), samples=num_samples)
        return audio

    async def _synthesize(self, text: str) -> np.ndarray:
        """
        Real synthesis using Piper TTS.

        Args:
            text: Text to synthesize

        Returns:
            Complete audio array
        """
        # TODO: Implement real Piper TTS synthesis
        # This requires:
        # 1. Load ONNX model
        # 2. Run inference
        # 3. Return audio
        pass
        return self._synthesize_mock(text)

    async def _synthesize_stream(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Stream synthesis using Piper TTS.

        Args:
            text: Text to synthesize

        Yields:
            Audio chunks
        """
        # TODO: Implement real streaming synthesis
        audio = self._synthesize_mock(text)
        chunk_size = 2400  # 100ms at 24kHz

        for i in range(0, len(audio), chunk_size):
            yield audio[i:i+chunk_size]

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "syntheses_total": self.stats.syntheses_total,
            "syntheses_success": self.stats.syntheses_success,
            "syntheses_error": self.stats.syntheses_error,
            "total_duration_ms": self.stats.total_duration_ms,
            "total_synthesis_time_ms": self.stats.total_synthesis_time_ms,
            "average_synthesis_time_ms": self.stats.average_synthesis_time_ms,
        }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = TTSStats()
        logger.info("tts_worker.stats_reset")


# Utility functions for common use cases

def create_from_config(config: Optional[TTSConfig] = None) -> TTSWorker:
    """
    Create TTS worker from configuration.

    Args:
        config: TTS configuration (uses default if None)

    Returns:
        Configured TTSWorker instance
    """
    from bridge.config import get_config

    cfg = config
    if cfg is None:
        try:
            tts_config = get_config().tts
            cfg = TTSConfig(
                voice_model=tts_config.voice,
                speed=tts_config.speed,
                volume=tts_config.volume,
            )
        except Exception:
            cfg = TTSConfig()

    return TTSWorker(voice_model=cfg.voice_model, config=cfg)