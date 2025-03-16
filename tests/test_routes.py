from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.config import settings
import pytest
import asyncio

client = TestClient(app)

# Setup and teardown for test database
@pytest.fixture(autouse=True)
async def setup_test_db():
    # Connect to test database
    test_db_url = settings.MONGODB_URL + "_test"
    test_client = AsyncIOMotorClient(test_db_url)
    test_db = test_client.get_default_database()
    
    # Store original database URL
    original_db_url = settings.MONGODB_URL
    settings.MONGODB_URL = test_db_url
    
    yield test_db
    
    # Cleanup: drop test database and restore original URL
    await test_client.drop_database(test_db.name)
    test_client.close()
    settings.MONGODB_URL = original_db_url

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "password123",
        "profile_name": "Test User"
    }

@pytest.fixture
def auth_headers(test_user):
    # Register and get token
    response = client.post("/api/auth/register", json=test_user)
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

# Test root endpoint
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Netflix Clone API"}

# Authentication tests
class TestAuth:
    def test_register_success(self, test_user):
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["message"] == "Registration successful"

    def test_register_duplicate_email(self, test_user):
        # First registration
        client.post("/api/auth/register", json=test_user)
        # Duplicate registration
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self, test_user):
        test_user["email"] = "invalid-email"
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, test_user):
        test_user["password"] = "123"  # Too short
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 422

    def test_login_success(self, test_user):
        # Register user first
        client.post("/api/auth/register", json=test_user)
        # Try logging in
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["message"] == "Login successful"

    def test_login_invalid_credentials(self, test_user):
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_missing_fields(self):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

# Content tests
class TestContent:
    def test_get_content_unauthorized(self):
        response = client.get("/api/content")
        assert response.status_code == 401

    def test_get_content_empty(self, auth_headers):
        response = client.get("/api/content", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_content_with_filters(self, auth_headers):
        response = client.get(
            "/api/content",
            params={"genre": "Action", "page": 1, "limit": 10},
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_content_invalid_page(self, auth_headers):
        response = client.get(
            "/api/content",
            params={"page": 0},  # Invalid page number
            headers=auth_headers
        )
        assert response.status_code == 422

# Configure pytest for async
def pytest_configure(config):
    """Setup pytest to handle async tests"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 