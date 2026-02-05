#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
# ]
# ///
"""
Get all available Home Assistant services with their descriptions and fields.

Usage:
    uv run ha_get_services.py [domain]

Examples:
    uv run ha_get_services.py           # All services
    uv run ha_get_services.py light     # Just light services
    uv run ha_get_services.py climate   # Just climate services

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"

def get_services(domain=None):
    """Fetch available services, optionally filtered by domain."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            # Get domains which contain the services
            domains = client.get_domains()

            if domain:
                # Get specific domain
                if domain in domains:
                    domain_obj = domains[domain]
                    # Get services from the domain
                    services = {svc_name: svc.model_dump(mode='json') for svc_name, svc in domain_obj.services.items()}
                    return {domain: services}
                else:
                    return {}

            # Get all services from all domains
            all_services = {}
            for domain_name, domain_obj in domains.items():
                services = {svc_name: svc.model_dump(mode='json') for svc_name, svc in domain_obj.services.items()}
                all_services[domain_name] = services

            return all_services
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else None
    services = get_services(domain)
    print(json.dumps(services, indent=2))

if __name__ == "__main__":
    main()
