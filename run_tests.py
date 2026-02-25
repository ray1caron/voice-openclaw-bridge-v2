#!/usr/bin/env python3
"""
Test runner to identify failing tests.
"""
import subprocess
import sys

def run_tests():
    """Run pytest and capture output."""
    # Run all tests with verbose output
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=180
    )
    
    print("=" * 80)
    print("STDOUT:")
    print("=" * 80)
    print(result.stdout)
    
    print("\n" + "=" * 80)
    print("STDERR:")
    print("=" * 80)
    print(result.stderr)
    
    print("\n" + "=" * 80)
    print(f"Return code: {result.returncode}")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
