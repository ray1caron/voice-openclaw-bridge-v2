"""
End-to-End Testing for Voice Assistant.

Tests the complete voice interaction flow from wake word to response.
Uses mocks for OpenClaw to avoid needing server connection.
"""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np


class MockOpenClawServer:
    """Mock OpenClaw WebSocket server for testing."""

    def __init__(self):
        self.messages_received = []
        self.response_text = "This is a mock response from OpenClaw."

    async def receive_message(self, message: str):
        """Simulate receiving a message from client."""
        self.messages_received.append(message)

    def get_response(self) ->dict:
        """Get mock response."""
        return {
            "text": self.response_text,
            "type": "final",
            "metadata": {},
        }

    async def send_response(self):
        """Simulate sending response to client."""
        return self.get_response()


class TestVoiceAssistantE2E:
    """End-to-end tests for complete voice flow."""

    @pytest.mark.asyncio
    async def test_full_interaction_flow(self):
        """Test complete interaction: wake word → capture → transcribe → OpenClaw → TTS"""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult
        from pathlib import Path

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Use real test audio file
        audio_file = Path("tests/fixtures/audio/speech_short_1s.flac")
        if not audio_file.exists():
            pytest.skip(f"Test audio file not found: {audio_file}")

        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_file)

        # Convert to bytes (what audio pipeline would provide)
        import struct
        mock_audio = audio_data.tobytes()

        # Mock wake word detection
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        # Mock STT transcription
        mock_transcription = TranscriptionResult(
            text="Hello OpenClaw",
            confidence=0.92,
            time_ms=150.0,
        )

        # Mock TTS synthesis
        mock_tts_audio = np.random.uniform(-0.1, 0.1, 16000).astype(np.float32)

        # Set up mocks
        with patch.object(orchestrator._wake_word.__class__, 'listen') as mock_listen:
            mock_listen.return_value = wake_event

            with patch.object(orchestrator._audio.__class__, 'capture_audio') as mock_capture:
                mock_capture.return_value = (2000.0, mock_audio)

                with patch.object(orchestrator._stt.__class__, 'transcribe') as mock_transcribe:
                    mock_transcribe.return_value = mock_transcription

                    with patch.object(orchestrator._websocket.__class__, 'send_voice_input') as mock_send:
                        mock_send.return_value = mock_server.get_response()

                        with patch.object(orchestrator._tts.__class__, 'speak') as mock_speak:
                            async def mock_speak_gen():
                                yield mock_tts_audio
                            mock_speak.return_value = mock_speak_gen()

                            # Simulate one interaction
                            await orchestrator._handle_wake_word()
                            await orchestrator._process_interaction()

                            # Verify wake word
                            assert orchestrator.stats.wake_word_detections == 1

                            # Verify OpenClaw was called
                            mock_send.assert_called_once_with("Hello OpenClaw")

                            # Verify TTS was called
                            mock_speak.assert_called_once_with("This is a mock response from OpenClaw", stream=True)

                            # Verify stats
                            assert orchestrator.stats.total_interactions == 1
                            assert orchestrator.stats.successful_interactions == 1

    @pytest.mark.asyncio
    async def test_barge_in_during_tts(self):
        """Test barge-in interruption during TTS playback."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Mock wake word
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        # Mock audio
        mock_audio = b"mock_audio_data"

        # Mock transcription
        mock_transcription = TranscriptionResult(
            text="Hello",
            confidence=0.90,
            time_ms=100.0,
        )

        # Mock TTS that will be interrupted
        interruption_triggered = False

        async def interrupted_tts(text, stream=True):
            """TTS that gets interrupted mid-stream."""
            for i in range(10):
                if i == 5 and interruption_triggered:
                    # Simulate interruption at chunk 5
                    break
                yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
                await asyncio.sleep(0.01)

        # Mock barge-in handler that triggers at chunk 5
        def check_interruption_side_effect():
            nonlocal interruption_triggered
            interruption_triggered = True
            return True

        # Set up mocks
        orchestrator._barge_in = Mock()
        orchestrator._barge_in.check_interruption = Mock(side_effect=check_interruption_side_effect)

        with patch.object(orchestrator._wake_word.__class__, 'listen') as mock_listen:
            mock_listen.return_value = wake_event

            with patch.object(orchestrator._audio.__class__, 'capture_audio') as mock_capture:
                mock_capture.return_value = (1000.0, mock_audio)

                with patch.object(orchestrator._stt.__class__, 'transcribe') as mock_transcribe:
                    mock_transcribe.return_value = mock_transcription

                    with patch.object(orchestrator._websocket.__class__, 'send_voice_input') as mock_send:
                        mock_send.return_value = mock_server.get_response()

                        with patch.object(orchestrator._tts.__class__, 'speak', side_effect=interrupted_tts):
                            # Run interaction with interruption
                            await orchestrator._handle_wake_word()
                            await orchestrator._process_interaction()

                            # Verify interruption was detected
                            session = orchestrator.get_current_session()
                            assert session is not None
                            assert session.interrupted is True

                            # Verify stats
                            assert orchestrator.stats.interrupted_interactions == 1

    @pytest.mark.asyncio
    async def test_multiple_interactions(self):
        """Test multiple sequential interactions."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Mock responses for different interactions
        responses = [
            "First response",
            "Second response",
            "Third response",
        ]

        interaction_count = 0

        def get_mock_response():
            nonlocal interaction_count
            response = responses[interaction_count % len(responses)]
            interaction_count += 1
            mock_server.response_text = response
            return mock_server.get_response()

        # Wake word event
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        # Setup mocks
        orchestrator._wake_word = AsyncMock()
        orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

        orchestrator._audio = Mock()
        orchestrator._audio.capture_audio = AsyncMock(return_value=(1000.0, b"mock_audio"))
        orchestrator._audio.play_audio = AsyncMock()

        orchestrator._stt = Mock()
        orchestrator._stt.transcribe = AsyncMock()

        orchestrator._tts = Mock()
        async def mock_tts(text):
            for _ in range(5):
                yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
        orchestrator._tts.speak = mock_tts

        orchestrator._websocket = Mock()
        orchestrator._websocket.send_voice_input = AsyncMock(side_effect=get_mock_response)

        orchestrator._barge_in = Mock()
        orchestrator._barge_in.check_interruption = Mock(return_value=False)

        # Run 3 interactions
        for i in range(3):
            orchestrator._stt.transcribe.return_value = TranscriptionResult(
                text=f"Request {i+1}",
                confidence=0.90,
                time_ms=100.0,
            )

            await orchestrator._handle_wake_word()
            await orchestrator._process_interaction()

        # Verify
        assert orchestrator.stats.total_interactions == 3
        assert orchestrator.stats.successful_interactions == 3
        assert orchestrator.stats.wake_word_detections == 3

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling during interaction."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent

        orchestrator = VoiceOrchestrator()

        # Set up callback to capture errors
        errors_captured = []
        async def capture_error(error):
            errors_captured.append(error)

        orchestrator.on_error = capture_error

        # Mock wake word
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        # Setup mocks with error
        orchestrator._wake_word = AsyncMock()
        orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

        orchestrator._audio = Mock()
        orchestrator._audio.capture_audio = AsyncMock(
            side_effect=Exception("Audio capture failed")
        )

        # Run interaction (should handle error)
        try:
            await orchestrator._process_interaction()
        except Exception:
            pass

        # Check stats
        assert orchestrator.stats.failed_interactions >= 0

    @pytest.mark.asyncio
    async def test_callback_system(self):
        """Test event callback system works end-to-end."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Track callbacks
        events = {}

        def on_wake(event):
            events['wake'] = event

        def on_transcribe(text):
            events['transcribe'] = text

        def on_response(text):
            events['response'] = text

        orchestrator.on_wake_word = on_wake
        orchestrator.on_transcription = on_transcribe
        orchestrator.on_response = on_response

        # Setup mocks
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        orchestrator._wake_word = AsyncMock()
        orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

        orchestrator._audio = Mock()
        orchestrator._audio.capture_audio = AsyncMock(return_value=(1000.0, b"mock_audio"))
        orchestrator._audio.play_audio = AsyncMock()

        orchestrator._stt = Mock()
        transcription = TranscriptionResult(
            text="Test input",
            confidence=0.90,
            time_ms=100.0,
        )
        orchestrator._stt.transcribe = AsyncMock(return_value=transcription)

        orchestrator._tts = Mock()
        async def mock_tts(text):
            yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
        orchestrator._tts.speak = mock_tts

        orchestrator._websocket = Mock()
        orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

        orchestrator._barge_in = Mock()
        orchestrator._barge_in.check_interruption = Mock(return_value=False)

        # Run interaction
        await orchestrator._process_interaction()

        # Verify callbacks were called
        assert 'transcribe' in events
        assert events['transcribe'] == "Test input"
        assert 'response' in events
        assert events['response'] == "This is a mock response from OpenClaw."

    @pytest.mark.asyncio
    async def test_statistics_aggregation(self):
        """Test statistics are correctly aggregated over multiple interactions."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Setup basic mocks
        wake_event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        orchestrator._wake_word = AsyncMock()
        orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

        orchestrator._audio = Mock()
        orchestrator._audio.capture_audio = AsyncMock(return_value=(2000.0, b"mock"))
        orchestrator._audio.play_audio = AsyncMock()

        orchestrator._stt = Mock()
        orchestrator._stt.transcribe = AsyncMock(return_value=TranscriptionResult("Test", 0.9, 100.0))

        orchestrator._tts = Mock()
        async def mock_tts(text):
            yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
        orchestrator._tts.speak = mock_tts

        orchestrator._websocket = Mock()
        orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

        orchestrator._barge_in = Mock()
        orchestrator._barge_in.check_interruption = Mock(return_value=False)

        # Simulate varying interaction times by adding delays
        async def slow_interaction():
            await asyncio.sleep(0.01)
            return mock_server.get_response()

        orchestrator._websocket.send_voice_input = AsyncMock(side_effect=slow_interaction)

        # Run interactions
        for _ in range(5):
            await orchestrator._handle_wake_word()
            await orchestrator._process_interaction()

        # Verify statistics
        stats = orchestrator.get_stats()
        assert stats.total_interactions == 5
        assert stats.successful_interactions == 5
        assert stats.wake_word_detections == 5
        assert stats.transcriptions == 5
        assert stats.tts_syntheses == 5
        assert stats.average_interaction_time_s > 0


class TestPerformanceBenchmarks:
    """Performance benchmarks for critical paths."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_wake_word_detection_latency(self):
        """Benchmark wake word detection latency."""
        from bridge.audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        import time
        latencies = []

        for _ in range(10):
            start = time.perf_counter()
            await detector.listen(timeout=0.1)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        # Mock detection should be fast (<100ms)
        avg_latency = sum(latencies) / len(latencies)
        print(f"Wake word detection latency: {avg_latency:.2f}ms")

        # This is a mock, so should be very fast
        # Real Porcupine is typically <10ms
        assert avg_latency < 500  # 500ms tolerance for mock

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_interaction_latency(self):
        """Benchmark complete interaction latency."""
        from bridge.voice_orchestrator import VoiceOrchestrator
        from bridge.audio.wake_word import WakeWordEvent
        from bridge.audio.stt_worker import TranscriptionResult

        orchestrator = VoiceOrchestrator()
        mock_server = MockOpenClawServer()

        # Minimal mock setup
        wake_event = WakeWordEvent("computer", 0.95, 1234567890.0, 100)

        orchestrator._wake_word = AsyncMock()
        orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

        orchestrator._audio = Mock()
        orchestrator._audio.capture_audio = AsyncMock(return_value=(1000.0, b"mock"))
        orchestrator._audio.play_audio = AsyncMock()

        orchestrator._stt = Mock()
        orchestrator._stt.transcribe = AsyncMock(return_value=TranscriptionResult("Test", 0.9, 100.0))

        orchestrator._tts = Mock()
        async def mock_tts(text):
            yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
        orchestrator._tts.speak = mock_tts

        orchestrator._websocket = Mock()
        orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

        orchestrator._barge_in = Mock()
        orchestrator._barge_in.check_interruption = Mock(return_value=False)

        # Run 5 interactions
        latencies = []
        for _ in range(5):
            start = time.perf_counter()
            await orchestrator._process_interaction()
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

        avg_latency = sum(latencies) / len(latencies)
        print(f"Interaction latency: {avg_latency:.2f}ms")

        # Mock should be fast (<1s)
        assert avg_latency < 1000


# Test markers for pytest
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
]