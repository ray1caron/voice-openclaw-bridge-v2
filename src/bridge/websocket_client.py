"""
WebSocket Client for OpenClaw Integration

Handles bidirectional communication with OpenClaw gateway.
Manages connection lifecycle, reconnection, and message routing.
"""
import asyncio
import json
import time
from typing import Callable, Optional

import structlog
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

logger = structlog.get_logger()


class OpenClawWebSocketClient:
    """
    Async WebSocket client for communicating with OpenClaw.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Bidirectional message handling
    - Connection state tracking
    - Message queue for offline buffering
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 3000,
        path: str = "/api/voice",
        reconnect_enabled: bool = True,
        max_retries: int = 5,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
    ):
        self.host = host
        self.port = port
        self.path = path
        self.url = f"ws://{host}:{port}{path}"
        
        # Reconnection settings
        self.reconnect_enabled = reconnect_enabled
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        
        # Connection state
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.session_id: Optional[str] = None
        self._connection_attempts = 0
        
        # Message handlers
        self.on_message: Optional[Callable[[dict], None]] = None
        self.on_connect: Optional[Callable[[], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
        
        # Runtime
        self._receive_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection to OpenClaw.
        Returns True if successful, False otherwise.
        """
        while self._connection_attempts < self.max_retries:
            try:
                logger.info(
                    "Connecting to OpenClaw",
                    url=self.url,
                    attempt=self._connection_attempts + 1,
                    max_retries=self.max_retries,
                )
                
                self.websocket = await websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=10,
                )
                
                self.is_connected = True
                self._connection_attempts = 0
                
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
                
                # Start message receiver
                self._receive_task = asyncio.create_task(
                    self._receive_loop(),
                )
                
                if self.on_connect:
                    self.on_connect()
                
                return True
                
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
                
            except Exception as e:
                logger.error("Unexpected error during connection", error=str(e))
                self._connection_attempts += 1
                break
        
        logger.error(
            "Failed to connect after max retries",
            max_retries=self.max_retries,
        )
        return False
    
    async def disconnect(self):
        """
        Gracefully close the WebSocket connection.
        """
        logger.info("Disconnecting from OpenClaw")
        self._shutdown_event.set()
        self.is_connected = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        if self.on_disconnect:
            self.on_disconnect()
        
        logger.info("Disconnected")
    
    async def send(self, message: dict) -> bool:
        """
        Send a message to OpenClaw.
        Returns True if sent successfully, False otherwise.
        """
        if not self.is_connected or not self.websocket:
            logger.warning("Cannot send, not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug("Message sent", type=message.get("type"))
            return True
        except ConnectionClosed:
            logger.warning("Connection closed while sending")
            self.is_connected = False
            
            if self.reconnect_enabled:
                await self._handle_reconnect()
            
            return False
        except Exception as e:
            logger.error("Error sending message", error=str(e))
            return False
    
    async def send_voice_input(self, text: str, confidence: Optional[float] = None):
        """
        Send transcribed voice input to OpenClaw.
        """
        message = {
            "type": "voice_input",
            "text": text,
            "timestamp": time.time(),
        }
        
        if confidence is not None:
            message["metadata"] = {"confidence": confidence}
        
        return await self.send(message)
    
    async def send_interrupt(self):
        """
        Send interruption signal (user barge-in).
        """
        message = {
            "type": "control",
            "action": "interrupt",
            "timestamp": time.time(),
        }
        return await self.send(message)
    
    async def _receive_loop(self):
        """
        Background task to receive messages from OpenClaw.
        """
        try:
            while not self._shutdown_event.is_set():
                try:
                    message_raw = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=0.1,
                    )
                    
                    message = json.loads(message_raw)
                    logger.debug("Message received", type=message.get("type"))
                    
                    if self.on_message:
                        self.on_message(message)
                
                except asyncio.TimeoutError:
                    continue
                except ConnectionClosed:
                    logger.warning("Connection closed by server")
                    self.is_connected = False
                    
                    if self.reconnect_enabled:
                        await self._handle_reconnect()
                    break
                    
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        except Exception as e:
            logger.error("Error in receive loop", error=str(e))
    
    async def _handle_reconnect(self):
        """
        Handle reconnection after disconnection.
        """
        if not self.reconnect_enabled:
            return
        
        logger.info("Attempting to reconnect")
        self.is_connected = False
        
        if self.on_disconnect:
            self.on_disconnect()
        
        # Wait a bit before reconnecting
        await asyncio.sleep(self.backoff_base)
        
        # Try to reconnect
        success = await self.connect()
        
        if success and self.session_id:
            # Restore session if we have a session ID
            await self._restore_session()
    
    async def _restore_session(self):
        """
        Request session restoration after reconnection.
        """
        if not self.session_id:
            return
        
        message = {
            "type": "session_restore",
            "session_id": self.session_id,
        }
        await self.send(message)
        logger.info("Requested session restoration", session_id=self.session_id)
