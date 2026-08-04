#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Get the state of a specific Home Assistant entity.

Usage:
    uv run ha_get_state.py <entity_id>

Example:
    uv run ha_get_state.py light.living_room

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def get_state(entity_id):
    """Fetch the state of a specific entity."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            # Get all states and filter for the requested entity_id
            states = client.get_states()
            entity = next((e for e in states if e.entity_id == entity_id), None)

            if entity is None:
                print(f"Error: Entity '{entity_id}' not found", file=sys.stderr)
                sys.exit(1)

            return entity.model_dump(mode='json')
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run ha_get_state.py <entity_id>", file=sys.stderr)
        sys.exit(1)

    entity_id = sys.argv[1]
    state = get_state(entity_id)
    print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
