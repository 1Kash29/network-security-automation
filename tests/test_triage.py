import time

from app import triage
from app.storage import Storage


def make_storage(tmp_path):
    return Storage(str(tmp_path / "test.db"))


def record_event(storage, event, score, severity):
    storage.insert_security_event(
        {
            "source": "test",
            "category": event["category"],
            "src_ip": event.get("src_ip"),
            "dst_ip": event.get("dst_ip"),
            "message": event.get("message", ""),
            "severity": severity,
            "score": score,
            "raw": "",
            "received_at": time.time(),
        }
    )


def test_unknown_category_scores_low(tmp_path):
    storage = make_storage(tmp_path)
    score, severity = triage.score_event(storage, {"category": "unknown", "message": ""})
    assert severity == "low"
    assert score < 20


def test_high_risk_category_scores_high_or_critical(tmp_path):
    storage = make_storage(tmp_path)
    score, severity = triage.score_event(
        storage, {"category": "ips_alert", "message": "IPS blocked a known exploit"}
    )
    assert severity in ("high", "critical")
    assert score >= 40


def test_repeat_offender_escalates_score(tmp_path):
    storage = make_storage(tmp_path)
    event = {"category": "block", "src_ip": "10.0.0.5", "message": ""}

    last_score = None
    for _ in range(triage.REPEAT_OFFENDER_THRESHOLD):
        last_score, severity = triage.score_event(storage, event)
        record_event(storage, event, last_score, severity)

    escalated_score, _ = triage.score_event(storage, event)
    assert escalated_score > last_score
