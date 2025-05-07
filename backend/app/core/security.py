# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union # Union for Python < 3.10, use | for 3.10+
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.schemas.token import TokenData # Import TokenData schema
from fastapi import HTTPException, status

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)} # "sub" is the standard claim for subject (e.g., user ID or email)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> TokenData | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 'sub' claim will be our identifier (e.g., email)
        identifier: str | None = payload.get("sub")
        if identifier is None:
            # Standard practice: raise an error if 'sub' is missing
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials (missing subject)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenData(identifier=identifier)
    except JWTError:
        # This catches expired tokens, invalid signatures, etc.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials (invalid token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return None # Should not be reached if exceptions are raised