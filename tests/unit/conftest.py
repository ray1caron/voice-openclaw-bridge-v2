"""Unit test configuration and fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
import numpy as np


@pytest.fixture
def sample_audio_frame():
    """Create a sample audio frame for testing."""
    return np.zeros(480, dtype=np.int16)


@pytest.fixture
def high_energy_audio_frame():
    """Create a high-energy audio frame simulating speech."""
    return np.full(480, 2000, dtype=np.int16)
