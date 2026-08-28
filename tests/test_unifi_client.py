import pytest
import requests

from app.unifi_client import UniFiAPIError, UniFiClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._payload = payload or {}
        self.text = str(payload)

    def json(self):
        return self._payload


def test_list_devices_builds_expected_url(monkeypatch):
    captured = {}

    def fake_get(self, url, params=None, timeout=None):
        captured["url"] = url
        captured["headers"] = dict(self.headers)
        return FakeResponse(200, {"data": [{"id": "abc"}]})

    monkeypatch.setattr(requests.Session, "get", fake_get)

    client = UniFiClient(host="https://10.0.0.1", api_key="test-key", site="site123")
    devices = client.list_devices()

    assert devices == [{"id": "abc"}]
    assert captured["url"] == "https://10.0.0.1/proxy/network/integration/v1/sites/site123/devices"
    assert captured["headers"]["X-API-KEY"] == "test-key"


def test_non_ok_response_raises(monkeypatch):
    def fake_get(self, url, params=None, timeout=None):
        return FakeResponse(500, {"error": "boom"})

    monkeypatch.setattr(requests.Session, "get", fake_get)

    client = UniFiClient(host="https://10.0.0.1", api_key="test-key")
    with pytest.raises(UniFiAPIError):
        client.list_devices()
