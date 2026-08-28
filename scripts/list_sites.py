"""Helper CLI: prints the UniFi sites visible to your API key, so you can
find the site ID to put in UNIFI_SITE.

Usage: python scripts/list_sites.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.unifi_client import UniFiAPIError, UniFiClient  # noqa: E402
from config.config import Config  # noqa: E402


def main():
    if not Config.UNIFI_HOST or not Config.UNIFI_API_KEY:
        print("Set UNIFI_HOST and UNIFI_API_KEY in your .env first.")
        return 1

    client = UniFiClient(
        host=Config.UNIFI_HOST,
        api_key=Config.UNIFI_API_KEY,
        verify_ssl=Config.UNIFI_VERIFY_SSL,
    )
    try:
        sites = client.list_sites()
    except UniFiAPIError as exc:
        print(f"Failed to list sites: {exc}")
        return 1

    for site in sites:
        print(f"{site.get('id')}\t{site.get('name')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
