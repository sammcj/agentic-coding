#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Get Home Assistant configuration including available integrations and domains.

Usage:
    uv run ha_get_config.py

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def get_config():
    """Fetch Home Assistant configuration."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            config = client.get_config()
            return config
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    config = get_config()
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
