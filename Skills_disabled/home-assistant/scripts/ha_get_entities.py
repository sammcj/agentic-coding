#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Retrieve entities from Home Assistant.

Usage:
    uv run ha_get_entities.py [domain]

Examples:
    uv run ha_get_entities.py light
    uv run ha_get_entities.py sensor
    uv run ha_get_entities.py          # All entities

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def get_entities(domain=None):
    """Fetch entities from Home Assistant, optionally filtered by domain."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            entities = client.get_states()

            # Convert to dict format for JSON serialization (mode='json' handles datetime serialization)
            entities_data = [entity.model_dump(mode='json') for entity in entities]

            if domain:
                entities_data = [e for e in entities_data if e["entity_id"].startswith(f"{domain}.")]

            return entities_data
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else None
    entities = get_entities(domain)
    print(json.dumps(entities, indent=2))

if __name__ == "__main__":
    main()
