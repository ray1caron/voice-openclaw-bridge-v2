"""Unit tests for Voice Orchestrator.

Tests the main voice assistant event loop and component integration.
All components are mocked to allow independent orchestrator testing.
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock


class TestOrchestratorConfig:
    """Tests for orchestrator configuration."""

    def test_default_config(self):
        """Test creation with default parameters."""
        from bridge.voice_orchestrator import OrchestratorConfig

        config = OrchestratorConfig()

        assert config.wake_word_keyword.value == "computer"
        assert config.wake_word_sensitivity == 0.85
        assert config.stt_model == "tiny"
        assert config.tts_voice.value == "en_US-lessac-medium"
        assert config.barge_in_enabled is True

    def test_custom_config(self):
        """Test creation with custom parameters."""
        from bridge.voice_orchestrator import (
            OrchestratorConfig,
            BuiltInWakeWord,
            VoiceModel,
        )

        config = OrchestratorConfig(
            wake_word_keyword=BuiltInWakeWord.BUMBLEBEE,
            wake_word_sensitivity=0.90,
            stt_model="base",
            tts_voice=VoiceModel.LESSAC_LOW,
            barge_in_enabled=False,
        )

        assert config.wake_word_keyword.value == "bumblebee"
        assert config.wake_word_sensitivity == 0.90
        assert config.stt_model == "base"
        assert config.tts_voice.value == "en_US-lessac-low"
        assert config.barge_in_enabled is False


class TestInteractionSession:
    """Tests for interaction session dataclass."""

    def test_session_creation(self):
        """Test creating an interaction session."""
        from bridge.voice_orchestrator import InteractionSession

        session = InteractionSession()

        assert session.wake_word_event is None
        assert session.audio_length_ms == 0.0
        assert session.transcription == ""
        assert session.interrupted is False

    def test_session_with_data(self):
        """Test session with interaction data."""
        from bridge.voice_orchestrator import InteractionSession
        from audio.wake_word import WakeWordEvent

        event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        session = InteractionSession(
            wake_word_event=event,
            transcription="Hello world",
            transcription_confidence=0.9,
            transcription_time_ms=150.0,
            total_time_ms=3000.0,
        )

        assert session.wake_word_event.keyword == "computer"
        assert session.transcription == "Hello world"
        assert session.duration() == 3.0


class TestOrchestratorStats:
    """Tests for orchestrator statistics."""

    def test_stats_creation(self):
        """Test creating orchestrator statistics."""
        from bridge.voice_orchestrator import OrchestratorStats

        stats = OrchestratorStats()

        assert stats.total_interactions == 0
        assert stats.successful_interactions == 0
        assert stats.total_time_ms == 0.0

    def test_stats_updates(self):
        """Test updating statistics."""
        from bridge.voice_orchestrator import OrchestratorStats

        stats = OrchestratorStats()
        stats.total_interactions = 10
        stats.successful_interactions = 8
        stats.failed_interactions = 2
        stats.total_time_ms = 15000.0

        stats.average_interaction_time_s = stats.total_time_ms / 1000.0 / stats.total_interactions

        assert stats.total_interactions == 10
        assert stats.successful_interactions == 8
        assert stats.average_interaction_time_s == 1.5


class TestVoiceOrchestratorInit:
    """Tests for voice orchestrator initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator.state.value == "idle"
        assert orchestrator.stats.total_interactions == 0
        assert orchestrator.config.stt_model == "tiny"

    def test_init_custom_config(self):
        """Test initialization with custom config."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            OrchestratorConfig,
        )

        config = OrchestratorConfig(stt_model="base")
        orchestrator = VoiceOrchestrator(config=config)

        assert orchestrator.config.stt_model == "base"


class TestVoiceOrchestratorInitComponents:
    """Tests for component initialization."""

    def test_ensure_components_wake_word(self):
        """Test wake word detector initialization."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator._wake_word is None

        orchestrator._ensure_components()

        assert orchestrator._wake_word is not None

    def test_ensure_components_audio(self):
        """Test audio pipeline initialization."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator._audio is None

        orchestrator._ensure_components()

        assert orchestrator._audio is not None

    def test_ensure_components_stt(self):
        """Test STT worker initialization."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator._stt is None

        orchestrator._ensure_components()

        assert orchestrator._stt is not None

    def test_ensure_components_websocket(self):
        """Test WebSocket client initialization."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator._websocket is None

        orchestrator._ensure_components()

        assert orchestrator._websocket is not None

    def test_ensure_components_tts(self):
        """Test TTS worker initialization."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        assert orchestrator._tts is None

        orchestrator._ensure_components()

        assert orchestrator._tts is not None


class TestVoiceOrchestratorState:
    """Tests for state management."""

    def test_initial_state(self):
        """Test initial state is IDLE."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            OrchestratorState,
        )

        orchestrator = VoiceOrchestrator()

        assert orchestrator.state == OrchestratorState.IDLE

    def test_state_change(self):
        """Test state changes."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            OrchestratorState,
        )

        orchestrator = VoiceOrchestrator()
        orchestrator.state = OrchestratorState.LISTENING

        assert orchestrator.state == OrchestratorState.LISTENING


class TestVoiceOrchestratorCallbacks:
    """Tests for callback system."""

    def test_callback_setters(self):
        """Test setting callbacks."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()

        on_wake = Mock()
        on_transcribe = Mock()
        on_response = Mock()
        on_interrupt = Mock()
        on_error = Mock()

        orchestrator.on_wake_word = on_wake
        orchestrator.on_transcription = on_transcribe
        orchestrator.on_response = on_response
        orchestrator.on_interrupt = on_interrupt
        orchestrator.on_error = on_error

        assert orchestrator.on_wake_word == on_wake
        assert orchestrator.on_transcription == on_transcribe
        assert orchestrator.on_response == on_response
        assert orchestrator.on_interrupt == on_interrupt
        assert orchestrator.on_error == on_error


class TestVoiceOrchestratorStats:
    """Tests for statistics tracking."""

    def test_get_stats(self):
        """Test getting current statistics."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()
        stats = orchestrator.get_stats()

        assert isinstance(stats, orchestrator.stats.__class__)
        assert stats.total_interactions == 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()
        orchestrator.stats.total_interactions = 10

        orchestrator.reset_stats()

        assert orchestrator.stats.total_interactions == 0

    def test_get_current_session(self):
        """Test getting current session."""
        from bridge.voice_orchestrator import VoiceOrchestrator

        orchestrator = VoiceOrchestrator()
        session = orchestrator.get_current_session()

        assert session is None


class TestVoiceOrchestratorConfiguration:
    """Tests for runtime configuration changes."""

    def test_set_wake_word(self):
        """Test updating wake word."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            BuiltInWakeWord,
        )

        orchestrator = VoiceOrchestrator()
        orchestrator._wake_word = Mock()  # Set up existing detector

        orchestrator.set_wake_word(BuiltInWakeWord.BUMBLEBEE)

        assert orchestrator.config.wake_word_keyword == BuiltInWakeWord.BUMBLEBEE
        assert orchestrator._wake_word is None  # Should be cleared for re-init

    def test_set_tts_voice(self):
        """Test updating TTS voice."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            VoiceModel,
        )

        orchestrator = VoiceOrchestrator()
        orchestrator._tts = Mock()  # Set up existing TTS

        orchestrator.set_tts_voice(VoiceModel.LESSAC_LOW)

        assert orchestrator.config.tts_voice == VoiceModel.LESSAC_LOW
        assert orchestrator._tts is None  # Should be cleared for re-init


class TestCreateFromConfig:
    """Tests for factory function."""

    def test_create_from_config_default(self):
        """Test creating with default config."""
        from bridge.voice_orchestrator import create_from_config

        orchestrator = create_from_config()

        assert orchestrator.config.stt_model == "tiny"

    def test_create_from_config_custom(self):
        """Test creating with custom config."""
        from bridge.voice_orchestrator import (
            create_from_config,
            OrchestratorConfig,
        )

        config = OrchestratorConfig(stt_model="base")
        orchestrator = create_from_config(config=config)

        assert orchestrator.config.stt_model == "base"


class TestOrchestratorStateEnum:
    """Tests for OrchestratorState enum."""

    def test_state_values(self):
        """Test state enum values."""
        from bridge.voice_orchestrator import OrchestratorState

        assert OrchestratorState.IDLE.value == "idle"
        assert OrchestratorState.LISTENING.value == "listening"
        assert OrchestratorState.PROCESSING.value == "processing"
        assert OrchestratorState.SPEAKING.value == "speaking"
        assert OrchestratorState.ERROR.value == "error"


class TestStop:
    """Tests for stopping the orchestrator."""

    def test_stop(self):
        """Test stopping orchestrator."""
        from bridge.voice_orchestrator import (
            VoiceOrchestrator,
            OrchestratorState,
        )

        orchestrator = VoiceOrchestrator()
        orchestrator._barge_in = Mock()

        orchestrator.stop()

        assert orchestrator.state == OrchestratorState.IDLE
        orchestrator._barge_in.stop.assert_called_once()


# Test markers for pytest
pytestmark = [
    pytest.mark.unit,
    pytest.mark.orchestrator,
]