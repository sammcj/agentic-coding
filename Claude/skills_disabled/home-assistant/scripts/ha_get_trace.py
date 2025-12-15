#!/usr/bin/env python3
# /// script
# dependencies = [
#   "websockets",
# ]
# ///
"""
Get detailed trace for a specific automation run.

Usage:
    uv run ha_get_trace.py <automation_id> <run_id>

Example:
    uv run ha_get_trace.py automation.notify_on_door_open 1ceef6b2b6f63a8745eb5dba3fe12f71

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
import asyncio
import websockets
from datetime import datetime
from zoneinfo import ZoneInfo

HA_URL = "ws://homeassistant.local:8123"
MOUNTAIN_TZ = ZoneInfo("America/Denver")

def convert_to_mountain_time(timestamp_str):
    """Convert ISO timestamp string to Mountain Time formatted string."""
    if not timestamp_str:
        return None
    try:
        # Parse ISO timestamp (handles both +00:00 and Z formats)
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Convert to Mountain Time
        dt_mountain = dt.astimezone(MOUNTAIN_TZ)
        # Return formatted string
        return dt_mountain.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return timestamp_str  # Return original if conversion fails

def convert_trace_timestamps(trace):
    """Convert timestamp fields in trace data to Mountain Time."""
    if not trace:
        return trace

    # Convert top-level timestamp fields
    if "timestamp" in trace and isinstance(trace["timestamp"], dict):
        timestamp = trace["timestamp"]
        if "start" in timestamp:
            timestamp["start"] = convert_to_mountain_time(timestamp["start"])
        if "finish" in timestamp:
            timestamp["finish"] = convert_to_mountain_time(timestamp["finish"])

    return trace

async def get_trace(automation_id, run_id):
    """Get detailed trace for a specific automation run."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        async with websockets.connect(HA_URL) as websocket:
            # Step 1: Receive auth_required message
            msg = await websocket.recv()
            auth_msg = json.loads(msg)

            if auth_msg.get("type") != "auth_required":
                print(f"Error: Expected auth_required, got {auth_msg.get('type')}", file=sys.stderr)
                sys.exit(1)

            # Step 2: Send auth message
            await websocket.send(json.dumps({
                "type": "auth",
                "access_token": token
            }))

            # Step 3: Receive auth response
            msg = await websocket.recv()
            auth_result = json.loads(msg)

            if auth_result.get("type") != "auth_ok":
                print(f"Error: Authentication failed: {auth_result}", file=sys.stderr)
                sys.exit(1)

            # Step 4: Send trace/get command
            # Strip "automation." prefix if present
            item_id = automation_id.replace("automation.", "")

            command = {
                "id": 1,
                "type": "trace/get",
                "domain": "automation",
                "item_id": item_id,
                "run_id": run_id
            }

            await websocket.send(json.dumps(command))

            # Step 5: Receive response
            msg = await websocket.recv()
            response = json.loads(msg)

            if not response.get("success"):
                error = response.get("error", {})
                print(f"Error: {error.get('message', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)

            trace = response.get("result")

            if not trace:
                print(f"No trace found for {automation_id} run {run_id}", file=sys.stderr)
                sys.exit(1)

            # Convert timestamps to Mountain Time
            trace = convert_trace_timestamps(trace)

            return trace

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: uv run ha_get_trace.py <automation_id> <run_id>", file=sys.stderr)
        print("\nTip: Use ha_list_traces.py to find run_ids for an automation", file=sys.stderr)
        sys.exit(1)

    automation_id = sys.argv[1]
    run_id = sys.argv[2]

    trace = asyncio.run(get_trace(automation_id, run_id))
    print(json.dumps(trace, indent=2))

if __name__ == "__main__":
    main()
