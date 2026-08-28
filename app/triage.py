"""Rule-based scoring for inbound security events (firewall/IDS-IPS/auth logs).

Deliberately simple and transparent rather than a black-box model: every
point added is a named rule, so an analyst can see exactly why an event was
flagged and can tune the thresholds for their own network.
"""

HIGH_RISK_CATEGORIES = {"ips_alert", "honeypot", "malware", "botnet", "exploit"}
MEDIUM_RISK_CATEGORIES = {"port_scan", "block", "firewall_deny"}

REPEAT_OFFENDER_WINDOW_SECONDS = 15 * 60
REPEAT_OFFENDER_THRESHOLD = 5


def score_event(storage, event):
    """Return (score, severity) for a normalized event dict.

    Expected event keys: category, src_ip, message.
    """
    score = 0
    category = (event.get("category") or "").lower()

    if category in HIGH_RISK_CATEGORIES:
        score += 60
    elif category in MEDIUM_RISK_CATEGORIES:
        score += 25
    else:
        score += 5

    src_ip = event.get("src_ip")
    if src_ip:
        repeat_count = storage.recent_event_count_from_ip(src_ip, REPEAT_OFFENDER_WINDOW_SECONDS)
        if repeat_count >= REPEAT_OFFENDER_THRESHOLD:
            score += 30

    message = (event.get("message") or "").lower()
    if any(keyword in message for keyword in ("brute", "credential", "unauthorized")):
        score += 15

    score = min(score, 100)

    if score >= 70:
        severity = "critical"
    elif score >= 40:
        severity = "high"
    elif score >= 20:
        severity = "medium"
    else:
        severity = "low"

    return score, severity
