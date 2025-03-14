from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from ..config import settings

security = HTTPBearer()

def create_token(user_id: str) -> str:
    expires = datetime.utcnow() + timedelta(days=1)
    data = {"user_id": user_id, "exp": expires}
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")

async def get_current_user(credentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token") 