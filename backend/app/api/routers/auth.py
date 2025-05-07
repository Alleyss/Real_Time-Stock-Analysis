# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Standard form for username/password
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas import user as user_schemas
from app.schemas import token as token_schemas
from app.crud import crud_user
from app.core import security
from app.core.config import settings
from app.api import deps # Import your dependencies

router = APIRouter()

@router.post("/register", response_model=user_schemas.User) # Or /signup
def register_user(
    *, # Enforces keyword-only arguments after this
    db: Session = Depends(get_db),
    user_in: user_schemas.UserCreate,
):
    """
    Create new user.
    """
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    if user_in.username: # If username is provided, check if it exists
        user_by_username = crud_user.get_user_by_username(db, username=user_in.username)
        if user_by_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this username already exists in the system.",
            )
            
    new_user = crud_user.create_user(db=db, user=user_in)
    return new_user


@router.post("/token", response_model=token_schemas.Token) # Or /login
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # FastAPI injects form data
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Username in OAuth2PasswordRequestForm will be the email.
    """
    # form_data.username will contain the email entered by the user
    user = crud_user.get_user_by_email(db, email=form_data.username) 
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = security.create_access_token(
        subject=user.email # Use email as the JWT subject
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example of a protected endpoint
@router.get("/me", response_model=user_schemas.User)
async def read_users_me(
    current_user: user_schemas.User = Depends(deps.get_current_active_user)
):
    """
    Get current logged-in user.
    """
    return current_user