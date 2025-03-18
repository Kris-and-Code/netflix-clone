from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.config import settings
import pytest
import asyncio

client = TestClient(app)

# Database Fixtures
@pytest.fixture(autouse=True)
async def test_db():
    """Setup test database"""
    test_client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = test_client.get_default_database()
    
    # Clear database before each test
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})
    
    yield db
    
    # Cleanup after tests
    await test_client.drop_database(db.name)
    test_client.close()

# Test Data Fixtures
@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "Password123!",
        "profile_name": "Test User"
    }

@pytest.fixture
def content_data():
    return {
        "title": "Test Movie",
        "description": "A test movie description",
        "type": "movie",
        "genre": ["Action", "Drama"],
        "release_year": 2023,
        "duration": "120",
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "video_url": "https://example.com/video.mp4"
    }

@pytest.fixture
async def auth_token(user_data):
    """Create user and return auth token"""
    response = client.post("/api/auth/register", json=user_data)
    return response.json()["token"]

@pytest.fixture
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}

# Authentication Tests
class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_success(self, user_data):
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["message"] == "Registration successful"

    def test_register_validation(self):
        invalid_cases = [
            ({}, 422, "Missing data"),
            ({"email": "invalid"}, 422, "Invalid email"),
            ({"email": "test@example.com", "password": "short"}, 422, "Password too short"),
            ({"email": "test@example.com"}, 422, "Missing password")
        ]
        
        for data, expected_status, message in invalid_cases:
            response = client.post("/api/auth/register", json=data)
            assert response.status_code == expected_status, message

    def test_register_duplicate_email(self, user_data):
        # First registration
        client.post("/api/auth/register", json=user_data)
        # Duplicate registration
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_login_flow(self, user_data):
        # Register
        client.post("/api/auth/register", json=user_data)
        
        # Test successful login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        assert "token" in response.json()
        
        # Test invalid password
        login_data["password"] = "wrong_password"
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

# Content Tests
class TestContent:
    """Test content endpoints"""

    async def test_create_content(self, auth_headers, content_data):
        response = client.post(
            "/api/content",
            json=content_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == content_data["title"]

    def test_get_content_list(self, auth_headers):
        response = client.get("/api/content", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_content_pagination(self, auth_headers, content_data):
        # Create multiple content items
        for i in range(15):
            content_data["title"] = f"Movie {i}"
            client.post("/api/content", json=content_data, headers=auth_headers)

        # Test pagination
        response = client.get(
            "/api/content",
            params={"page": 1, "limit": 10},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

    def test_content_filters(self, auth_headers, content_data):
        # Create content with different genres
        content_data["genre"] = ["Action"]
        client.post("/api/content", json=content_data, headers=auth_headers)
        
        content_data["genre"] = ["Drama"]
        client.post("/api/content", json=content_data, headers=auth_headers)

        # Test genre filter
        response = client.get(
            "/api/content",
            params={"genre": "Action"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert "Action" in response.json()[0]["genre"]

# User Profile Tests
class TestUserProfile:
    """Test user profile endpoints"""

    def test_get_profile(self, auth_headers):
        response = client.get("/api/user/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "profile_name" in data

    def test_update_profile(self, auth_headers):
        update_data = {"profile_name": "Updated Name"}
        response = client.put(
            "/api/user/profile",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["profile_name"] == update_data["profile_name"]

# Error Handling Tests
class TestErrorHandling:
    """Test error handling"""

    def test_invalid_token(self):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/content", headers=headers)
        assert response.status_code == 401

    def test_missing_token(self):
        response = client.get("/api/content")
        assert response.status_code == 401

    def test_invalid_endpoint(self):
        response = client.get("/api/invalid")
        assert response.status_code == 404

# Setup pytest for async testing
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as async")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close() 