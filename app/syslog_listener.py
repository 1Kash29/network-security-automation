"""UDP syslog receiver for UniFi firewall/IDS-IPS log forwarding.

UniFi OS is Linux-based, and UDM/USG firewall logging uses the standard
netfilter LOG format (SRC=, DST=, PROTO=, SPT=, DPT=, ...). IDS/IPS alerts
are emitted as separate, less structured lines — those are still captured,
with the raw message preserved for the analyst.

Point the UniFi OS console's remote syslog target
(Settings > System > Logging) at this host on SYSLOG_LISTEN_PORT.
"""

import re
import socketserver
import threading
import time

from . import triage

KV_PATTERN = re.compile(r"(\w+)=(\S+)")


def parse_syslog_line(line):
    """Parse one syslog line into a normalized event dict."""
    fields = dict(KV_PATTERN.findall(line))
    lowered = line.lower()

    if "ips" in lowered or "ids" in lowered or "alert" in lowered:
        category = "ips_alert"
    elif "honeypot" in lowered:
        category = "honeypot"
    elif "SRC" in fields:
        category = "firewall_deny"
    else:
        category = "unknown"

    return {
        "source": "unifi_syslog",
        "category": category,
        "src_ip": fields.get("SRC"),
        "dst_ip": fields.get("DST"),
        "message": line.strip(),
    }


def _make_handler(storage):
    class SyslogUDPHandler(socketserver.BaseRequestHandler):
        def handle(self):
            data = self.request[0].decode("utf-8", errors="replace")
            event = parse_syslog_line(data)
            score, severity = triage.score_event(storage, event)
            event.update(
                {
                    "severity": severity,
                    "score": score,
                    "raw": data,
                    "received_at": time.time(),
                }
            )
            storage.insert_security_event(event)

    return SyslogUDPHandler


def start_syslog_listener(storage, host, port):
    """Start the UDP syslog listener in a background daemon thread."""
    server = socketserver.ThreadingUDPServer((host, port), _make_handler(storage))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
