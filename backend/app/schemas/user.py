# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional # Use Optional for Python 3.9+ if not using | None syntax

# Shared properties for user input
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50) # Example constraints

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8) # Password is required and must be at least 8 chars

# Properties to receive via API on update (not used in auth step, but good to have)
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)

# Properties shared by models stored in DB - this is what we return FROM the DB
class UserInDBBase(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    # Pydantic V2: from_attributes = True for ORM mode
    # Pydantic V1: class Config: orm_mode = True
    model_config = {"from_attributes": True}


# Additional properties to return to client
class User(UserInDBBase):
    pass # No extra fields for now

# Additional properties stored in DB but not usually returned to client
class UserInDB(UserInDBBase):
    hashed_password: str