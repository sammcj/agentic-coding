#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Search for entities similar to a given pattern or domain.
Useful for finding examples when building automations.

Usage:
    uv run ha_search_similar_entities.py <pattern>

Examples:
    uv run ha_search_similar_entities.py "bedroom light"
    uv run ha_search_similar_entities.py "motion"
    uv run ha_search_similar_entities.py "temperature"

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def search_entities(pattern):
    """Search for entities matching a pattern."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            entities = client.get_states()

            pattern_lower = pattern.lower()
            matching = []

            for entity in entities:
                entity_dict = entity.model_dump(mode='json')
                entity_id = entity_dict["entity_id"].lower()
                friendly_name = entity_dict.get("attributes", {}).get("friendly_name", "").lower()

                if pattern_lower in entity_id or pattern_lower in friendly_name:
                    matching.append({
                        "entity_id": entity_dict["entity_id"],
                        "friendly_name": entity_dict.get("attributes", {}).get("friendly_name", ""),
                        "state": entity_dict["state"],
                        "domain": entity_dict["entity_id"].split(".")[0],
                        "attributes": entity_dict.get("attributes", {})
                    })

            return matching
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run ha_search_similar_entities.py <pattern>", file=sys.stderr)
        sys.exit(1)

    pattern = sys.argv[1]
    matches = search_entities(pattern)

    if matches:
        print(json.dumps(matches, indent=2))
    else:
        print(f"No entities found matching '{pattern}'", file=sys.stderr)

if __name__ == "__main__":
    main()
