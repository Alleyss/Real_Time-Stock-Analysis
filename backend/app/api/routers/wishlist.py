# app/api/routers/wishlist.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List # For List response model

from app.db.database import get_db
from app.schemas import wishlist as wishlist_schemas # Your Pydantic wishlist schemas
from app.db import models as db_models # Your SQLAlchemy models
from app.crud import crud_wishlist # Your wishlist CRUD functions
from app.api import deps # Your dependencies, especially get_current_active_user

router = APIRouter()

@router.post("/", response_model=wishlist_schemas.WishlistItem, status_code=status.HTTP_201_CREATED)
def add_stock_to_wishlist(
    *,
    db: Session = Depends(get_db),
    item_in: wishlist_schemas.WishlistItemCreate,
    current_user: db_models.User = Depends(deps.get_current_active_user)
):
    """
    Add a stock to the current user's wishlist.
    """
    # Convert ticker to uppercase for consistent checking and storage
    ticker_upper = item_in.ticker_symbol.upper()
    
    existing_item = crud_wishlist.get_wishlist_item(db, user_id=current_user.id, ticker_symbol=ticker_upper)
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker {ticker_upper} is already in your wishlist."
        )
    
    # Update item_in with uppercase ticker before passing to CRUD
    item_in_processed = wishlist_schemas.WishlistItemCreate(ticker_symbol=ticker_upper)
    wishlist_item = crud_wishlist.add_item_to_wishlist(db=db, item=item_in_processed, user_id=current_user.id)
    return wishlist_item

@router.get("/", response_model=List[wishlist_schemas.WishlistItem]) # Return a list of items
def read_user_wishlist(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: db_models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve the current user's wishlist.
    """
    wishlist_items = crud_wishlist.get_wishlist_items_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return wishlist_items

@router.delete("/{ticker_symbol}", response_model=wishlist_schemas.WishlistItem)
def remove_stock_from_wishlist(
    *,
    db: Session = Depends(get_db),
    ticker_symbol: str,
    current_user: db_models.User = Depends(deps.get_current_active_user)
):
    """
    Remove a stock from the current user's wishlist.
    """
    # Convert ticker to uppercase for consistent checking
    ticker_upper = ticker_symbol.upper()
    
    deleted_item = crud_wishlist.remove_item_from_wishlist(db, user_id=current_user.id, ticker_symbol=ticker_upper)
    if not deleted_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker {ticker_upper} not found in your wishlist."
        )
    return deleted_item

# Optional: Get a specific wishlist item (might not be needed if GET / already returns enough detail)
@router.get("/{ticker_symbol}", response_model=wishlist_schemas.WishlistItem)
def read_specific_wishlist_item(
    *,
    db: Session = Depends(get_db),
    ticker_symbol: str,
    current_user: db_models.User = Depends(deps.get_current_active_user)
):
    """
    Check if a specific stock is in the current user's wishlist.
    """
    ticker_upper = ticker_symbol.upper()
    item = crud_wishlist.get_wishlist_item(db, user_id=current_user.id, ticker_symbol=ticker_upper)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker {ticker_upper} not found in your wishlist."
        )
    return item