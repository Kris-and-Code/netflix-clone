from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import auth, content, user
from .utils.db import connect_to_mongo, close_mongo_connection
from .config import get_settings

settings = get_settings()

app = FastAPI(title="Netflix Clone API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.client_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(user.router, prefix="/api/user", tags=["User"]) 