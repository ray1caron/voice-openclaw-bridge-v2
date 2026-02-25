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
from bridge.openclaw_middleware import (
    OpenClawMiddleware,
    MessageMetadata,
    TaggedMessage,
    MessageType,
    Speakability,
    mark_tool_call,
    wrap_tool_execution,
)
from bridge.middleware_integration import (
    MiddlewareResponseFilter,
    filter_message,
)
from bridge.tool_chain_manager import (
    ToolChainManager,
    ToolStep,
    ToolChainResult,
    ToolChainState,
    ToolResultStatus,
    execute_tool_chain,
)
from bridge.conversation_store import (
    ConversationStore,
    get_conversation_store,
    get_session_db_path,
)
from bridge.session_manager import (
    SessionManager,
    Session,
    SessionState,
    SessionError,
    get_session_manager,
)
from bridge.history_manager import (
    HistoryManager,
    ConversationTurn,
    ConversationSession,
    get_history_manager,
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
    # OpenClaw Middleware
    "OpenClawMiddleware",
    "MessageMetadata",
    "TaggedMessage",
    "MessageType",
    "Speakability",
    "mark_tool_call",
    "wrap_tool_execution",
    # Middleware Integration
    "MiddlewareResponseFilter",
    "filter_message",
    # Tool Chain Manager
    "ToolChainManager",
    "ToolStep",
    "ToolChainResult",
    "ToolChainState",
    "ToolResultStatus",
    "execute_tool_chain",
    # Sprint 3 - Session Persistence
    "ConversationStore",
    "get_conversation_store",
    "get_session_db_path",
    # Sprint 3 - Session Manager
    "SessionManager",
    "Session",
    "SessionState",
    "SessionError",
    "get_session_manager",
    # Sprint 3 - History Manager
    "HistoryManager",
    "ConversationTurn",
    "ConversationSession",
    "get_history_manager",
]
