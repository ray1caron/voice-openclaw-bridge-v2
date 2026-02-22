"""
Audio Pipeline for Voice Bridge.

Manages audio I/O, voice activity detection, buffering, and barge-in.
Connects microphone input to STT and TTS output to speakers.
"""
import enum
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, List, Dict, Any

import structlog
import numpy as np

from bridge.config import get_config, AudioConfig
from bridge.vad import WebRTCVAD, VADConfig, VADMode, SpeechSegmenter, SpeechSegment
from bridge.audio_buffer import AudioBuffer

logger = structlog.get_logger()

# Optional imports for audio I/O
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    logger.warning("sounddevice not available, audio I/O disabled")


class PipelineState(enum.Enum):
    """Audio pipeline states."""
    IDLE = "idle"                    # Waiting for wake word
    LISTENING = "listening"          # Capturing speech
    PROCESSING = "processing"         # STT/OpenClaw processing
    SPEAKING = "speaking"            # TTS playback
    ERROR = "error"                  # Error state


class AudioDeviceType(enum.Enum):
    """Type of audio device."""
    INPUT = "input"
    OUTPUT = "output"


@dataclass
class AudioDeviceInfo:
    """Information about an audio device."""
    index: int
    name: str
    device_type: AudioDeviceType
    channels: int
    sample_rate: int
    is_default: bool = False


@dataclass
class PipelineStats:
    """Audio pipeline statistics."""
    state_changes: int = 0
    speech_segments_detected: int = 0
    audio_frames_processed: int = 0
    tts_utterances_played: int = 0
    barge_in_count: int = 0
    error_count: int = 0
    start_time: float = 0.0
    
    @property
    def uptime_seconds(self) -> float:
        """Get pipeline uptime in seconds."""
        if self.start_time == 0:
            return 0
        return time.time() - self.start_time


class AudioDeviceManager:
    """
    Manages audio device discovery and selection.
    
    Handles device enumeration, selection by name/index,
    and provides device information.
    """
    
    def __init__(self):
        """Initialize device manager."""
        self._devices: Dict[int, AudioDeviceInfo] = {}
        self._refresh_devices()
    
    def _refresh_devices(self):
        """Refresh device list from sounddevice."""
        self._devices.clear()
        
        if not SOUNDDEVICE_AVAILABLE:
            logger.warning("sounddevice not available, no devices found")
            return
        
        try:
            # Get all devices
            devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')
            default_output = sd.query_devices(kind='output')
            
            for idx, device in enumerate(devices):
                # Determine device type
                max_input = device.get('max_input_channels', 0)
                max_output = device.get('max_output_channels', 0)
                
                if max_input > 0:
                    device_type = AudioDeviceType.INPUT
                    channels = max_input
                    is_default = (device == default_input)
                elif max_output > 0:
                    device_type = AudioDeviceType.OUTPUT
                    channels = max_output
                    is_default = (device == default_output)
                else:
                    continue
                
                info = AudioDeviceInfo(
                    index=idx,
                    name=device['name'],
                    device_type=device_type,
                    channels=channels,
                    sample_rate=int(device.get('default_samplerate', 16000)),
                    is_default=is_default
                )
                self._devices[idx] = info
            
            logger.info(
                "devices_refreshed",
                input_count=sum(1 for d in self._devices.values() if d.device_type == AudioDeviceType.INPUT),
                output_count=sum(1 for d in self._devices.values() if d.device_type == AudioDeviceType.OUTPUT)
            )
            
        except Exception as e:
            logger.error("device_refresh_failed", error=str(e))
    
    def list_devices(self, device_type: Optional[AudioDeviceType] = None) -> List[AudioDeviceInfo]:
        """
        List available audio devices.
        
        Args:
            device_type: Filter by type (input/output) or None for all
            
        Returns:
            List of device information
        """
        devices = list(self._devices.values())
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        return sorted(devices, key=lambda d: (not d.is_default, d.name))
    
    def get_device(self, identifier: str or int, device_type: AudioDeviceType) -> Optional[AudioDeviceInfo]:
        """
        Get device by index or name.
        
        Args:
            identifier: Device index (int) or name (str)
            device_type: Expected device type
            
        Returns:
            Device info or None if not found
        """
        if isinstance(identifier, int):
            device = self._devices.get(identifier)
            if device and device.device_type == device_type:
                return device
        else:
            # Search by name (case-insensitive, partial match)
            identifier_lower = identifier.lower()
            for device in self._devices.values():
                if (device.device_type == device_type and 
                    identifier_lower in device.name.lower()):
                    return device
        return None
    
    def get_default_device(self, device_type: AudioDeviceType) -> Optional[AudioDeviceInfo]:
        """
        Get default device for type.
        
        Args:
            device_type: Input or output
            
        Returns:
            Default device info or None
        """
        for device in self._devices.values():
            if device.device_type == device_type and device.is_default:
                return device
        return None


class AudioPipeline:
    """
    Main audio pipeline managing I/O, VAD, and barge-in.
    
    Coordinates audio capture, voice activity detection, buffering,
    and playback with support for interruption (barge-in).
    """
    
    def __init__(
        self,
        audio_config: Optional[AudioConfig] = None,
        vad_config: Optional[VADConfig] = None
    ):
        """
        Initialize audio pipeline.
        
        Args:
            audio_config: Audio configuration (loads from config if None)
            vad_config: VAD configuration (uses defaults if None)
        """
        # Load configuration
        if audio_config is None:
            config = get_config()
            audio_config = config.audio
        
        self.audio_config = audio_config
        self.vad_config = vad_config or VADConfig()
        
        # Initialize components
        self.device_manager = AudioDeviceManager()
        self.vad = WebRTCVAD(self.vad_config)
        self.segmenter = SpeechSegmenter(self.vad, self.vad_config)
        
        # Audio buffers
        self.input_buffer = AudioBuffer(
            max_frames=50,
            frame_size=int(
                self.audio_config.sample_rate * self.vad_config.frame_duration_ms / 1000
            )
        )
        self.output_buffer = AudioBuffer(
            max_frames=20,
            frame_size=1024  # TTS frame size
        )
        
        # State
        self._state = PipelineState.IDLE
        self._state_lock = threading.RLock()
        self._state_callbacks: List[Callable[[PipelineState, PipelineState], None]] = []
        
        # Audio I/O
        self._input_stream = None
        self._output_stream = None
        self._input_device = None
        self._output_device = None
        
        # Barge-in
        self._barge_in_enabled = True
        self._is_speaking = False
        self._barge_in_lock = threading.Lock()
        
        # Statistics
        self._stats = PipelineStats(start_time=time.time())
        
        logger.info(
            "audio_pipeline_initialized",
            sample_rate=self.audio_config.sample_rate,
            vad_mode=self.vad_config.mode.name,
            barge_in=self._barge_in_enabled
        )
    
    @property
    def state(self) -> PipelineState:
        """Get current pipeline state."""
        with self._state_lock:
            return self._state
    
    def _set_state(self, new_state: PipelineState):
        """Set pipeline state and notify callbacks."""
        with self._state_lock:
            old_state = self._state
            if old_state != new_state:
                self._state = new_state
                self._stats.state_changes += 1
                logger.info(
                    "pipeline_state_changed",
                    old=old_state.value,
                    new=new_state.value
                )
                
                # Notify callbacks
                for callback in self._state_callbacks:
                    try:
                        callback(old_state, new_state)
                    except Exception as e:
                        logger.error("state_callback_error", error=str(e))
    
    def add_state_callback(self, callback: Callable[[PipelineState, PipelineState], None]):
        """Add callback for state changes."""
        self._state_callbacks.append(callback)
    
    def remove_state_callback(self, callback: Callable[[PipelineState, PipelineState], None]):
        """Remove state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)
    
    @property
    def stats(self) -> PipelineStats:
        """Get pipeline statistics."""
        return self._stats
    
    def initialize_devices(
        self,
        input_device: Optional[str or int] = None,
        output_device: Optional[str or int] = None
    ) -> bool:
        """
        Initialize audio input/output devices.
        
        Args:
            input_device: Input device name or index (uses config default if None)
            output_device: Output device name or index (uses config default if None)
            
        Returns:
            True if both devices initialized successfully
        """
        # Resolve devices
        if input_device is None:
            input_device = getattr(self.audio_config, 'input_device', None)
        if output_device is None:
            output_device = getattr(self.audio_config, 'output_device', None)
        
        # Get input device
        if input_device is not None:
            self._input_device = self.device_manager.get_device(
                input_device, AudioDeviceType.INPUT
            )
        if self._input_device is None:
            self._input_device = self.device_manager.get_default_device(
                AudioDeviceType.INPUT
            )
        
        # Get output device
        if output_device is not None:
            self._output_device = self.device_manager.get_device(
                output_device, AudioDeviceType.OUTPUT
            )
        if self._output_device is None:
            self._output_device = self.device_manager.get_default_device(
                AudioDeviceType.OUTPUT
            )
        
        if self._input_device is None:
            logger.error("no_input_device_found")
            return False
        if self._output_device is None:
            logger.error("no_output_device_found")
            return False
        
        logger.info(
            "devices_initialized",
            input_device=self._input_device.name,
            input_index=self._input_device.index,
            output_device=self._output_device.name,
            output_index=self._output_device.index
        )
        
        return True
    
    def start_capture(self) -> bool:
        """
        Start audio capture from input device.
        
        Returns:
            True if capture started successfully
        """
        if not SOUNDDEVICE_AVAILABLE:
            logger.error("sounddevice_not_available")
            return False
        
        if self._input_device is None:
            logger.error("no_input_device_initialized")
            return False
        
        try:
            frame_size = int(
                self.audio_config.sample_rate * self.vad_config.frame_duration_ms / 1000
            )
            
            self._input_stream = sd.InputStream(
                device=self._input_device.index,
                channels=1,
                samplerate=self.audio_config.sample_rate,
                blocksize=frame_size,
                dtype=np.int16,
                callback=self._audio_input_callback
            )
            
            self._input_stream.start()
            self._set_state(PipelineState.LISTENING)
            
            logger.info("audio_capture_started", frame_size=frame_size)
            return True
            
        except Exception as e:
            logger.error("audio_capture_start_failed", error=str(e))
            self._set_state(PipelineState.ERROR)
            return False
    
    def stop_capture(self):
        """Stop audio capture."""
        if self._input_stream:
            try:
                self._input_stream.stop()
                self._input_stream.close()
                logger.info("audio_capture_stopped")
            except Exception as e:
                logger.error("audio_capture_stop_error", error=str(e))
            finally:
                self._input_stream = None
                
        if self.state == PipelineState.LISTENING:
            self._set_state(PipelineState.IDLE)
    
    def _audio_input_callback(self, indata, frames, time_info, status):
        """
        Callback for audio input stream.
        
        Called by sounddevice on each audio block.
        """
        if status:
            logger.warning("audio_input_status", status=str(status))
        
        # Convert to mono if needed
        if indata.shape[1] > 1:
            audio_frame = indata.mean(axis=1).astype(np.int16)
        else:
            audio_frame = indata[:, 0].astype(np.int16)
        
        # Write to input buffer
        self.input_buffer.write(audio_frame, block=False)
        self._stats.audio_frames_processed += 1
        
        # Process through segmenter if listening
        if self.state == PipelineState.LISTENING:
            segment = self.segmenter.process_frame(audio_frame)
            if segment:
                self._stats.speech_segments_detected += 1
                self._on_speech_segment(segment)
    
    def _on_speech_segment(self, segment: SpeechSegment):
        """
        Handle detected speech segment.
        
        Called when VAD detects end of speech.
        Override or connect callback for custom handling.
        """
        logger.info(
            "speech_segment_ready",
            duration_ms=segment.duration_ms,
            confidence=segment.confidence
        )
        # Subclasses can override this or use callbacks
    
    def start_playback(self) -> bool:
        """
        Start audio playback to output device.
        
        Returns:
            True if playback started successfully
        """
        if not SOUNDDEVICE_AVAILABLE:
            logger.error("sounddevice_not_available")
            return False
        
        if self._output_device is None:
            logger.error("no_output_device_initialized")
            return False
        
        try:
            self._output_stream = sd.OutputStream(
                device=self._output_device.index,
                channels=1,
                samplerate=self.audio_config.sample_rate,
                blocksize=1024,
                dtype=np.int16,
                callback=self._audio_output_callback
            )
            
            self._output_stream.start()
            logger.info("audio_playback_started")
            return True
            
        except Exception as e:
            logger.error("audio_playback_start_failed", error=str(e))
            return False
    
    def stop_playback(self):
        """Stop audio playback."""
        if self._output_stream:
            try:
                self._output_stream.stop()
                self._output_stream.close()
                logger.info("audio_playback_stopped")
            except Exception as e:
                logger.error("audio_playback_stop_error", error=str(e))
            finally:
                self._output_stream = None
    
    def _audio_output_callback(self, outdata, frames, time_info, status):
        """
        Callback for audio output stream.
        
        Called by sounddevice when it needs more audio data.
        """
        if status:
            logger.warning("audio_output_status", status=str(status))
        
        # Try to read from output buffer
        frame = self.output_buffer.read(block=False)
        
        if frame is not None:
            # Ensure correct size
            if len(frame) >= frames:
                outdata[:, 0] = frame[:frames]
            else:
                outdata[:len(frame), 0] = frame
                outdata[len(frame):, 0] = 0  # Zero padding
        else:
            # Output silence
            outdata.fill(0)
    
    def play_audio(self, audio_data: np.ndarray) -> bool:
        """
        Queue audio data for playback.
        
        Args:
            audio_data: Audio samples as numpy array (int16)
            
        Returns:
            True if audio was queued successfully
        """
        if self.state == PipelineState.ERROR:
            logger.error("cannot_play_audio_in_error_state")
            return False
        
        # Split into frames
        frame_size = 1024  # TTS frame size
        frames = [
            audio_data[i:i+frame_size]
            for i in range(0, len(audio_data), frame_size)
        ]
        
        # Queue frames
        queued = 0
        for frame in frames:
            if self.output_buffer.write(frame, block=False):
                queued += 1
        
        if queued > 0:
            self._set_state(PipelineState.SPEAKING)
            self._is_speaking = True
            self._stats.tts_utterances_played += 1
            logger.info("audio_queued_for_playback", frames=queued)
            return True
        else:
            logger.warning("failed_to_queue_audio")
            return False
    
    def stop_playback_immediate(self):
        """Immediately stop playback (barge-in)."""
        with self._barge_in_lock:
            if self._is_speaking:
                logger.info("barge_in_triggered")
                self.output_buffer.clear()
                self._is_speaking = False
                self._stats.barge_in_count += 1
                self._set_state(PipelineState.LISTENING)
    
    def enable_barge_in(self, enabled: bool = True):
        """Enable or disable barge-in capability."""
        self._barge_in_enabled = enabled
        logger.info("barge_in_toggled", enabled=enabled)
    
    def start(self) -> bool:
        """
        Start the audio pipeline.
        
        Initializes devices and starts capture/playback.
        
        Returns:
            True if started successfully
        """
        logger.info("starting_audio_pipeline")
        
        # Initialize devices
        if not self.initialize_devices():
            self._set_state(PipelineState.ERROR)
            return False
        
        # Start playback first (so it's ready)
        if not self.start_playback():
            logger.warning("playback_start_failed")
        
        # Start capture
        if not self.start_capture():
            self._set_state(PipelineState.ERROR)
            return False
        
        logger.info("audio_pipeline_started")
        return True
    
    def stop(self):
        """Stop the audio pipeline."""
        logger.info("stopping_audio_pipeline")
        
        self.stop_capture()
        self.stop_playback()
        
        self._set_state(PipelineState.IDLE)
        logger.info("audio_pipeline_stopped")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
