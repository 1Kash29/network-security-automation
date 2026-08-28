import hmac
import time

from flask import Blueprint, abort, current_app, jsonify, render_template, request

from . import triage

bp = Blueprint("main", __name__)


@bp.route("/")
def dashboard():
    return render_template("dashboard.html")


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/api/status")
def api_status():
    storage = current_app.config["STORAGE"]
    return jsonify(
        {
            "devices": storage.list_devices(),
            "clients": storage.list_clients(),
        }
    )


@bp.route("/api/events")
def api_events():
    storage = current_app.config["STORAGE"]
    min_score = request.args.get("min_score", 0, type=int)
    limit = request.args.get("limit", 100, type=int)
    return jsonify({"events": storage.list_recent_events(limit=limit, min_score=min_score)})


@bp.route("/api/events/ingest", methods=["POST"])
def ingest_event():
    """Webhook for pushing security events from an external source (e.g. a
    syslog-to-HTTP forwarder) instead of the built-in UDP listener.

    Requires the shared INGEST_WEBHOOK_TOKEN as a bearer token, when set.
    """
    token = current_app.config.get("INGEST_WEBHOOK_TOKEN")
    if token:
        expected = f"Bearer {token}"
        provided = request.headers.get("Authorization", "")
        if not hmac.compare_digest(provided, expected):
            abort(401)

    payload = request.get_json(silent=True)
    if not payload:
        abort(400)

    storage = current_app.config["STORAGE"]
    event = {
        "source": payload.get("source", "webhook"),
        "category": payload.get("category", "unknown"),
        "src_ip": payload.get("src_ip"),
        "dst_ip": payload.get("dst_ip"),
        "message": payload.get("message", ""),
    }
    score, severity = triage.score_event(storage, event)
    event.update(
        {
            "severity": severity,
            "score": score,
            "raw": payload.get("raw", str(payload)),
            "received_at": time.time(),
        }
    )
    storage.insert_security_event(event)
    return jsonify({"status": "recorded", "score": score, "severity": severity})
