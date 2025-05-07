# app/crud/crud_user.py
from sqlalchemy.orm import Session
from app.db import models # Import your SQLAlchemy models
from app.schemas import user as user_schemas # Import your Pydantic user schemas
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: user_schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username, # Make sure username is handled if optional
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user) # Refresh to get DB-generated values like ID, created_at
    return db_user

def update_user(db: Session, db_user: models.User, user_in: user_schemas.UserUpdate) -> models.User:
    user_data = user_in.model_dump(exclude_unset=True) # Pydantic V2, V1: user_in.dict(...)
    if "password" in user_data and user_data["password"]: # If password is provided for update
        hashed_password = get_password_hash(user_data["password"])
        db_user.hashed_password = hashed_password
    
    # Update other fields
    if "email" in user_data:
        db_user.email = user_data["email"]
    if "username" in user_data:
        db_user.username = user_data["username"]
    if "is_active" in user_data: # Example if you add is_active to UserUpdate
        db_user.is_active = user_data["is_active"]
        
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Add activate/deactivate user functions if needed
# def activate_user(db: Session, db_user: models.User) -> models.User: ...
# def deactivate_user(db: Session, db_user: models.User) -> models.User: ...