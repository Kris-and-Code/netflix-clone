from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Netflix Clone API"}

def test_register():
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "profile_name": "Test User"
    })
    assert response.status_code == 200
    assert "token" in response.json() 