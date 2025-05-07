# app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For server-side default timestamps
from app.db.database import Base # Import Base from our database.py
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # Username can be optional or made unique and required like email
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True) # For deactivating accounts
    
    # Using server_default=func.now() makes the DB handle timestamp generation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # onupdate=func.now() updates the timestamp automatically on record update
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to WishlistItems
    # 'back_populates' links this relationship to the 'owner' attribute in WishlistItem
    wishlist_items = relationship("WishlistItem", back_populates="owner", cascade="all, delete-orphan")

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String, index=True, nullable=False)
    # Foreign Key to link to the User table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to User
    # 'back_populates' links this relationship to the 'wishlist_items' attribute in User
    owner = relationship("User", back_populates="wishlist_items")

    # To ensure a user can only add a ticker once to their wishlist:
    # from sqlalchemy.schema import UniqueConstraint
    # __table_args__ = (UniqueConstraint('user_id', 'ticker_symbol', name='_user_ticker_uc'),)