"""Thin client for the UniFi Network Integration API.

This targets Ubiquiti's official, documented API-key-based Integration API
(see https://developer.ui.com) rather than the internal cookie-authenticated
endpoints the UniFi Network web app itself uses. That means no
username/password is ever stored by this app — only a scoped API key.
"""

import requests


class UniFiAPIError(Exception):
    pass


class UniFiClient:
    def __init__(self, host, api_key, site="default", verify_ssl=False, timeout=10):
        self.host = host.rstrip("/")
        self.site = site
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update(
            {
                "X-API-KEY": api_key,
                "Accept": "application/json",
            }
        )

    def _get(self, path, params=None):
        url = f"{self.host}/proxy/network/integration/v1{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if not resp.ok:
            raise UniFiAPIError(f"GET {path} failed: {resp.status_code} {resp.text[:200]}")
        return resp.json()

    def list_sites(self):
        data = self._get("/sites")
        return data.get("data", data)

    def list_devices(self, site_id=None):
        site_id = site_id or self.site
        data = self._get(f"/sites/{site_id}/devices")
        return data.get("data", data)

    def list_clients(self, site_id=None):
        site_id = site_id or self.site
        data = self._get(f"/sites/{site_id}/clients")
        return data.get("data", data)

    def get_device(self, device_id, site_id=None):
        site_id = site_id or self.site
        return self._get(f"/sites/{site_id}/devices/{device_id}")
