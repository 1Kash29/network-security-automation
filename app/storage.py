"""SQLite-backed storage, shared across threads.

The poller thread, the syslog listener's UDP handler threads, and Flask's
own request threads all touch this connection, so every read/write is
serialized through a single lock rather than trusting sqlite3 (which isn't
safe to share across threads on its own, even with check_same_thread=False).
"""

import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS device_status (
    device_id TEXT PRIMARY KEY,
    name TEXT,
    model TEXT,
    state TEXT,
    ip TEXT,
    last_seen REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS client_status (
    client_id TEXT PRIMARY KEY,
    name TEXT,
    ip TEXT,
    mac TEXT,
    network TEXT,
    last_seen REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS security_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    category TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    message TEXT,
    severity TEXT,
    score INTEGER,
    raw TEXT,
    received_at REAL
);

CREATE INDEX IF NOT EXISTS idx_events_received_at ON security_events(received_at);
CREATE INDEX IF NOT EXISTS idx_events_src_ip ON security_events(src_ip);
"""


class Storage:
    def __init__(self, db_path):
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def upsert_device_status(self, device):
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO device_status (device_id, name, model, state, ip, last_seen, updated_at)
                VALUES (:device_id, :name, :model, :state, :ip, :last_seen, :updated_at)
                ON CONFLICT(device_id) DO UPDATE SET
                    name=excluded.name, model=excluded.model, state=excluded.state,
                    ip=excluded.ip, last_seen=excluded.last_seen, updated_at=excluded.updated_at
                """,
                {**device, "updated_at": time.time()},
            )
            self._conn.commit()

    def upsert_client_status(self, client):
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO client_status (client_id, name, ip, mac, network, last_seen, updated_at)
                VALUES (:client_id, :name, :ip, :mac, :network, :last_seen, :updated_at)
                ON CONFLICT(client_id) DO UPDATE SET
                    name=excluded.name, ip=excluded.ip, mac=excluded.mac,
                    network=excluded.network, last_seen=excluded.last_seen, updated_at=excluded.updated_at
                """,
                {**client, "updated_at": time.time()},
            )
            self._conn.commit()

    def insert_security_event(self, event):
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO security_events
                    (source, category, src_ip, dst_ip, message, severity, score, raw, received_at)
                VALUES (:source, :category, :src_ip, :dst_ip, :message, :severity, :score, :raw, :received_at)
                """,
                event,
            )
            self._conn.commit()

    def list_devices(self):
        with self._lock:
            rows = self._conn.execute("SELECT * FROM device_status ORDER BY name").fetchall()
        return [dict(row) for row in rows]

    def list_clients(self, limit=200):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM client_status ORDER BY last_seen DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def list_recent_events(self, limit=100, min_score=0):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM security_events WHERE score >= ? ORDER BY received_at DESC LIMIT ?",
                (min_score, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def recent_event_count_from_ip(self, src_ip, window_seconds):
        cutoff = time.time() - window_seconds
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) as c FROM security_events WHERE src_ip = ? AND received_at >= ?",
                (src_ip, cutoff),
            ).fetchone()
        return row["c"] if row else 0

    def close(self):
        with self._lock:
            self._conn.close()
