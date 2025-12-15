#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
# ]
# ///
"""
Get Home Assistant config entries, optionally filtered by domain.
Requires HA_TOKEN environment variable.

Usage:
    uv run ha_get_config_entries.py              # All config entries
    uv run ha_get_config_entries.py telegram_bot # Just Telegram bots
    uv run ha_get_config_entries.py mqtt         # Just MQTT entries
"""

import os
import sys
import json
import requests

HA_URL = "http://homeassistant.local:8123"

def get_config_entries(domain_filter=None):
    """Get config entries, optionally filtered by domain."""
    token = os.getenv("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            f"{HA_URL}/api/config/config_entries/entry",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        entries = response.json()

        # Filter by domain if specified
        if domain_filter:
            entries = [
                entry for entry in entries
                if entry.get("domain") == domain_filter
            ]

        if not entries:
            if domain_filter:
                print(f"No config entries found for domain: {domain_filter}")
            else:
                print("No config entries found")
            return

        # Format for easy use
        result = []
        for entry in entries:
            result.append({
                "config_entry_id": entry["entry_id"],
                "title": entry.get("title", "Unknown"),
                "domain": entry["domain"],
                "state": entry.get("state", "unknown"),
                "source": entry.get("source", "unknown")
            })

        print(json.dumps(result, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"Error fetching config entries: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    domain = sys.argv[1] if len(sys.argv) > 1 else None
    get_config_entries(domain)
