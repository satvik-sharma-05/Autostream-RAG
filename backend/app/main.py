"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.routes import chat, leads, webhooks
from app.core.agent import build_graph
from app.core.rag import load_knowledge_base
from app.utils.rate_limiter import limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load KB and build agent graph."""
    logger.info("Starting AutoStream backend...")
    load_knowledge_base()
    await build_graph()
    logger.info("AutoStream backend ready.")
    yield
    logger.info("Shutting down AutoStream backend.")


app = FastAPI(
    title="AutoStream Agent API",
    description="AI-powered lead generation agent for AutoStream video editing SaaS",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(leads.router, prefix="/api/v1", tags=["Leads"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AutoStream Agent API"}
