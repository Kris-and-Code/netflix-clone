from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.main import app
from app.config import settings
from app.utils.auth import create_access_token
import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

client = TestClient(app)

# Test Database Configuration
@pytest.fixture(scope="session")
def test_db_name() -> str:
    return f"netflix_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@pytest.fixture(autouse=True)
async def test_db(test_db_name: str):
    """Setup and teardown test database"""
    test_client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = test_client[test_db_name]
    
    try:
        yield db
    finally:
        await test_client.drop_database(test_db_name)
        await test_client.close()

# Test Data Fixtures
@pytest.fixture
def user_data() -> Dict[str, str]:
    return {
        "email": "test@example.com",
        "password": "Password123!",
        "profile_name": "Test User"
    }

@pytest.fixture
def content_data() -> Dict[str, Any]:
    return {
        "title": "Test Movie",
        "description": "A test movie description that meets minimum length",
        "type": "movie",
        "genre": ["Action", "Drama"],
        "release_year": datetime.now().year,
        "duration": "120",
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "video_url": "https://example.com/video.mp4",
        "rating": 8.5
    }

@pytest.fixture
async def registered_user(test_db, user_data: Dict[str, str]) -> Dict[str, Any]:
    """Create and return a registered user with token"""
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    user_dict = response.json()
    return {
        "token": user_dict["token"],
        "user_data": user_data
    }

@pytest.fixture
def auth_headers(registered_user: Dict[str, Any]) -> Dict[str, str]:
    """Return authentication headers"""
    return {"Authorization": f"Bearer {registered_user['token']}"}

# Authentication Tests
class TestAuth:
    """Authentication endpoint tests"""
    
    @pytest.mark.parametrize("invalid_data, expected_status, expected_error", [
        ({}, 422, "Missing data"),
        ({"email": "invalid"}, 422, "Invalid email format"),
        ({"email": "test@example.com", "password": "short"}, 422, "Password too short"),
        ({"email": "test@example.com"}, 422, "Missing password"),
        ({"password": "password123"}, 422, "Missing email")
    ])
    async def test_register_validation(
        self,
        invalid_data: Dict[str, str],
        expected_status: int,
        expected_error: str
    ):
        response = client.post("/api/auth/register", json=invalid_data)
        assert response.status_code == expected_status
        
    async def test_register_success(self, user_data: Dict[str, str]):
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["message"] == "Registration successful"

    async def test_login_flow(self, registered_user: Dict[str, Any]):
        # Test successful login
        login_data = {
            "email": registered_user["user_data"]["email"],
            "password": registered_user["user_data"]["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        assert "token" in response.json()

        # Test invalid credentials
        invalid_cases = [
            {"email": login_data["email"], "password": "wrong_password"},
            {"email": "wrong@email.com", "password": login_data["password"]},
            {"email": "invalid_email", "password": login_data["password"]},
        ]
        
        for invalid_data in invalid_cases:
            response = client.post("/api/auth/login", json=invalid_data)
            assert response.status_code in [401, 422]

# Content Tests
class TestContent:
    """Content endpoint tests"""

    async def test_content_crud(self, auth_headers: Dict[str, str], content_data: Dict[str, Any]):
        # Create content
        create_response = client.post(
            "/api/content",
            json=content_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        content_id = create_response.json()["id"]

        # Read content
        get_response = client.get(
            f"/api/content/{content_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["title"] == content_data["title"]

        # Update content
        update_data = {"title": "Updated Movie Title"}
        update_response = client.put(
            f"/api/content/{content_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == update_data["title"]

        # Delete content
        delete_response = client.delete(
            f"/api/content/{content_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 204

    @pytest.mark.parametrize("page,limit,expected_count", [
        (1, 5, 5),
        (2, 5, 5),
        (3, 5, 2)
    ])
    async def test_content_pagination(
        self,
        auth_headers: Dict[str, str],
        content_data: Dict[str, Any],
        page: int,
        limit: int,
        expected_count: int
    ):
        # Create 12 content items
        for i in range(12):
            content_data["title"] = f"Movie {i}"
            client.post("/api/content", json=content_data, headers=auth_headers)

        response = client.get(
            "/api/content",
            params={"page": page, "limit": limit},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == expected_count
        assert response.json()["total"] == 12

# User Profile Tests
class TestUserProfile:
    """User profile endpoint tests"""

    async def test_profile_operations(self, auth_headers: Dict[str, str]):
        # Get profile
        get_response = client.get("/api/user/profile", headers=auth_headers)
        assert get_response.status_code == 200
        initial_profile = get_response.json()

        # Update profile
        update_data = {
            "profile_name": "Updated Name",
            "preferences": {
                "language": "es",
                "notifications_enabled": True
            }
        }
        update_response = client.put(
            "/api/user/profile",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["profile_name"] == update_data["profile_name"]
        assert updated_profile["preferences"] == update_data["preferences"]

# Error Handling Tests
class TestErrorHandling:
    """Error handling tests"""

    @pytest.mark.parametrize("endpoint,method,expected_status", [
        ("/api/invalid", "GET", 404),
        ("/api/content", "GET", 401),
        ("/api/content", "POST", 401),
        ("/api/user/profile", "PUT", 401)
    ])
    async def test_error_scenarios(
        self,
        endpoint: str,
        method: str,
        expected_status: int
    ):
        response = client.request(method, endpoint)
        assert response.status_code == expected_status

# Async Setup
@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close() 