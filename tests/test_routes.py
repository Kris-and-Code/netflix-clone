from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.config import settings

client = TestClient(app)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "password123",
        "profile_name": "Test User"
    }

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Netflix Clone API"}

def test_register(test_user):
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 201
    assert "token" in response.json()
    assert response.json()["message"] == "Registration successful"

def test_register_duplicate_email(test_user):
    # First registration
    client.post("/api/auth/register", json=test_user)
    # Duplicate registration
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login(test_user):
    # Register user first
    client.post("/api/auth/register", json=test_user)
    # Try logging in
    response = client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    assert "token" in response.json()
    assert response.json()["message"] == "Login successful"

def test_login_invalid_credentials(test_user):
    response = client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"] 