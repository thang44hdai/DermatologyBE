import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "model_loaded" in data
    assert "device" in data


def test_health_alternative():
    """Test alternative health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


# Add more tests for prediction and user endpoints
