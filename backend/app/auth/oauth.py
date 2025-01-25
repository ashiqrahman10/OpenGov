from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import aiohttp
from typing import Optional
from .. import models, schemas, database
from ..config import settings
from .utils import create_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def verify_google_token(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="Invalid Google token")
            user_data = await response.json()
            return user_data

async def get_or_create_user(db: Session, email: str, auth_provider: str = "google") -> models.User:
    # Check if user exists
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        # Create new user
        user = models.User(
            email=email,
            auth_provider=auth_provider,
            is_active=True,
            role="user",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

async def authenticate_google_user(token: str, db: Session):
    # Verify Google token
    user_data = await verify_google_token(token)
    email = user_data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Invalid email from Google")
    
    # Get or create user
    user = await get_or_create_user(db, email)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    }

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    if not token:
        return None
        
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
            
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None

# Add this function for optional authentication
async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> Optional[models.User]:
    return await get_current_user(token, db)