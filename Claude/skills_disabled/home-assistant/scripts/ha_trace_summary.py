#!/usr/bin/env python3
# /// script
# dependencies = [
#   "websockets",
# ]
# ///
"""
Get summary statistics for automation runs from traces.

Usage:
    uv run ha_trace_summary.py <automation_id>

Example:
    uv run ha_trace_summary.py automation.notify_on_door_open

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
import asyncio
import websockets
from datetime import datetime

HA_URL = "ws://homeassistant.local:8123"

async def get_trace_summary(automation_id):
    """Get summary statistics for an automation's trace history."""
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

            # Step 4: Send trace/list command
            # Strip "automation." prefix if present
            item_id = automation_id.replace("automation.", "")

            command = {
                "id": 1,
                "type": "trace/list",
                "domain": "automation",
                "item_id": item_id
            }

            await websocket.send(json.dumps(command))

            # Step 5: Receive response
            msg = await websocket.recv()
            response = json.loads(msg)

            if not response.get("success"):
                error = response.get("error", {})
                print(f"Error: {error.get('message', 'Unknown error')}", file=sys.stderr)
                sys.exit(1)

            result = response.get("result", [])

            if not result:
                print(f"No traces found for automation: {automation_id}", file=sys.stderr)
                sys.exit(1)

            # Filter traces for this automation
            runs = [trace for trace in result if trace.get("item_id") == item_id]

            if not runs:
                print(f"No traces found for automation: {automation_id}", file=sys.stderr)
                sys.exit(1)

            # Calculate statistics
            summary = calculate_summary(runs, automation_id)
            return summary

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def calculate_summary(runs, automation_id):
    """Calculate summary statistics from trace runs."""
    total_runs = len(runs)
    successful_runs = 0
    failed_runs = 0
    execution_times = []
    errors = {}
    last_steps = {}

    for run in runs:
        state = run.get("state")
        script_execution = run.get("script_execution")

        # Count states
        if state == "stopped" and script_execution == "finished":
            successful_runs += 1
        elif run.get("error"):
            failed_runs += 1
        elif state == "stopped" and script_execution != "finished":
            failed_runs += 1

        # Track execution times
        exec_time = calculate_execution_time(run)
        if exec_time is not None:
            execution_times.append(exec_time)

        # Track error patterns
        error = run.get("error")
        if error:
            error_key = error if isinstance(error, str) else str(error)
            errors[error_key] = errors.get(error_key, 0) + 1

        # Track where executions stop
        last_step = run.get("last_step", "unknown")
        last_steps[last_step] = last_steps.get(last_step, 0) + 1

    # Calculate average execution time
    avg_exec_time = sum(execution_times) / len(execution_times) if execution_times else 0
    min_exec_time = min(execution_times) if execution_times else 0
    max_exec_time = max(execution_times) if execution_times else 0

    # Build summary
    summary = {
        "automation_id": automation_id,
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "success_rate": f"{(successful_runs / total_runs * 100):.1f}%" if total_runs > 0 else "0%",
        "execution_time": {
            "average": f"{avg_exec_time:.2f}s" if avg_exec_time > 0 else "N/A",
            "min": f"{min_exec_time:.2f}s" if min_exec_time > 0 else "N/A",
            "max": f"{max_exec_time:.2f}s" if max_exec_time > 0 else "N/A"
        },
        "last_steps": last_steps,
        "error_patterns": errors if errors else "No errors"
    }

    return summary

def calculate_execution_time(run):
    """Calculate execution time in seconds from trace data."""
    timestamp = run.get("timestamp", {})
    start = timestamp.get("start")
    finish = timestamp.get("finish")

    if not start or not finish:
        return None

    try:
        # Parse ISO timestamps with timezone info (handles both +00:00 and Z formats)
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        finish_dt = datetime.fromisoformat(finish.replace('Z', '+00:00'))
        duration = (finish_dt - start_dt).total_seconds()
        return duration
    except:
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run ha_trace_summary.py <automation_id>", file=sys.stderr)
        sys.exit(1)

    automation_id = sys.argv[1]
    summary = asyncio.run(get_trace_summary(automation_id))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
