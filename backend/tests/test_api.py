import os

os.environ.setdefault("FORCE_MOCK_NOTIFICATIONS", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/fraud_engine_test.db")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_reports_database_connection():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"


def test_rule_registry_exposes_required_rules():
    response = client.get("/api/rules")

    assert response.status_code == 200
    rule_ids = {rule["rule_id"] for rule in response.json()}
    assert {
        "transaction_velocity",
        "unusual_transaction_amount",
        "impossible_geographical_location",
    }.issubset(rule_ids)


def test_api_key_protects_private_routes(monkeypatch):
    monkeypatch.setattr("app.main.settings.API_KEY", "test-key")

    unauthorized = client.get("/api/rules")
    authorized = client.get("/api/rules", headers={"X-API-Key": "test-key"})

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200

    monkeypatch.setattr("app.main.settings.API_KEY", None)
