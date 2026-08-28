"""Background polling loop that mirrors UniFi device/client state into storage."""

import logging
import threading
import time

from .unifi_client import UniFiAPIError

logger = logging.getLogger(__name__)


def _normalize_device(raw):
    return {
        "device_id": raw.get("id"),
        "name": raw.get("name") or raw.get("model") or "unknown",
        "model": raw.get("model"),
        "state": raw.get("state", "unknown"),
        "ip": raw.get("ipAddress") or raw.get("ip"),
        "last_seen": time.time(),
    }


def _normalize_client(raw):
    return {
        "client_id": raw.get("id") or raw.get("mac"),
        "name": raw.get("name") or raw.get("hostname") or "unknown",
        "ip": raw.get("ipAddress") or raw.get("ip"),
        "mac": raw.get("macAddress") or raw.get("mac"),
        "network": raw.get("network") or raw.get("essid") or "",
        "last_seen": time.time(),
    }


def poll_once(client, storage):
    """Fetch current devices/clients from UniFi and persist their status.

    A failed poll is logged and skipped rather than raised, so a momentary
    controller hiccup doesn't kill the background loop.
    """
    try:
        for raw in client.list_devices():
            storage.upsert_device_status(_normalize_device(raw))
    except UniFiAPIError as exc:
        logger.warning("Device poll failed: %s", exc)

    try:
        for raw in client.list_clients():
            storage.upsert_client_status(_normalize_client(raw))
    except UniFiAPIError as exc:
        logger.warning("Client poll failed: %s", exc)


def start_poller(client, storage, interval_seconds):
    """Start the polling loop in a background daemon thread."""

    def _loop():
        while True:
            poll_once(client, storage)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread
