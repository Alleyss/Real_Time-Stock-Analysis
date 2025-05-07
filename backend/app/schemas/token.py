# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional # Or use `str | None` for Python 3.10+

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    # This will store the identifier from the JWT (e.g., username or email)
    identifier: Optional[str] = None