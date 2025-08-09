"""Test health endpoint"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health_endpoint():
    """Test that health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ReAgent Backend V3"
    assert "timestamp" in data
    assert "models_available" in data