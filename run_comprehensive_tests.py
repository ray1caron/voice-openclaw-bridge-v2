#!/usr/bin/env python3
"""
Comprehensive test runner for Voice-OpenClaw Bridge v2

Run this script to execute the full test suite and generate a report.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description, timeout=180):
    """Run a command and return results."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*80)
    
    start_time = time.time()
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    elapsed = time.time() - start_time
    
    print(f"\nCompleted in {elapsed:.2f}s")
    print(f"Return code: {result.returncode}")
    
    return result


def main():
    """Run comprehensive tests."""
    script_dir = Path(__file__).parent
    
    print("=" * 80)
    print("    Voice-OpenClaw Bridge v2 - Comprehensive Test Suite")
    print("=" * 80)
    
    # Test 1: Import test
    print("\n\n1. Testing imports...")
    import_test = run_command(
        "python3 -c \"from bridge import *; print('All imports successful')\"",
        "Import all bridge modules",
        timeout=30
    )
    
    if import_test.returncode != 0:
        print("ERROR: Import test failed!")
        print(import_test.stderr)
    else:
        print("✓ Import test passed")
    
    # Test 2: Unit tests - OpenClaw Middleware
    print("\n\n2. Testing OpenClaw Middleware...")
    middleware_test = run_command(
        "python3 -m pytest tests/unit/test_openclaw_middleware.py -v --tb=short",
        "OpenClaw Middleware Unit Tests",
        timeout=60
    )
    
    print(middleware_test.stdout[-2000:] if len(middleware_test.stdout) > 2000 else middleware_test.stdout)
    if middleware_test.stderr:
        print("STDERR:", middleware_test.stderr[-500:])
    
    # Test 3: Unit tests - Tool Chain Manager
    print("\n\n3. Testing Tool Chain Manager...")
    chain_test = run_command(
        "python3 -m pytest tests/unit/test_tool_chain_manager.py -v --tb=short",
        "Tool Chain Manager Unit Tests",
        timeout=60
    )
    
    print(chain_test.stdout[-2000:] if len(chain_test.stdout) > 2000 else chain_test.stdout)
    if chain_test.stderr:
        print("STDERR:", chain_test.stderr[-500:])
    
    # Test 4: Unit tests - Middleware Integration
    print("\n\n4. Testing Middleware Integration...")
    integration_test = run_command(
        "python3 -m pytest tests/unit/test_middleware_integration.py -v --tb=short",
        "Middleware Integration Unit Tests",
        timeout=60
    )
    
    print(integration_test.stdout[-2000:] if len(integration_test.stdout) > 2000 else integration_test.stdout)
    if integration_test.stderr:
        print("STDERR:", integration_test.stderr[-500:])
    
    # Test 5: Unit tests - VAD (fixed)
    print("\n\n5. Testing VAD (with fixes)...")
    vad_test = run_command(
        "python3 -m pytest tests/unit/test_vad.py -v --tb=short",
        "VAD Unit Tests",
        timeout=60
    )
    
    print(vad_test.stdout[-2000:] if len(vad_test.stdout) > 2000 else vad_test.stdout)
    if vad_test.stderr:
        print("STDERR:", vad_test.stderr[-500:])
    
    # Test 6: Full test suite summary
    print("\n\n6. Running full test suite summary...")
    full_test = run_command(
        "python3 -m pytest tests/ --tb=no -q",
        "Full Test Suite Summary",
        timeout=180
    )
    
    print(full_test.stdout)
    if full_test.stderr:
        print("STDERR:", full_test.stderr)
    
    # Summary
    print("\n" + "=" * 80)
    print("                       TEST SUMMARY")
    print("=" * 80)
    
    results = [
        ("Import Test", import_test.returncode == 0),
        ("Middleware Tests", middleware_test.returncode == 0),
        ("Tool Chain Tests", chain_test.returncode == 0),
        ("Integration Tests", integration_test.returncode == 0),
        ("VAD Tests", vad_test.returncode == 0),
    ]
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8} {name}")
    
    print("\n" + "=" * 80)
    
    # Return appropriate exit code
    all_passed = all(r[1] for r in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
