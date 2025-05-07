# app/api/deps.py
from typing import Generator # For Python < 3.9, use from typing_extensions import Annotated for Python 3.9+ for Depends type hints
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import security # Your security.py
from app.db import models # Your db/models.py
from app.db.database import SessionLocal, get_db # Your db/database.py
from app.crud import crud_user # Your crud_user.py

# OAuth2PasswordBearer tells FastAPI where to look for the token (e.g., Authorization header)
# tokenUrl should point to your login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token") # Adjust tokenUrl to your actual login path

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = security.decode_access_token(token)
    if not token_data or not token_data.identifier: # identifier is what we stored in 'sub' (e.g., email)
        raise credentials_exception
    
    # Assuming identifier is the email. Adjust if you use username or user ID.
    user = crud_user.get_user_by_email(db, email=token_data.identifier)
    if user is None:
        raise credentials_exception
    if not user.is_active: # Optional: check if user is active
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    # This is a simple wrapper if you only want to ensure the user from get_current_user is active
    # The active check is already in get_current_user, but this makes it explicit for routes.
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user