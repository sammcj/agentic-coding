#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Retrieve all automations from Home Assistant with their configurations.

Usage:
    uv run ha_get_automations.py [search_term]

Examples:
    uv run ha_get_automations.py                    # All automations
    uv run ha_get_automations.py motion             # Automations with 'motion' in name
    uv run ha_get_automations.py light              # Automations with 'light' in name

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client
from datetime import datetime
from zoneinfo import ZoneInfo

HA_URL = "http://homeassistant.local:8123/api"
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

def get_automations(search_term=None):
    """Fetch all automation entities."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            entities = client.get_states()

            # Filter to automation entities
            automations = [
                entity.model_dump(mode='json') for entity in entities
                if entity.entity_id.startswith("automation.")
            ]

            # Filter by search term if provided
            if search_term:
                search_term = search_term.lower()
                automations = [
                    a for a in automations
                    if search_term in a["entity_id"].lower() or
                       search_term in a.get("attributes", {}).get("friendly_name", "").lower()
                ]

            # Convert timestamps to Mountain Time
            for automation in automations:
                # Convert last_triggered in attributes
                if "attributes" in automation and "last_triggered" in automation["attributes"]:
                    automation["attributes"]["last_triggered"] = convert_to_mountain_time(
                        automation["attributes"]["last_triggered"]
                    )
                # Convert top-level timestamps
                for field in ["last_changed", "last_updated", "last_reported"]:
                    if field in automation:
                        automation[field] = convert_to_mountain_time(automation[field])

            return automations
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    search_term = sys.argv[1] if len(sys.argv) > 1 else None
    automations = get_automations(search_term)
    print(json.dumps(automations, indent=2))

if __name__ == "__main__":
    main()
