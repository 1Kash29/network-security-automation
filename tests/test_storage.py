from app.storage import Storage


def test_device_status_roundtrip(tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    storage.upsert_device_status(
        {
            "device_id": "dev-1",
            "name": "Switch-1",
            "model": "USW-24",
            "state": "online",
            "ip": "192.168.1.10",
            "last_seen": 1234.0,
        }
    )

    devices = storage.list_devices()
    assert len(devices) == 1
    assert devices[0]["device_id"] == "dev-1"
    assert devices[0]["state"] == "online"


def test_device_status_upsert_updates_existing_row(tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    base = {
        "device_id": "dev-1",
        "name": "Switch-1",
        "model": "USW-24",
        "state": "online",
        "ip": "192.168.1.10",
        "last_seen": 1234.0,
    }
    storage.upsert_device_status(base)
    storage.upsert_device_status({**base, "state": "offline"})

    devices = storage.list_devices()
    assert len(devices) == 1
    assert devices[0]["state"] == "offline"


def test_security_event_filtering_by_min_score(tmp_path):
    storage = Storage(str(tmp_path / "test.db"))
    for score in (5, 25, 75):
        storage.insert_security_event(
            {
                "source": "test",
                "category": "block",
                "src_ip": "10.0.0.1",
                "dst_ip": None,
                "message": "",
                "severity": "low",
                "score": score,
                "raw": "",
                "received_at": 1000.0,
            }
        )

    events = storage.list_recent_events(min_score=50)
    assert len(events) == 1
    assert events[0]["score"] == 75
