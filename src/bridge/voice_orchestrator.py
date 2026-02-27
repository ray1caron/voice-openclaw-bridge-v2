"""
Voice Orchestrator - Main voice assistant event loop.

Wires together all voice components:
- Wake Word Detection
- Audio Capture and Processing
- Speech-to-Text (STT)
- OpenClaw WebSocket Communication
- Text-to-Speech (TTS)
- Audio Playback with Barge-in

This is the main voice assistant controller.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import structlog

from audio.wake_word import (
    WakeWordDetector,
    WakeWordEvent,
    WakeWordConfig,
    BuiltInWakeWord,
)
from audio.stt_worker import (
    STTWorker,
    TranscriptionResult,
    STTConfig,
)
from audio.tts_worker import (
    TTSWorker,
    TTSConfig,
    TTSResult,
    VoiceModel,
)
from bridge.audio_pipeline import (
    AudioPipeline,
    PipelineState,
)
from bridge.websocket_client import (
    WebSocketClient,
    WebSocketState,
    ConnectionConfig,
)
from audio.barge_in import (
    BargeInState,
    BargeInHandler,
    InterruptionEvent,
)

logger = structlog.get_logger()


class OrchestratorState(Enum):
    """Orchestrator state machine."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class InteractionSession:
    """Single voice interaction session."""
    wake_word_event: WakeWordEvent | None = None
    audio_length_ms: float = 0.0
    transcription: str = ""
    transcription_confidence: float = 0.0
    transcription_time_ms: float = 0.0
    openclaw_response_time_ms: float = 0.0
    tts_time_ms: float = 0.0
    total_time_ms: float = 0.0
    interrupted: bool = False

    def duration(self) -> float:
        """Total interaction duration in seconds."""
        return self.total_time_ms / 1000.0


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    #Wake Word
    wake_word_keyword: str | BuiltInWakeWord = BuiltInWakeWord.COMPUTER
    wake_word_sensitivity: float = 0.85
    wake_word_timeout: Optional[float] = None

    #Audio
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    #STT
    stt_model: str = "tiny"
    stt_compute_type: str = "auto"

    #TTS
    tts_voice: str | VoiceModel = VoiceModel.LESSAC_MEDIUM
    tts_speed: float = 1.0
    tts_volume: float = 1.0

    #WebSocket
    websocket_url: str = "ws://127.0.0.1:18789/api/voice"
    websocket_timeout: float = 30.0

    #Barge-in
    barge_in_enabled: bool = True
    barge_in_sensitivity: str = "medium"

    #General
    silence_threshold_ms: float = 1500.0
    max_interaction_time_s: float = 60.0


@dataclass
class OrchestratorStats:
    """Orchestrator statistics."""
    total_interactions: int = 0
    successful_interactions: int = 0
    interrupted_interactions: int = 0
    failed_interactions: int = 0
    total_time_ms: float = 0.0
    average_interaction_time_s: float = 0.0
    wake_word_detections: int = 0
    transcriptions: int = 0
    tts_syntheses: int = 0


class VoiceOrchestrator:
    """
    Main voice assistant orchestrator.

    Manages the complete voice interaction loop:
    1. Listen for wake word
    2. Capture speech until silence
    3. Transcribe to text
    4. Send to OpenClaw
    5. Synthesize response
    6. Play audio (with barge-in support)
    7. Return to listening

    Example:
        >>> orchestrator = VoiceOrchestrator()
        >>> await orchestrator.run()  # Event loop runs continuously
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize voice orchestrator.

        Args:
            config: Orchestrator configuration (uses default if None)

        Raises:
            ImportError: If required components not available
        """
        self.config = config or OrchestratorConfig()
        self.state = OrchestratorState.IDLE

        # Statistics
        self.stats = OrchestratorStats()
        self.session: Optional[InteractionSession] = None

        # Initialize components (lazy init for flexibility)
        self._wake_word: Optional[WakeWordDetector] = None
        self._audio: Optional[AudioPipeline] = None
        self._stt: Optional[STTWorker] = None
        self._websocket: Optional[WebSocketClient] = None
        self._tts: Optional[TTSWorker] = None
        self._barge_in: Optional[BargeInHandler] = None

        # Event callbacks
        self.on_wake_word: Optional[Callable[[WakeWordEvent], None]] = None
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.on_response: Optional[Callable[[str], None]] = None
        self.on_interrupt: Optional[Callable[[InterruptionEvent], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        logger.info(
            "voice_orchestrator.initializing",
            wake_word=self.config.wake_word_keyword,
            stt_model=self.config.stt_model,
            tts_voice=self.config.tts_voice,
        )

    def _ensure_components(self):
        """Ensure all components are initialized."""
        if self._wake_word is None:
            wake_config = WakeWordConfig(
                sensitivity=self.config.wake_word_sensitivity,
            )
            self._wake_word = WakeWordDetector(
                keyword=self.config.wake_word_keyword,
                config=wake_config,
            )

        if self._audio is None:
            self._audio = AudioPipeline()

        if self._stt is None:
            stt_config = STTConfig(
                model=self.config.stt_model,
                compute_type=self.config.stt_compute_type,
            )
            self._stt = STTWorker(config=stt_config)

        if self._websocket is None:
            ws_config = ConnectionConfig(
                url=self.config.websocket_url,
                timeout=self.config.websocket_timeout,
            )
            self._websocket = WebSocketClient(config=ws_config)

        if self._tts is None:
            tts_config = TTSConfig(
                voice_model=self.config.tts_voice,
                speed=self.config.tts_speed,
                volume=self.config.tts_volume,
            )
            self._tts = TTSWorker(config=tts_config)

        if self._barge_in is None:
            self._barge_in = BargeInHandler()
        else:
            # Reuse existing barge-in but check config
            self._barge_in.enabled = self.config.barge_in_enabled

        logger.info("voice_orchestrator.components_ready")

    async def run(self):
        """
        Run the main voice assistant event loop.

        This method runs indefinitely until stopped.
        Typical usage: await orchestrator.run()

        The loop:
        1. Listen for wake word
        2. Capture and process speech
        3. Handle OpenClaw response
        4. Speak response
        5. Return to listening
        """
        self._ensure_components()
        logger.info("voice_orchestrator.starting")

        try:
            self.state = OrchestratorState.LISTENING

            while True:
                # 1. Wait for wake word
                await self._handle_wake_word()

                # 2. Process voice interaction
                await self._process_interaction()

                # 3. Return to listening
                self.state = OrchestratorState.LISTENING

        except asyncio.CancelledError:
            logger.info("voice_orchestrator.cancelled")
            raise
        except Exception as e:
            logger.error("voice_orchestrator.fatal_error", error=str(e), exc_info=True)
            self.state = OrchestratorState.ERROR
            if self.on_error:
                self.on_error(e)
            raise

    async def _handle_wake_word(self):
        """Wait for wake word detection."""
        if self._wake_word is None:
            return

        logger.debug("voice_orchestrator.waiting_for_wake_word")
        self.state = OrchestratorState.LISTENING

        event = await self._wake_word.listen(
            callback=self.on_wake_word,
            timeout=self.config.wake_word_timeout,
        )

        if event:
            self.stats.wake_word_detections += 1
            logger.info("voice_orchestrator.wake_word_detected", keyword=event.keyword)
        else:
            logger.debug("voice_orchestrator.wake_word_timeout")

    async def _process_interaction(self):
        """Process a complete voice interaction."""
        session_start = time.perf_counter()
        self.session = InteractionSession()
        self.stats.total_interactions += 1

        try:
            self.state = OrchestratorState.PROCESSING

            # 1. Capture audio until silence
            audio, duration_ms = await self._capture_speech()
            self.session.audio_length_ms = duration_ms

            # 2. Transcribe to text
            transcription = await self._transcribe(audio)
            self.session.transcription = transcription.text
            self.session.transcription_confidence = transcription.confidence

            logger.info(
                "voice_orchestrator.transcribed",
                text=transcription.text,
                confidence=transcription.confidence,
            )

            if self.on_transcription:
                self.on_transcription(transcription.text)

            # 3. Send to OpenClaw and get response
            response_text = await self._send_to_openclaw(transcription.text)

            logger.info("voice_orchestrator.response_received", text=response_text)

            if self.on_response:
                self.on_response(response_text)

            # 4. Synthesize and speak response
            await self._speak_response(response_text)

            # 5. Update stats
            total_time_ms = (time.perf_counter() - session_start) * 1000
            self.session.total_time_ms = total_time_ms
            self.stats.successful_interactions += 1
            self.stats.total_time_ms += total_time_ms
            self.stats.average_interaction_time_s = (
                self.stats.total_time_ms / 1000.0 / self.stats.total_interactions
            )

            logger.info(
                "voice_orchestrator.interaction_complete",
                duration_s=self.session.duration(),
            )

        except asyncio.CancelledError:
            logger.info("voice_orchestrator.interaction_cancelled")
            self.session.interrupted = True
            self.stats.interrupted_interactions += 1
            raise
        except Exception as e:
            logger.error("voice_orchestrator.interaction_failed", error=str(e))
            self.stats.failed_interactions += 1
            if self.on_error:
                self.on_error(e)
            raise

    async def _capture_speech(self) ->tuple[bytes, float]:
        """
        Capture audio from microphone until silence.

        Returns:
            Tuple of (audio_data, duration_ms)
        """
        if self._audio is None:
            raise RuntimeError("Audio pipeline not initialized")

        # Capture with Vad until silence
        audio_data = asyncio.create_task(
            self._audio.capture_audio(
                silence_threshold_ms=self.config.silence_threshold_ms,
            )
        )

        # Wait for capture or interruption
        try:
            result = await asyncio.wait_for(
                audio_data,
                timeout=self.config.max_interaction_time_s,
            )
            duration_ms, audio_bytes = result
            return audio_bytes, duration_ms

        except asyncio.TimeoutError:
            logger.warning("voice_orchestrator.capture_timeout")
            # Return empty audio
            audio_bytes = b""
            return audio_bytes, 0.0

    async def _transcribe(self, audio_data: bytes) ->TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio_data: Audio data to transcribe

        Returns:
            Transcription result with text and confidence
        """
        if self._stt is None:
            raise RuntimeError("STT worker not initialized")

        start_time = time.perf_counter()
        result = await self._stt.transcribe(audio_data)
        transcription_time_ms = (time.perf_counter() - start_time) * 1000

        self.session.transcription_time_ms = transcription_time_ms
        self.stats.transcriptions += 1

        return result

    async def _send_to_openclaw(self, text: str) ->str:
        """
        Send text to OpenClaw and get response.

        Args:
            text: Transcribed speech to send

        Returns:
            OpenClaw response text
        """
        if self._websocket is None:
            raise RuntimeError("WebSocket client not initialized")

        start_time = time.perf_counter()

        # Send voice input
        await self._websocket.send_voice_input(text)

        # Wait for response
        response = await self._websocket.receive_response()
        response_text = response.get("text", "")

        response_time_ms = (time.perf_counter() - start_time) * 1000
        self.session.openclaw_response_time_ms = response_time_ms

        return response_text

    async def _speak_response(self, text: str):
        """
        Synthesize and speak response.

        Args:
            text: Response text to speak
        """
        if self._tts is None:
            raise RuntimeError("TTS worker not initialized")

        self.state = OrchestratorState.SPEAKING

        start_time = time.perf_counter()

        # Stream TTS for barge-in support
        async for chunk in self._tts.speak(text, stream=True):
            # Check for interruption
            if self._barge_in and self._barge_in.check_interruption():
                logger.info("voice_orchestrator.barge_in_interrupted")
                await self._barge_in.handle_interruption()
                self.session.interrupted = True
                break

            # Play audio chunk
            if self._audio:
                await self._audio.play_audio(chunk)

        tts_time_ms = (time.perf_counter() - start_time) * 1000
        self.session.tts_time_ms = tts_time_ms
        self.stats.tts_syntheses += 1

    def stop(self):
        """Stop the orchestrator gracefully."""
        logger.info("voice_orchestrator.stopping")
        self.state = OrchestratorState.IDLE

        # Stop barge-in handler
        if self._barge_in:
            self._barge_in.stop()

    def get_stats(self) ->OrchestratorStats:
        """Get current statistics."""
        return self.stats

    def get_current_session(self) ->Optional[InteractionSession]:
        """Get current interaction session."""
        return self.session

    def reset_stats(self):
        """Reset all statistics."""
        self.stats = OrchestratorStats()
        logger.info("voice_orchestrator.stats_reset")

    def set_wake_word(self, keyword: str | BuiltInWakeWord):
        """
        Update wake word (requires restart).

        Args:
            keyword: New wake word to use
        """
        self.config.wake_word_keyword = keyword
        if self._wake_word:
            # Force re-init
            self._wake_word = None

    def set_tts_voice(self, voice: str | VoiceModel):
        """
        Update TTS voice.

        Args:
            voice: New TTS voice model
        """
        self.config.tts_voice = voice
        if self._tts:
            # Force re-init
            self._tts = None


def create_from_config(config: Optional[OrchestratorConfig] = None) -> VoiceOrchestrator:
    """
    Create voice orchestrator from configuration.

    Args:
        config: Orchestrator configuration (uses default if None)

    Returns:
        Configured VoiceOrchestrator instance
    """
    return VoiceOrchestrator(config=config)


# Utility functions

async def run_orchestrator(
    wake_word: str | BuiltInWakeWord = BuiltInWakeWord.COMPUTER,
):
    """
    Run voice orchestrator with default configuration.

    Convenience function for quick setup.

    Args:
        wake_word: Wake word to use

    Example:
        >>> await run_orchestrator(wake_word="computer")
    """
    orchestrator = VoiceOrchestrator()
    await orchestrator.run()