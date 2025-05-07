# app/schemas/wishlist.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Properties to receive when adding an item to the wishlist
class WishlistItemCreate(BaseModel):
    ticker_symbol: str = Field(..., examples=["AAPL"], description="Stock ticker symbol to add to wishlist")

# Properties of a wishlist item as stored in DB and returned to client
class WishlistItemBase(BaseModel):
    id: int
    ticker_symbol: str
    added_at: datetime
    # Pydantic V2: from_attributes = True for ORM mode
    model_config = {"from_attributes": True}


class WishlistItem(WishlistItemBase):
    pass # No extra fields for now

# For returning a list of wishlist items
class Wishlist(BaseModel):
    items: list[WishlistItem]
    total: int