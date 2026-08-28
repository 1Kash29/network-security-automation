"""Entrypoint: starts the Flask app plus its background workers.

For local development: `python run.py`. In production, run behind gunicorn
against `app:create_app()` and start the poller/syslog listener from a
single worker (see README) so multiple gunicorn workers don't each spin up
duplicate background threads.
"""

from app import create_app
from app.poller import start_poller
from app.syslog_listener import start_syslog_listener
from app.unifi_client import UniFiClient
from config.config import Config

app = create_app()

if __name__ == "__main__":
    storage = app.config["STORAGE"]

    if Config.UNIFI_HOST and Config.UNIFI_API_KEY:
        unifi = UniFiClient(
            host=Config.UNIFI_HOST,
            api_key=Config.UNIFI_API_KEY,
            site=Config.UNIFI_SITE,
            verify_ssl=Config.UNIFI_VERIFY_SSL,
        )
        start_poller(unifi, storage, Config.POLL_INTERVAL_SECONDS)
    else:
        print(
            "UNIFI_HOST/UNIFI_API_KEY not set - skipping device polling "
            "(the dashboard will show no devices/clients until configured)."
        )

    start_syslog_listener(storage, Config.SYSLOG_LISTEN_HOST, Config.SYSLOG_LISTEN_PORT)

    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
