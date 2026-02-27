"""Run E2E tests with proper Python path."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now run pytest
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main([__file__.replace("run_e2e.py", "integration/test_voice_e2e.py"), "-v", "--tb=short"]))