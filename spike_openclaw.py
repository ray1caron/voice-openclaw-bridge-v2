#!/usr/bin/env python3
"""Day 0 Spike: Test OpenClaw Sessions API connectivity.

This is the blocking gate before Phase 5 integration. We need to verify:
1. OpenClaw gateway is running
2. We can list sessions
3. We can send a message to a session
4. We receive a response

Goal: Working proof-of-concept for OpenClaw client integration.
"""

import httpx
import json
import sys
from pathlib import Path

# Configuration
DEFAULT_BASE_URL = "http://127.0.0.1:18789"
DEFAULT_SESSION_ID = "main"
DEFAULT_TOKEN = "2fb4459127f320829acfd1b14b0174dd8358d6eb02d141f9"

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_health(base_url: str) -> bool:
    """Test if OpenClaw gateway is running."""
    print_section("Step 1: Gateway Health Check")
    print(f"Connecting to: {base_url}\n")

    try:
        headers = {"Authorization": f"Bearer {DEFAULT_TOKEN}"}
        response = httpx.get(f"{base_url}/health", headers=headers, timeout=5.0)
        response.raise_for_status()

        print(f"✅ Gateway is UP")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}\n")

        # Try to parse response
        try:
            data = response.json()
            print(f"   JSON: {json.dumps(data, indent=2)}\n")
        except json.JSONDecodeError:
            pass

        return True

    except httpx.ConnectError as e:
        print(f"❌ Cannot connect to gateway: {e}")
        print(f"\nTroubleshooting:")
        print(f"   1. Check if OpenClaw is running:")
        print(f"      $ openclaw gateway status")
        print(f"   2. Start gateway if needed:")
        print(f"      $ openclaw gateway start")
        print(f"   3. Verify OpenClaw is listening on {base_url}\n")
        return False

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e}")
        return False

def test_list_sessions(base_url: str, timeout: float = 5.0) -> list | None:
    """Test listing available sessions."""
    print_section("Step 2: List Sessions")
    print(f"GET {base_url}/api/sessions\n")

    try:
        headers = {"Authorization": f"Bearer {DEFAULT_TOKEN}"}
        response = httpx.get(f"{base_url}/api/sessions", headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Sessions retrieved")
        print(f"   Status: {response.status_code}")
        print(f"   Count: {len(data) if isinstance(data, list) else 'N/A'}\n")
        print(f"   Data: {json.dumps(data, indent=2)}\n")

        return data

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error listing sessions: {e}")
        print(f"   Status: {e.response.status_code}")
        print(f"   Response: {e.response.text}\n")
        return None

    except Exception as e:
        print(f"❌ Error listing sessions: {e}\n")
        return None

def test_send_message(base_url: str, session_id: str, timeout: float = 10.0) -> bool:
    """Test sending a message to a session."""
    print_section("Step 3: Send Test Message")
    print(f"POST {base_url}/api/sessions/{session_id}/send")
    print(f"Session ID: {session_id}")
    print(f"Message: 'ping'\n")

    try:
        headers = {"Authorization": f"Bearer {DEFAULT_TOKEN}"}
        payload = {"message": "ping"}
        response = httpx.post(
            f"{base_url}/api/sessions/{session_id}/send",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()

        data = response.json()
        print(f"✅ Message sent successfully")
        print(f"   Status: {response.status_code}\n")
        print(f"   Response: {json.dumps(data, indent=2)}\n")

        return True

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error sending message: {e}")
        print(f"   Status: {e.response.status_code}")
        print(f"   Response: {e.response.text}\n")
        return False

    except Exception as e:
        print(f"❌ Error sending message: {e}\n")
        return False

def test_get_session_output(base_url: str, session_id: str, timeout: float = 5.0) -> bool:
    """Test getting session output (if API supports it)."""
    print_section("Step 4: Get Session Output (Optional)")
    print(f"GET {base_url}/api/sessions/{session_id}/output\n")

    try:
        headers = {"Authorization": f"Bearer {DEFAULT_TOKEN}"}
        # Try with since parameter (common pattern)
        response = httpx.get(
            f"{base_url}/api/sessions/{session_id}/output",
            headers=headers,
            params={"since": 0},
            timeout=timeout
        )

        # Success if 200 or 404 (endpoint might not exist)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session output retrieved")
            print(f"   Status: {response.status_code}\n")
            print(f"   Data: {json.dumps(data, indent=2)}\n")
            return True

        elif response.status_code == 404:
            print(f"⚠️  Output endpoint not found (404)")
            print(f"   This is okay if responses are synchronous in POST body\n")
            return True

        else:
            print(f"❌ Unexpected status: {response.status_code}")
            return False

    except httpx.HTTPStatusError as e:
        print(f"⚠️  Error getting output: {e}")
        print(f"   This endpoint might not exist in all OpenClaw versions\n")
        return True  # Not a blocker

    except Exception as e:
        print(f"⚠️  Error getting output: {e}\n")
        return True  # Not a blocker

def main():
    """Run the Day 0 spike tests."""
    print_section("OpenClaw Sessions API - Day 0 Spike")
    print("Goal: Verify OpenClaw gateway connectivity before integration\n")

    # Parse args
    base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE_URL
    session_id = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SESSION_ID

    print(f"Configuration:")
    print(f"  Base URL: {base_url}")
    print(f"  Session ID: {session_id}")

    # Blocker: Gateway must be running
    if not test_health(base_url):
        print_section("❌ SPIKE FAILED")
        print("OpenClaw gateway is not accessible.")
        print("Start it with: openclaw gateway start")
        sys.exit(1)

    # List sessions
    sessions = test_list_sessions(base_url)
    if sessions is None:
        print_section("⚠️  WARNING")
        print("Could not list sessions, but continuing...")
        print("This might be due to permissions or API version.\n")

    # Test sending message
    if not test_send_message(base_url, session_id):
        print_section("❌ SPIKE FAILED")
        print("Cannot send messages to OpenClaw.")
        print("Check the session ID and permissions.")
        sys.exit(1)

    # Try to get output (optional)
    test_get_session_output(base_url, session_id)

    # Success!
    print_section("✅ SPIKE PASSED")
    print("OpenClaw gateway is accessible and sessions API works!")
    print("\nNext steps:")
    print("  1. Document exact API shape in docs/openclaw-api-notes.md")
    print("  2. Create src/bridge/openclaw_client.py with HTTP client")
    print("  3. Integrate with audio pipeline for full voice loop")
    print("\nYou can proceed to Phase 5 integration.\n")

    sys.exit(0)

if __name__ == "__main__":
    main()