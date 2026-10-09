from fastapi.testclient import TestClient


def test_response_contains_request_id(
    client: TestClient,
) -> None:
    response = client.get("/orders")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) > 0


def test_request_id_is_propagated(
    client: TestClient,
) -> None:
    response = client.get(
        "/orders",
        headers={"X-Request-ID": "integration-test-123"},
    )

    assert response.status_code == 200

    assert response.headers["X-Request-ID"] == "integration-test-123"
