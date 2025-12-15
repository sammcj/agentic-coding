#!/usr/bin/env python3
# /// script
# dependencies = [
#   "homeassistant-api",
#   "requests",
# ]
# ///
"""
Search for Home Assistant dashboards by name or ID.

Usage:
    uv run ha_search_dashboards.py [search_pattern]

Examples:
    uv run ha_search_dashboards.py                    # List all dashboards
    uv run ha_search_dashboards.py "phone"            # Search for dashboards with "phone" in the name
    uv run ha_search_dashboards.py "cullen's phone"   # Search for specific dashboard

Requires HA_TOKEN environment variable to be set.
"""

import os
import sys
import json
from homeassistant_api import Client

HA_URL = "http://homeassistant.local:8123/api"
HA_BASE_URL = "http://homeassistant.local:8123"

def get_dashboards(search_pattern=None):
    """Get all dashboards, optionally filtered by search pattern."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            # Use the underlying session to make a custom API call for dashboards
            session = client._session

            # Get the list of dashboards
            response = session.get(f"{HA_BASE_URL}/api/lovelace/dashboards/list")
            response.raise_for_status()
            dashboards = response.json()

            # Filter by search pattern if provided
            if search_pattern:
                pattern_lower = search_pattern.lower()
                matching = []

                for dashboard in dashboards:
                    # Search in both the ID and the title
                    dashboard_id = dashboard.get("id", "").lower()
                    title = dashboard.get("title", "").lower()
                    url_path = dashboard.get("url_path", "").lower()

                    if (pattern_lower in dashboard_id or
                        pattern_lower in title or
                        pattern_lower in url_path):
                        matching.append(dashboard)

                return matching

            return dashboards

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def get_dashboard_config(dashboard_url_path):
    """Get the full configuration for a specific dashboard."""
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("Error: HA_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        with Client(HA_URL, token) as client:
            session = client._session

            # Get the dashboard configuration
            response = session.get(f"{HA_BASE_URL}/api/lovelace/{dashboard_url_path}")
            response.raise_for_status()
            config = response.json()

            return config

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    search_pattern = sys.argv[1] if len(sys.argv) > 1 else None

    # Get matching dashboards
    dashboards = get_dashboards(search_pattern)

    if not dashboards:
        if search_pattern:
            print(f"No dashboards found matching '{search_pattern}'", file=sys.stderr)
        else:
            print("No dashboards found", file=sys.stderr)
        sys.exit(1)

    # If only one dashboard matches, get its full config
    if len(dashboards) == 1:
        dashboard = dashboards[0]
        url_path = dashboard.get("url_path")

        print(f"Found dashboard: {dashboard.get('title', 'Untitled')} (url_path: {url_path})")
        print("\nDashboard metadata:")
        print(json.dumps(dashboard, indent=2))

        if url_path:
            print(f"\n\nFull dashboard configuration:")
            config = get_dashboard_config(url_path)
            print(json.dumps(config, indent=2))
    else:
        # Multiple matches, just list them
        print(f"Found {len(dashboards)} dashboard(s):\n")
        for dashboard in dashboards:
            print(json.dumps(dashboard, indent=2))
            print()

if __name__ == "__main__":
    main()
