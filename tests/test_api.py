import pytest
from fastapi.testclient import TestClient
from main import app, requests_store

client = TestClient(app)

# A valid payload we can reuse across tests
VALID_PAYLOAD = {
    "title": "Payment failed",
    "description": "My last invoice shows an error.",
    "category": "Billing",
    "contactEmail": "user@example.com",
}


# Clear the store before and after each test so they don't affect each other
@pytest.fixture(autouse=True)
def clear_store():
    requests_store.clear()
    yield
    requests_store.clear()


def test_create_request_success():
    # Should return 201 with all fields present
    response = client.post("/api/requests", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == VALID_PAYLOAD["title"]
    assert data["description"] == VALID_PAYLOAD["description"]
    assert data["category"] == VALID_PAYLOAD["category"]
    assert data["contactEmail"] == VALID_PAYLOAD["contactEmail"]
    assert "id" in data
    assert "createdAt" in data


def test_create_request_missing_title():
    # Missing title should return 400
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "title"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_create_request_missing_description():
    # Missing description should return 400
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "description"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_create_request_invalid_category():
    # Category must be Billing, Technical, or Other
    payload = {**VALID_PAYLOAD, "category": "Invalid"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_create_request_invalid_email():
    # Bad email format should return 400
    payload = {**VALID_PAYLOAD, "contactEmail": "not-an-email"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_create_request_empty_title():
    # Whitespace-only title should be rejected
    payload = {**VALID_PAYLOAD, "title": "   "}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_create_request_rejects_extra_fields():
    # Unknown fields should be rejected (strict input validation)
    payload = {**VALID_PAYLOAD, "priority": "HIGH"}
    response = client.post("/api/requests", json=payload)
    assert response.status_code == 400


def test_list_requests_empty():
    # Should return an empty list when nothing has been created
    response = client.get("/api/requests")
    assert response.status_code == 200
    assert response.json() == []


def test_list_requests_newest_first():
    # Most recently created request should appear first
    client.post("/api/requests", json={**VALID_PAYLOAD, "title": "First"})
    client.post("/api/requests", json={**VALID_PAYLOAD, "title": "Second"})
    response = client.get("/api/requests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Second"
    assert data[1]["title"] == "First"


def test_get_request_by_id():
    # Should return the correct request when given a valid ID
    create_resp = client.post("/api/requests", json=VALID_PAYLOAD)
    request_id = create_resp.json()["id"]
    response = client.get(f"/api/requests/{request_id}")
    assert response.status_code == 200
    assert response.json()["id"] == request_id


def test_get_request_not_found():
    # Should return 404 for an ID that doesn't exist
    response = client.get("/api/requests/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Request not found"
