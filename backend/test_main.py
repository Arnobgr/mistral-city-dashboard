import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch, MagicMock
from models import DashboardData, MetricKPI

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_dashboard_endpoint():
    # Mock the agent's run_dashboard_agent method
    mock_dashboard_data = DashboardData(
        city="Lyon",
        summary="Test summary for Lyon",
        metrics=[
            MetricKPI(
                id="population",
                title="Population",
                type="kpi",
                unit="inhabitants",
                source_dataset="Test Data",
                source_url="https://example.com",
                value=518000
            )
        ]
    )
    
    with patch('main.agent.run_dashboard_agent', new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = mock_dashboard_data
        
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
