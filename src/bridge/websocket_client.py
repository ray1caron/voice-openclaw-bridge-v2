"""
WebSocket Client for OpenClaw Integration

Handles bidirectional communication with OpenClaw gateway.
Manages connection lifecycle, reconnection, and message protocol validation.
"""
import asyncio
import enum
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

import structlog
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

from bridge.config import get_config, OpenClawConfig

logger = structlog.get_logger()


class ConnectionState(enum.Enum):
    """WebSocket connection state machine states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessageType(enum.Enum):
    """Valid message types for OpenClaw protocol."""
    VOICE_INPUT = "voice_input"
    CONTROL = "control"
    SESSION_RESTORE = "session_restore"
    PING = "ping"
    PONG = "pong"


class ControlAction(enum.Enum):
    """Valid control actions."""
    INTERRUPT = "interrupt"
    MUTE = "mute"
    UNMUTE = "unmute"


@dataclass
class ConnectionStats:
    """Connection statistics."""
    connect_attempts: int = 0
    successful_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    reconnections: int = 0
    last_connect_time: Optional[float] = None
    last_disconnect_time: Optional[float] = None
    total_uptime: float = 0.0


class MessageValidator:
    """Validates WebSocket messages against protocol schema."""
    
    @staticmethod
    def validate_message(message: dict) -> tuple[bool, Optional[str]]:
        """
        Validate a message conforms to protocol.
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(message, dict):
            return False, "Message must be a dictionary"
        
        msg_type = message.get("type")
        if not msg_type:
            return False, "Message must have 'type' field"
        
        # Validate type is known
        try:
            MessageType(msg_type)
        except ValueError:
            return False, f"Unknown message type: {msg_type}"
        
        # Type-specific validation
        if msg_type == MessageType.VOICE_INPUT.value:
            return MessageValidator._validate_voice_input(message)
        elif msg_type == MessageType.CONTROL.value:
            return MessageValidator._validate_control(message)
        elif msg_type == MessageType.SESSION_RESTORE.value:
            return MessageValidator._validate_session_restore(message)
        elif msg_type in (MessageType.PING.value, MessageType.PONG.value):
            return True, None
        
        return True, None
    
    @staticmethod
    def _validate_voice_input(message: dict) -> tuple[bool, Optional[str]]:
        """Validate voice_input message."""
        text = message.get("text")
        if not text:
            return False, "voice_input requires 'text' field"
        if not isinstance(text, str):
            return False, "'text' must be a string"
        if not text.strip():
            return False, "'text' cannot be empty"
        
        # Validate metadata if present
        metadata = message.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            return False, "'metadata' must be a dictionary"
        
        return True, None
    
    @staticmethod
    def _validate_control(message: dict) -> tuple[bool, Optional[str]]:
        """Validate control message."""
        action = message.get("action")
        if not action:
            return False, "control requires 'action' field"
        
        try:
            ControlAction(action)
        except ValueError:
            valid = [a.value for a in ControlAction]
            return False, f"Invalid action '{action}'. Valid: {valid}"
        
        return True, None
    
    @staticmethod
    def _validate_session_restore(message: dict) -> tuple[bool, Optional[str]]:
        """Validate session_restore message."""
        session_id = message.get("session_id")
        if not session_id:
            return False, "session_restore requires 'session_id' field"
        if not isinstance(session_id, str):
            return False, "'session_id' must be a string"
        
        return True, None


class OpenClawWebSocketClient:
    """
    Async WebSocket client for communicating with OpenClaw.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Connection state machine with detailed tracking
    - Bidirectional message handling with protocol validation
    - Integration with config system
    - Connection statistics
    """
    
    def __init__(
        self,
        config: Optional[OpenClawConfig] = None,
        on_message: Optional[Callable[[dict], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        on_state_change: Optional[Callable[[ConnectionState, ConnectionState], None]] = None,
    ):
        # Use provided config or load from system
        self.config = config or get_config().openclaw
        
        # Build URL from config
        protocol = "wss" if self.config.secure else "ws"
        self.url = f"{protocol}://{self.config.host}:{self.config.port}/api/voice"
        
        # Reconnection settings
        self.max_retries = 5
        self.backoff_base = 1.0
        self.backoff_max = 30.0
        
        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self._connection_attempts = 0
        self.stats = ConnectionStats()
        
        # Message handlers
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_state_change = on_state_change
        
        # Runtime
        self._receive_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._ping_task: Optional[asyncio.Task] = None
        
        logger.info(
            "WebSocket client initialized",
            url=self.url,
            host=self.config.host,
            port=self.config.port,
            secure=self.config.secure,
        )
    
    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state
    
    def _set_state(self, new_state: ConnectionState) -> None:
        """Set connection state and notify observers."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            logger.info(
                "Connection state changed",
                old_state=old_state.value,
                new_state=new_state.value,
            )
            if self.on_state_change:
                try:
                    self.on_state_change(old_state, new_state)
                except Exception as e:
                    logger.error("State change callback failed", error=str(e))
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection to OpenClaw.
        Returns True if successful, False otherwise.
        """
        if self._state in (ConnectionState.CONNECTING, ConnectionState.CONNECTED):
            logger.warning("Already connecting or connected")
            return self.is_connected
        
        self._set_state(ConnectionState.CONNECTING)
        self._shutdown_event.clear()
        
        while self._connection_attempts < self.max_retries:
            self.stats.connect_attempts += 1
            
            try:
                logger.info(
                    "Connecting to OpenClaw",
                    url=self.url,
                    attempt=self._connection_attempts + 1,
                    max_retries=self.max_retries,
                )
                
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.url,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=self.config.timeout,
                    ),
                    timeout=self.config.timeout,
                )
                
                self._connection_attempts = 0
                self.stats.successful_connections += 1
                self.stats.last_connect_time = time.time()
                self._set_state(ConnectionState.CONNECTED)
                
                # Get session ID from welcome message
                welcome = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=5.0
                )
                welcome_data = json.loads(welcome)
                self.session_id = welcome_data.get("session_id")
                
                logger.info(
                    "Connected to OpenClaw",
                    session_id=self.session_id,
                )
                
                # Start background tasks
                self._receive_task = asyncio.create_task(
                    self._receive_loop(),
                    name="websocket_receive",
                )
                self._ping_task = asyncio.create_task(
                    self._ping_loop(),
                    name="websocket_ping",
                )
                
                if self.on_connect:
                    try:
                        self.on_connect()
                    except Exception as e:
                        logger.error("Connect callback failed", error=str(e))
                
                return True
                
            except asyncio.TimeoutError:
                self._connection_attempts += 1
                wait_time = min(
                    self.backoff_base * (2 ** self._connection_attempts),
                    self.backoff_max,
                )
                
                logger.warning(
                    "Connection timeout, retrying",
                    attempt=self._connection_attempts,
                    wait_seconds=wait_time,
                )
                
                if self._connection_attempts < self.max_retries:
                    await asyncio.sleep(wait_time)
                    self._set_state(ConnectionState.RECONNECTING)
                    
            except (ConnectionRefusedError, InvalidStatusCode) as e:
                self._connection_attempts += 1
                wait_time = min(
                    self.backoff_base * (2 ** self._connection_attempts),
                    self.backoff_max,
                )
                
                logger.warning(
                    "Connection failed, retrying",
                    error=str(e),
                    attempt=self._connection_attempts,
                    wait_seconds=wait_time,
                )
                
                if self._connection_attempts < self.max_retries:
                    await asyncio.sleep(wait_time)
                    self._set_state(ConnectionState.RECONNECTING)
                
            except Exception as e:
                logger.error("Unexpected error during connection", error=str(e))
                self._connection_attempts += 1
                self._set_state(ConnectionState.ERROR)
                break
        
        logger.error(
            "Failed to connect after max retries",
            max_retries=self.max_retries,
        )
        self._set_state(ConnectionState.DISCONNECTED)
        return False
    
    async def disconnect(self) -> None:
        """
        Gracefully close the WebSocket connection.
        """
        logger.info("Disconnecting from OpenClaw")
        self._shutdown_event.set()
        
        # Update stats
        if self.stats.last_connect_time:
            session_duration = time.time() - self.stats.last_connect_time
            self.stats.total_uptime += session_duration
        self.stats.last_disconnect_time = time.time()
        
        # Cancel background tasks
        tasks = [self._receive_task, self._ping_task]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._receive_task = None
        self._ping_task = None
        
        # Close websocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug("Error closing websocket", error=str(e))
            self.websocket = None
        
        self._set_state(ConnectionState.DISCONNECTED)
        
        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                logger.error("Disconnect callback failed", error=str(e))
        
        logger.info("Disconnected")
    
    async def send(self, message: dict) -> bool:
        """
        Send a message to OpenClaw with protocol validation.
        Returns True if sent successfully, False otherwise.
        """
        # Validate message
        is_valid, error = MessageValidator.validate_message(message)
        if not is_valid:
            logger.error("Invalid message", error=error, message=message)
            return False
        
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send, not connected", state=self._state.value)
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            self.stats.messages_sent += 1
            logger.debug("Message sent", type=message.get("type"))
            return True
            
        except ConnectionClosed:
            logger.warning("Connection closed while sending")
            self._set_state(ConnectionState.DISCONNECTED)
            
            if self.on_disconnect:
                try:
                    self.on_disconnect()
                except Exception as e:
                    logger.error("Disconnect callback failed", error=str(e))
            
            return False
            
        except Exception as e:
            logger.error("Error sending message", error=str(e))
            return False
    
    async def send_voice_input(self, text: str, confidence: Optional[float] = None) -> bool:
        """
        Send transcribed voice input to OpenClaw.
        """
        message = {
            "type": MessageType.VOICE_INPUT.value,
            "text": text,
            "timestamp": time.time(),
        }
        
        if confidence is not None:
            message["metadata"] = {"confidence": confidence}
        
        return await self.send(message)
    
    async def send_interrupt(self) -> bool:
        """
        Send interruption signal (user barge-in).
        """
        message = {
            "type": MessageType.CONTROL.value,
            "action": ControlAction.INTERRUPT.value,
            "timestamp": time.time(),
        }
        return await self.send(message)
    
    async def send_control(self, action: ControlAction, data: Optional[dict] = None) -> bool:
        """
        Send control message.
        """
        message = {
            "type": MessageType.CONTROL.value,
            "action": action.value,
            "timestamp": time.time(),
        }
        if data:
            message["data"] = data
        return await self.send(message)
    
    async def _receive_loop(self) -> None:
        """
        Background task to receive messages from OpenClaw.
        """
        try:
            while not self._shutdown_event.is_set():
                try:
                    message_raw = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=1.0,
                    )
                    
                    message = json.loads(message_raw)
                    self.stats.messages_received += 1
                    logger.debug("Message received", type=message.get("type"))
                    
                    if self.on_message:
                        try:
                            self.on_message(message)
                        except Exception as e:
                            logger.error("Message callback failed", error=str(e))
                
                except asyncio.TimeoutError:
                    continue
                    
                except ConnectionClosed as e:
                    logger.warning(
                        "Connection closed by server",
                        code=e.code,
                        reason=e.reason,
                    )
                    self._set_state(ConnectionState.DISCONNECTED)
                    break
                    
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        except Exception as e:
            logger.error("Error in receive loop", error=str(e))
            self._set_state(ConnectionState.ERROR)
    
    async def _ping_loop(self) -> None:
        """
        Send periodic pings to keep connection alive.
        """
        try:
            while not self._shutdown_event.is_set():
                await asyncio.sleep(30)
                if self.is_connected:
                    ping_msg = {
                        "type": MessageType.PING.value,
                        "timestamp": time.time(),
                    }
                    try:
                        await self.send(ping_msg)
                    except Exception as e:
                        logger.debug("Ping failed", error=str(e))
        except asyncio.CancelledError:
            logger.debug("Ping loop cancelled")
            raise
    
    async def restore_session(self, session_id: Optional[str] = None) -> bool:
        """
        Request session restoration.
        """
        sid = session_id or self.session_id
        if not sid:
            logger.warning("No session ID to restore")
            return False
        
        message = {
            "type": MessageType.SESSION_RESTORE.value,
            "session_id": sid,
        }
        
        success = await self.send(message)
        if success:
            self.session_id = sid
            logger.info("Requested session restoration", session_id=sid)
        return success
    
    def get_stats(self) -> dict[str, Any]:
        """Get connection statistics as dictionary."""
        return {
            "state": self._state.value,
            "session_id": self.session_id,
            "connect_attempts": self.stats.connect_attempts,
            "successful_connections": self.stats.successful_connections,
            "messages_sent": self.stats.messages_sent,
            "messages_received": self.stats.messages_received,
            "reconnections": self.stats.reconnections,
            "last_connect_time": self.stats.last_connect_time,
            "last_disconnect_time": self.stats.last_disconnect_time,
            "total_uptime": self.stats.total_uptime,
        }
