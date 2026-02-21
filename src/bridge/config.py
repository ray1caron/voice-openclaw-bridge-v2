"""Configuration management for Voice-OpenClaw Bridge.

Supports:
- YAML configuration files
- Environment variables
- .env file loading
- Hot-reload via file watching
- Strict validation with Pydantic
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = structlog.get_logger()

# Configuration paths
DEFAULT_CONFIG_DIR = Path.home() / ".voice-bridge"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_ENV_FILE = DEFAULT_CONFIG_DIR / ".env"


class AudioConfig(BaseModel):
    """Audio device configuration."""
    
    input_device: str | int = Field(default="default", description="Input device name or index")
    output_device: str | int = Field(default="default", description="Output device name or index")
    sample_rate: int = Field(default=16000, ge=8000, le=192000)
    channels: int = Field(default=1, ge=1, le=2)
    chunk_size: int = Field(default=1024, ge=256, le=8192)
    
    @field_validator("input_device", "output_device")
    @classmethod
    def validate_device(cls, v: str | int) -> str | int:
        """Validate device is string name or integer index."""
        if isinstance(v, int) and v < -1:
            raise ValueError(f"Device index must be >= -1, got {v}")
        return v


class STTConfig(BaseModel):
    """Speech-to-Text configuration."""
    
    model: str = Field(default="base", description="Whisper model size")
    language: str | None = Field(default=None, description="Language code (auto-detect if None)")
    device: Literal["cpu", "cuda", "auto"] = Field(default="auto")
    compute_type: Literal["int8", "float16", "float32"] = Field(default="int8")
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate Whisper model size."""
        valid = {"tiny", "base", "small", "medium", "large", "large-v2", "large-v3"}
        if v not in valid:
            raise ValueError(f"Invalid model '{v}'. Must be one of: {valid}")
        return v


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""
    
    voice: str = Field(default="en_US-lessac-medium", description="Piper voice model")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)


class OpenClawConfig(BaseModel):
    """OpenClaw connection configuration."""
    
    host: str = Field(default="localhost", description="OpenClaw host")
    port: int = Field(default=8080, ge=1, le=65535)
    secure: bool = Field(default=False, description="Use WSS/HTTPS")
    api_key: str | None = Field(default=None, description="API key if required")
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    
    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v or not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()


class BridgeConfig(BaseModel):
    """Bridge behavior configuration."""
    
    wake_word: str = Field(default="hey hal", description="Wake word phrase")
    response_timeout: float = Field(default=10.0, ge=1.0, le=60.0)
    max_session_duration: float = Field(default=300.0, ge=60.0, le=3600.0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    hot_reload: bool = Field(default=True, description="Enable config file watching")


class AppConfig(BaseSettings):
    """Main application configuration.
    
    Loads from:
    1. Environment variables (highest priority)
    2. .env file
    3. config.yaml file
    4. Default values (lowest priority)
    """
    
    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        validate_assignment=True,
        extra="forbid",  # Strict: fail on unknown fields
    )
    
    # Nested configuration sections
    audio: AudioConfig = Field(default_factory=AudioConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    openclaw: OpenClawConfig = Field(default_factory=OpenClawConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    
    # Internal
    _config_file: Path | None = None
    _watcher: Observer | None = None
    _on_reload: list[callable] = []
    
    @classmethod
    def load(cls, config_path: Path | str | None = None) -> AppConfig:
        """Load configuration from file.
        
        Args:
            config_path: Path to config file. If None, uses default location.
            
        Returns:
            Loaded AppConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist and create_default=False
            ValidationError: If config is invalid (strict mode)
        """
        if config_path is None:
            config_path = DEFAULT_CONFIG_FILE
        else:
            config_path = Path(config_path)
        
        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load from YAML if exists, otherwise use defaults
        if config_path.exists():
            logger.info("Loading configuration", config_file=str(config_path))
            with open(config_path) as f:
                yaml_data = yaml.safe_load(f) or {}
            
            # Create instance with YAML data
            instance = cls(**yaml_data)
        else:
            logger.info("No config file found, using defaults", config_file=str(config_path))
            instance = cls()
            # Create default config file
            instance.save(config_path)
        
        instance._config_file = config_path
        return instance
    
    def save(self, path: Path | str | None = None) -> None:
        """Save configuration to YAML file."""
        if path is None:
            path = self._config_file or DEFAULT_CONFIG_FILE
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save
        config_dict = self.model_dump(exclude={"_config_file", "_watcher", "_on_reload"})
        with open(path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        logger.info("Configuration saved", config_file=str(path))
    
    def start_hot_reload(self) -> None:
        """Start watching config file for changes."""
        if not self.bridge.hot_reload or self._watcher is not None:
            return
        
        config_file = self._config_file or DEFAULT_CONFIG_FILE
        if not config_file.exists():
            logger.warning("Cannot watch config file - does not exist", config_file=str(config_file))
            return
        
        logger.info("Starting config hot-reload watcher", config_file=str(config_file))
        
        class ConfigReloadHandler(FileSystemEventHandler):
            def __init__(self, config: AppConfig):
                self.config = config
                self._debounce_timer = None
            
            def on_modified(self, event):
                if event.src_path == str(config_file):
                    # Debounce rapid changes
                    if self.config._watcher and hasattr(self.config._watcher, '_debounce_timer'):
                        if self.config._watcher._debounce_timer:
                            self.config._watcher._debounce_timer.cancel()
                    
                    import threading
                    def reload():
                        try:
                            logger.info("Config file changed, reloading...")
                            new_config = AppConfig.load(config_file)
                            # Copy over callbacks
                            new_config._on_reload = self.config._on_reload
                            # Update this instance's data
                            for key, value in new_config.model_dump().items():
                                setattr(self.config, key, value)
                            # Notify callbacks
                            for callback in self.config._on_reload:
                                try:
                                    callback()
                                except Exception as e:
                                    logger.error("Config reload callback failed", error=str(e))
                            logger.info("Config reloaded successfully")
                        except Exception as e:
                            logger.error("Config reload failed", error=str(e))
                    
                    timer = threading.Timer(0.5, reload)
                    timer.start()
                    self.config._watcher._debounce_timer = timer
        
        handler = ConfigReloadHandler(self)
        self._watcher = Observer()
        self._watcher.schedule(handler, path=str(config_file.parent), recursive=False)
        self._watcher.start()
    
    def stop_hot_reload(self) -> None:
        """Stop watching config file."""
        if self._watcher:
            logger.info("Stopping config hot-reload watcher")
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None
    
    def on_reload(self, callback: callable) -> None:
        """Register a callback to be called when config is reloaded."""
        self._on_reload.append(callback)


def get_config() -> AppConfig:
    """Get or create the global configuration instance."""
    # This will be replaced with proper singleton management
    return AppConfig.load()
