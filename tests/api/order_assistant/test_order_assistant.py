from fastapi.testclient import TestClient


def test_order_assistant_returns_answer(
    assistant_client: TestClient,
) -> None:
    response = assistant_client.post(
        "/order-assistant/ask",
        json={
            "message": "Hello",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "answer": "Hello! How can I help?",
    }
