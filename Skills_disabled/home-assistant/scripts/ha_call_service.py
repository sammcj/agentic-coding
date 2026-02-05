#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Call a Home Assistant service.

Usage:
    uv run ha_call_service.py <domain> <service> <service_data_json>

Example:
    uv run ha_call_service.py light turn_on '{"entity_id": "light.living_room", "brightness": 255}'

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def call_service(domain, service, service_data):
    """Call a Home Assistant service."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            # Get all domains
            domains = client.get_domains()

            if domain not in domains:
                print(f"Error: Domain '{domain}' not found", file=sys.stderr)
                sys.exit(1)

            domain_obj = domains[domain]

            if service not in domain_obj.services:
                print(f"Error: Service '{service}' not found in domain '{domain}'", file=sys.stderr)
                sys.exit(1)

            service_obj = domain_obj.services[service]
            result = service_obj.trigger(**service_data)
            return result if result else {"success": True}
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) < 4:
        print("Usage: uv run ha_call_service.py <domain> <service> <service_data_json>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1]
    service = sys.argv[2]

    try:
        service_data = json.loads(sys.argv[3])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in service_data: {e}", file=sys.stderr)
        sys.exit(1)

    result = call_service(domain, service, service_data)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
