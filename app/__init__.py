import logging

from flask import Flask

from config.config import Config

from .routes import bp
from .storage import Storage


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if not app.config.get("INGEST_WEBHOOK_TOKEN"):
        logger.warning(
            "INGEST_WEBHOOK_TOKEN is not set - the /api/events/ingest webhook "
            "is unauthenticated. Set it before exposing this app beyond localhost."
        )

    storage = Storage(app.config["DB_PATH"])
    app.config["STORAGE"] = storage

    app.register_blueprint(bp)

    return app
