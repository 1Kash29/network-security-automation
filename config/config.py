import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    UNIFI_HOST = os.environ.get("UNIFI_HOST", "").rstrip("/")
    UNIFI_API_KEY = os.environ.get("UNIFI_API_KEY", "")
    UNIFI_SITE = os.environ.get("UNIFI_SITE", "default")
    UNIFI_VERIFY_SSL = os.environ.get("UNIFI_VERIFY_SSL", "false").lower() == "true"

    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "30"))

    SYSLOG_LISTEN_HOST = os.environ.get("SYSLOG_LISTEN_HOST", "0.0.0.0")
    SYSLOG_LISTEN_PORT = int(os.environ.get("SYSLOG_LISTEN_PORT", "5514"))
    INGEST_WEBHOOK_TOKEN = os.environ.get("INGEST_WEBHOOK_TOKEN", "")

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    DB_PATH = os.environ.get("DB_PATH", "data/monitor.db")
