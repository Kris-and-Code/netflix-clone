import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from ..app.main import app
from ..app.config.settings import get_settings

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def db():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME + "_test"]
    yield db
    await client.drop_database(settings.DATABASE_NAME + "_test")
    client.close() 