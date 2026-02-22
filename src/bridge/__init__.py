"""Voice-OpenClaw Bridge v2.

Bidirectional voice interface for OpenClaw.
"""

__version__ = "0.1.0"

from bridge.config import AppConfig, get_config, reload_config
from bridge.audio_discovery import AudioDiscovery, run_discovery, print_discovery_report
from bridge.response_filter import (
    ResponseFilter,
    ResponseFilterManager,
    ResponseType,
    FilterDecision,
    FilteredMessage,
)
from bridge.audio_buffer import AudioBuffer
from bridge.vad import (
    WebRTCVAD,
    VADConfig,
    VADMode,
    VADState,
    SpeechSegmenter,
    SpeechSegment,
    MockVAD,
)
from bridge.audio_pipeline import (
    AudioPipeline,
    AudioDeviceManager,
    AudioDeviceInfo,
    AudioDeviceType,
    PipelineState,
    PipelineStats,
)

__all__ = [
    "AppConfig",
    "get_config",
    "reload_config",
    "AudioDiscovery",
    "run_discovery",
    "print_discovery_report",
    "ResponseFilter",
    "ResponseFilterManager",
    "ResponseType",
    "FilterDecision",
    "FilteredMessage",
    "AudioBuffer",
    "WebRTCVAD",
    "VADConfig",
    "VADMode",
    "VADState",
    "SpeechSegmenter",
    "SpeechSegment",
    "MockVAD",
    "AudioPipeline",
    "AudioDeviceManager",
    "AudioDeviceInfo",
    "AudioDeviceType",
    "PipelineState",
    "PipelineStats",
]
