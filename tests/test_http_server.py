from __future__ import annotations

from local_toastd.http_server import LocalHttpServer
from local_toastd.models import NotificationPayload


def test_notify_accepts_valid_payload() -> None:
    received: list[NotificationPayload] = []

    def sink(payload: NotificationPayload) -> int:
        received.append(payload)
        return len(received)

    server = LocalHttpServer("127.0.0.1", 8765, sink)
    client = server.flask_app.test_client()

    response = client.post("/notify", json={"message": "hello", "title": "test"})

    assert response.status_code == 202
    assert response.get_json() == {"status": "accepted", "queue_size": 1}
    assert [item.message for item in received] == ["hello"]


def test_notify_rejects_invalid_payload() -> None:
    server = LocalHttpServer("127.0.0.1", 8765, lambda payload: 1)
    client = server.flask_app.test_client()

    response = client.post("/notify", json={"title": "missing message"})

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
