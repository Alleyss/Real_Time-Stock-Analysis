# app/crud/crud_wishlist.py
from sqlalchemy.orm import Session
from app.db import models # Your SQLAlchemy models (User, WishlistItem)
from app.schemas import wishlist as wishlist_schemas # Your Pydantic wishlist schemas

def get_wishlist_item(db: Session, user_id: int, ticker_symbol: str) -> models.WishlistItem | None:
    """
    Get a specific wishlist item for a user by ticker symbol.
    """
    return db.query(models.WishlistItem).filter(
        models.WishlistItem.user_id == user_id,
        models.WishlistItem.ticker_symbol == ticker_symbol.upper() # Store/check tickers consistently (e.g., uppercase)
    ).first()

def get_wishlist_items_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[models.WishlistItem]:
    """
    Get all wishlist items for a specific user.
    """
    return db.query(models.WishlistItem).filter(models.WishlistItem.user_id == user_id).offset(skip).limit(limit).all()

def add_item_to_wishlist(db: Session, item: wishlist_schemas.WishlistItemCreate, user_id: int) -> models.WishlistItem:
    """
    Add a new stock ticker to a user's wishlist.
    Ensures ticker is stored in uppercase.
    """
    db_item = models.WishlistItem(
        ticker_symbol=item.ticker_symbol.upper(), # Store consistently
        user_id=user_id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def remove_item_from_wishlist(db: Session, user_id: int, ticker_symbol: str) -> models.WishlistItem | None:
    """
    Remove a stock ticker from a user's wishlist.
    Returns the item that was deleted, or None if not found.
    """
    db_item = get_wishlist_item(db, user_id=user_id, ticker_symbol=ticker_symbol.upper())
    if db_item:
        db.delete(db_item)
        db.commit()
        return db_item
    return None