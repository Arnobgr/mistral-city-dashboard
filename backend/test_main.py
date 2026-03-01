import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_dashboard_endpoint():
    response = client.post("/api/dashboard", json={"city": "Lyon"})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["city"] == "Lyon"
    assert "summary" in data["data"]
    assert "metrics" in data["data"]

def test_dashboard_validation():
    response = client.post("/api/dashboard", json={"city": ""})
    assert response.status_code == 422
    
def test_dashboard_missing_city():
    response = client.post("/api/dashboard", json={})
    assert response.status_code == 422
