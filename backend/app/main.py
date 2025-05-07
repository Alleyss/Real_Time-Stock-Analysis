# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import engine, Base
from app.api.routers import auth, wishlist, stocks # <<< IMPORT & INCLUDE stocks router
from app.sentiment_model_loader import load_sentiment_model
import logging

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Application Startup...")
    try:
        log.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        log.info("Database tables checked/created.")
    except Exception as e: log.error(f"Database creation failed: {e}")
    log.info("Loading sentiment model...")
    load_sentiment_model()
    log.info("Sentiment model loading process initiated.")
    yield
    log.info("Application Shutdown...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root(): return {"message": f"Welcome to the {settings.PROJECT_NAME}!"}

# --- Include Routers ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(wishlist.router, prefix="/api/v1/wishlist", tags=["Wishlist"])
app.include_router(stocks.router, prefix="/api/v1/stocks", tags=["Stocks & Sentiment"]) # <<< INCLUDE ROUTER

# --- CORS Middleware ---
from fastapi.middleware.cors import CORSMiddleware
origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)