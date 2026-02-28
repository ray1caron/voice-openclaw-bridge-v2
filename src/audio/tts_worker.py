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
            # Import Piper TTS
            from piper import PiperVoice

            # Download/load the model
            model_path = self._get_model_path()
            logger.info("tts_worker.loading_model", model_path=str(model_path))

            # Load the model
            self.synthesize = PiperVoice.load(model_path)

            self.model_available = True
            logger.info("tts_worker.model_loaded", voice_model=self.config.voice_model)

        except ImportError as e:
            logger.warning("tts_worker.piper_not_available", error=str(e), message="Piper TTS not installed - using mock")
            self.model_available = False
            self.synthesize = None
        except Exception as e:
            logger.error("tts_worker.model_load_failed", error=str(e))
            self.model_available = False
            self.synthesize = None

    def _get_model_path(self) -> Path:
        """
        Get path to Piper TTS model file.

        Downloads model if not found locally.

        Returns:
            Path to ONNX model file

        Raises:
            RuntimeError: If model download/setup fails
        """
        try:
            from piper.download import find_model

            # Find or download the model
            model_dir = find_model(
                self.config.voice_model,
                update_config=False
            )

            model_path = model_dir / self.config.voice_model.split("-")[1] + ".onnx"
            if model_path.exists():
                logger.debug("tts_worker.model_found", model_path=str(model_path))
                return model_path

            # Alternative: try direct model name lookup
            voice_model = self.config.voice_model
            model_dir = find_model(voice_model, update_config=False)
            onnx_files = list(model_dir.glob("*.onnx"))

            if onnx_files:
                logger.debug("tts_worker.model_found", model_path=str(onnx_files[0]))
                return onnx_files[0]

            raise RuntimeError(f"Model not found: {self.config.voice_model}")

        except Exception as e:
            logger.error("tts_worker.model_path_error", error=str(e))
            raise RuntimeError(f"Failed to get model path: {e}") from e

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
            Complete audio array (float32, sample_rate Hz)
        """
        if not self.model_available or self.synthesize is None:
            logger.warning("tts_worker.fallback_to_mock", reason="model_not_available")
            return self._synthesize_mock(text)

        try:
            # Run synthesis in thread pool to avoid blocking
            import concurrent.futures

            loop = asyncio.get_event_loop()

            def _run_synthesis():
                audio_array = self.synthesize.synthesize(
                    text,
                    length_scale=1.0 / self.config.speed,
                )
                return audio_array

            # Run in executor (blocking operation)
            audio_array = await loop.run_in_executor(
                None,
                _run_synthesis,
            )

            audio_float32 = audio_array.astype(np.float32)

            logger.debug("tts_worker.real_synthesis", text_length=len(text), samples=len(audio_float32))
            return audio_float32

        except Exception as e:
            logger.error("tts_worker.synthesis_failed", error=str(e), text_preview=text[:50])
            # Fallback to mock on error
            return self._synthesize_mock(text)

    async def _synthesize_stream(self, text: str) -> AsyncGenerator[np.ndarray, None]:
        """
        Stream synthesis using Piper TTS.

        Yields audio chunks as they're generated, enabling low-latency playback.

        Args:
            text: Text to synthesize

        Yields:
            np.ndarray: Audio chunks (float32, ~100ms at 24kHz each)
        """
        if not self.model_available or self.synthesize is None:
            logger.warning("tts_worker.fallback_to_mock_stream", reason="model_not_available")
            audio = self._synthesize_mock(text)

            # Stream mock audio in chunks
            chunk_size = 2400  # 100ms at 24kHz
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i+chunk_size]
            return

        try:
            # For real streaming, we need to do synthesis in chunks
            # Piper TTS doesn't natively support async streaming,
            # but we can emit chunks after small batches

            import concurrent.futures
            loop = asyncio.get_event_loop()

            # Small sentences for streaming
            sentences = self._split_sentences(text)
            all_audio = []

            for sentence in sentences:
                def _run_synthesis():
                    audio_array = self.synthesize.synthesize(
                        sentence,
                        length_scale=1.0 / self.config.speed,
                    )
                    return audio_array

                # Synthesize sentence
                audio_array = await loop.run_in_executor(
                    None,
                    _run_synthesis,
                )

                # Stream in small chunks
                chunk_size = 2400  # 100ms at 24kHz

                for i in range(0, len(audio_array), chunk_size):
                    chunk = audio_array[i:i+chunk_size].astype(np.float32)
                    # Short delay to simulate streaming behavior
                    await asyncio.sleep(0.01)
                    yield chunk

                all_audio.append(audio_array)

            logger.debug(
                "tts_worker.streaming_complete",
                sentences=len(sentences),
                total_samples=sum(len(a) for a in all_audio)
            )

        except Exception as e:
            logger.error("tts_worker.streaming_failed", error=str(e), text_preview=text[:50])

            # Fallback to mock streaming on error
            audio = self._synthesize_mock(text)
            chunk_size = 2400  # 100ms at 24kHz
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i+chunk_size]

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for streaming.

        Simple rule-based sentence splitting.

        Args:
            text: Input text

        Returns:
            List of sentence strings
        """
        import re

        # Common sentence delimiters
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)

        # Filter empty sentences and add period back
        sentences = [s.strip() + '.' for s in sentences if s.strip() and len(s.strip()) > 2]

        # If no sentences found, return full text as single sentence
        if not sentences:
            sentences = [text]

        # Cap sentence length for better streaming
        max_length = 200
        result = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                result.append(sentence)
            else:
                # Split long sentences at commas
                parts = sentence.split(', ')
                current = ''
                for part in parts:
                    if len(current + part) <= max_length:
                        current += part + ', '
                    else:
                        if current:
                            result.append(current.rstrip(', ') + '.')
                        current = part + ', '
                if current:
                    result.append(current.rstrip(', ') + '.')

        return result

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