"""
Thread-safe ring buffer for audio streaming.

Provides producer/consumer pattern for continuous audio I/O
with overflow/underflow handling.
"""
import threading
from collections import deque
from typing import Optional, List

import structlog
import numpy as np

logger = structlog.get_logger()


class AudioBuffer:
    """
    Thread-safe ring buffer for audio streaming.
    
    Supports multiple producers and consumers with configurable
    overflow behavior and frame-based operations.
    """
    
    def __init__(
        self,
        max_frames: int = 20,
        frame_size: int = 480,  # 30ms @ 16kHz
        dtype: np.dtype = np.int16
    ):
        """
        Initialize audio buffer.
        
        Args:
            max_frames: Maximum number of frames to store
            frame_size: Samples per frame
            dtype: NumPy data type for audio samples
        """
        self.max_frames = max_frames
        self.frame_size = frame_size
        self.dtype = dtype
        
        # Thread-safe buffer using deque
        self._buffer: deque = deque(maxlen=max_frames)
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
        
        # Statistics
        self._overflow_count = 0
        self._underflow_count = 0
        self._total_written = 0
        self._total_read = 0
        
        logger.info(
            "audio_buffer_initialized",
            max_frames=max_frames,
            frame_size=frame_size,
            dtype=str(dtype)
        )
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        with self._lock:
            return len(self._buffer) == 0
    
    @property
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        with self._lock:
            return len(self._buffer) >= self.max_frames
    
    @property
    def frame_count(self) -> int:
        """Get current number of frames in buffer."""
        with self._lock:
            return len(self._buffer)
    
    @property
    def stats(self) -> dict:
        """Get buffer statistics."""
        with self._lock:
            return {
                "overflow_count": self._overflow_count,
                "underflow_count": self._underflow_count,
                "total_written": self._total_written,
                "total_read": self._total_read,
                "current_frames": len(self._buffer),
                "max_frames": self.max_frames
            }
    
    def write(self, frame: np.ndarray, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Write a frame to the buffer.
        
        Args:
            frame: Audio frame as numpy array
            block: If True, wait until space available
            timeout: Max seconds to wait if blocking
            
        Returns:
            True if frame was written, False if dropped
        """
        # Validate frame
        if frame.shape[0] != self.frame_size:
            logger.warning(
                "frame_size_mismatch",
                expected=self.frame_size,
                actual=frame.shape[0]
            )
            # Pad or truncate
            if frame.shape[0] < self.frame_size:
                frame = np.pad(frame, (0, self.frame_size - frame.shape[0]))
            else:
                frame = frame[:self.frame_size]
        
        with self._not_full:
            # Check if we need to wait
            if self.is_full:
                if not block:
                    self._overflow_count += 1
                    logger.debug("buffer_overflow_frame_dropped")
                    return False
                
                # Wait for space
                if not self._not_full.wait(timeout=timeout):
                    self._overflow_count += 1
                    logger.warning("buffer_write_timeout")
                    return False
            
            # Write frame
            self._buffer.append(frame.copy())
            self._total_written += 1
            self._not_empty.notify()
            
            logger.debug("frame_written", frame_count=len(self._buffer))
            return True
    
    def read(self, block: bool = True, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """
        Read a frame from the buffer.
        
        Args:
            block: If True, wait until data available
            timeout: Max seconds to wait if blocking
            
        Returns:
            Audio frame or None if timeout/empty
        """
        with self._not_empty:
            if self.is_empty:
                if not block:
                    self._underflow_count += 1
                    logger.debug("buffer_underflow")
                    return None
                
                if not self._not_empty.wait(timeout=timeout):
                    self._underflow_count += 1
                    logger.debug("buffer_read_timeout")
                    return None
            
            # Read frame
            frame = self._buffer.popleft()
            self._total_read += 1
            self._not_full.notify()
            
            logger.debug("frame_read", remaining=len(self._buffer))
            return frame
    
    def read_multiple(self, count: int, block: bool = True, timeout: Optional[float] = None) -> List[np.ndarray]:
        """
        Read multiple frames at once.
        
        Args:
            count: Number of frames to read
            block: If True, wait for all frames
            timeout: Max seconds to wait per frame
            
        Returns:
            List of frames (may be fewer than requested if non-blocking)
        """
        frames = []
        for _ in range(count):
            frame = self.read(block=block, timeout=timeout)
            if frame is None:
                break
            frames.append(frame)
        return frames
    
    def clear(self) -> int:
        """
        Clear all frames from buffer.
        
        Returns:
            Number of frames cleared
        """
        with self._lock:
            count = len(self._buffer)
            self._buffer.clear()
            self._not_full.notify_all()
            logger.info("buffer_cleared", frames_cleared=count)
            return count
    
    def peek(self) -> Optional[np.ndarray]:
        """
        Peek at next frame without removing it.
        
        Returns:
            Next frame or None if empty
        """
        with self._lock:
            if self._buffer:
                return self._buffer[0].copy()
            return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - clears buffer."""
        self.clear()
        return False
