from __future__ import annotations

import logging
from collections.abc import Callable
from threading import Thread

from flask import Flask, jsonify, request
from werkzeug.serving import BaseWSGIServer, make_server

from .models import NotificationPayload, PayloadValidationError

logger = logging.getLogger(__name__)


class LocalHttpServer:
    def __init__(
        self,
        host: str,
        port: int,
        enqueue_notification: Callable[[NotificationPayload], int],
    ) -> None:
        self.host = host
        self.port = port
        self._enqueue_notification = enqueue_notification
        self._server: BaseWSGIServer | None = None
        self._thread: Thread | None = None
        self.flask_app = self._create_app()

    def _create_app(self) -> Flask:
        app = Flask(__name__)

        @app.post("/notify")
        def notify():
            payload_json = request.get_json(silent=True)
            try:
                payload = NotificationPayload.from_mapping(payload_json or {})
            except PayloadValidationError as exc:
                return jsonify({"status": "error", "error": str(exc)}), 400

            queue_size = self._enqueue_notification(payload)
            logger.info("Accepted notification '%s' (queue=%s)", payload.message, queue_size)
            return jsonify({"status": "accepted", "queue_size": queue_size}), 202

        return app

    def start(self) -> None:
        if self._thread is not None:
            return

        server = make_server(self.host, self.port, self.flask_app, threaded=True)
        self._server = server
        self._thread = Thread(
            target=server.serve_forever,
            name="local-toastd-http",
            daemon=True,
        )
        self._thread.start()
        logger.info("HTTP server started on http://%s:%s", self.host, self.port)

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            logger.info("HTTP server stopped")
            self._server = None

        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
