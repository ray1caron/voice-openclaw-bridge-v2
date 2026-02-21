"""
Response Filtering Engine

Determines what responses should be spoken vs logged silently.
Supports both explicit message types and heuristic analysis.
"""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import structlog

logger = structlog.get_logger()


class MessageType(Enum):
    """Classification of message types from OpenClaw."""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SYSTEM = "system"
    FINAL_RESPONSE = "final_response"
    CLARIFICATION = "clarification"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ResponseClassification:
    """Result of classifying a response."""
    should_speak: bool
    message_type: MessageType
    confidence: float  # 0.0-1.0 confidence in classification
    reason: str


class ResponseFilter:
    """
    Filters OpenClaw responses to determine what should be spoken.
    
    Strategy:
    1. Check explicit type marker if present (highest priority)
    2. Fall back to heuristic analysis
    3. Default to NOT speaking if uncertain (conservative)
    """
    
    # Patterns that indicate internal thinking/process
    THINKING_PATTERNS = [
        r"^[Ll]et me\b",
        r"^[Ii]'ll\b",
        r"^[Ii]\s+will\b",
        r"^[Ss]earching\b",
        r"^[Ff]etching\b",
        r"^[Cc]hecking\b",
        r"^[Ll]ooking\b",
        r"^[Oo]ne\s+moment",
        r"^[Gg]ive\s+me\s+a\s+second",
        r"^[Hh]ang\s+on",
        r"^Thinking\s*:?\s*$",
    ]
    
    # Patterns that indicate system/log output
    SYSTEM_PATTERNS = [
        r"^\[.*\]",  # [INFO], [DEBUG], etc.
        r"^```",  # Code blocks
        r"^\{.*\}$",  # JSON objects
        r"^\[.*\]$",  # JSON arrays
        r"^Running\s+",
        r"^Executing\s+",
        r"^Tool\s+call\s*:",
        r"^Function\s+call\s*:",
    ]
    
    # Patterns that indicate final responses
    RESPONSE_PATTERNS = [
        r"^[Tt]he\s+",
        r"^[Hh]ere\s+(is|are)\s+",
        r"^[Ii]\s+",  # I think, I found, etc.
        r"^Based\s+on",
        r"^[Yy]es[,.]?\s+",
        r"^[Nn]o[,.]?\s+",
        r"^[Ss]ure[,.]?",
        r"^[Oo]kay[,.]?",
    ]
    
    def __init__(
        self,
        speak_types: Optional[list[str]] = None,
        silence_types: Optional[list[str]] = None,
        heuristic_enabled: bool = True,
    ):
        self.speak_types = set(speak_types or ["final_response", "clarification", "error"])
        self.silence_types = set(silence_types or ["thinking", "tool_call", "tool_result", "system"])
        self.heuristic_enabled = heuristic_enabled
        
        self._thinking_regex = [re.compile(p, re.IGNORECASE) for p in self.THINKING_PATTERNS]
        self._system_regex = [re.compile(p, re.IGNORECASE) for p in self.SYSTEM_PATTERNS]
        self._response_regex = [re.compile(p, re.IGNORECASE) for p in self.RESPONSE_PATTERNS]
    
    def classify(self, message: dict) -> ResponseClassification:
        """
        Classify a message from OpenClaw.
        
        Expected message format:
        {
            "type": "thinking" | "tool_call" | "final_response" | ...,
            "content": "message text",
            "flags": {"speak": bool}  # Optional explicit flag
        }
        """
        # Extract fields with defaults
        msg_type = message.get("type", "unknown")
        content = message.get("content", "")
        flags = message.get("flags", {})
        
        # Priority 1: Explicit speak flag
        if "speak" in flags:
            return ResponseClassification(
                should_speak=flags["speak"],
                message_type=MessageType(msg_type) if msg_type in MessageType else MessageType.UNKNOWN,
                confidence=1.0,
                reason="Explicit speak flag",
            )
        
        # Priority 2: Known message type
        if msg_type in ["final_response", "clarification", "error"]:
            return ResponseClassification(
                should_speak=True,
                message_type=MessageType(msg_type),
                confidence=0.9,
                reason=f"Explicit type: {msg_type}",
            )
        
        if msg_type in ["thinking", "tool_call", "tool_result", "system"]:
            return ResponseClassification(
                should_speak=False,
                message_type=MessageType(msg_type),
                confidence=0.9,
                reason=f"Silent type: {msg_type}",
            )
        
        # Priority 3: Heuristic analysis
        if self.heuristic_enabled and content:
            return self._heuristic_classify(content)
        
        # Priority 4: Default to silent (conservative)
        return ResponseClassification(
            should_speak=False,
            message_type=MessageType.UNKNOWN,
            confidence=0.5,
            reason="Unknown type, defaulting to silent",
        )
    
    def _heuristic_classify(self, content: str) -> ResponseClassification:
        """
        Use regex patterns to classify ambiguous content.
        """
        content_stripped = content.strip()
        
        # Check for system patterns first (strong signal)
        for pattern in self._system_regex:
            if pattern.match(content_stripped):
                return ResponseClassification(
                    should_speak=False,
                    message_type=MessageType.SYSTEM,
                    confidence=0.85,
                    reason="Matches system pattern",
                )
        
        # Check for thinking patterns
        for pattern in self._thinking_regex:
            if pattern.match(content_stripped):
                return ResponseClassification(
                    should_speak=False,
                    message_type=MessageType.THINKING,
                    confidence=0.75,
                    reason="Matches thinking pattern",
                )
        
        # Check for response patterns
        for pattern in self._response_regex:
            if pattern.match(content_stripped):
                return ResponseClassification(
                    should_speak=True,
                    message_type=MessageType.FINAL_RESPONSE,
                    confidence=0.7,
                    reason="Matches response pattern",
                )
        
        # Default: short messages might be filler/clarification
        if len(content_stripped) < 20:
            return ResponseClassification(
                should_speak=True,
                message_type=MessageType.CLARIFICATION,
                confidence=0.6,
                reason="Short message, likely clarification",
            )
        
        # Default: longer messages likely final responses
        return ResponseClassification(
            should_speak=True,
            message_type=MessageType.FINAL_RESPONSE,
            confidence=0.5,
            reason="Default to speak (conservative fallback)",
        )
    
    def should_speak(self, message: dict) -> bool:
        """Quick check: should this message be spoken?"""
        classification = self.classify(message)
        
        logger.debug(
            "Message classified",
            type=classification.message_type.value,
            speak=classification.should_speak,
            confidence=classification.confidence,
            reason=classification.reason,
            content_preview=message.get("content", "")[:50],
        )
        
        return classification.should_speak
