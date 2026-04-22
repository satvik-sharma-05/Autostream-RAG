"""FastAPI application entry point."""
import os
import time
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

_startup_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load KB and build agent graph."""
    global _startup_time
    t0 = time.time()
    logger.info("Starting AutoStream backend...")
    load_knowledge_base()
    await build_graph()
    _startup_time = time.time() - t0
    logger.info(f"AutoStream backend ready in {_startup_time:.1f}s.")
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

# CORS — allow all origins in production so Vercel frontend works
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
cors_origins = ["*"] if cors_origins_raw == "*" else cors_origins_raw.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(leads.router, prefix="/api/v1", tags=["Leads"])
app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])


@app.get("/health")
async def health():
    """Health check — Render pings this to confirm the service is up."""
    return {
        "status": "ok",
        "service": "AutoStream Agent API",
        "startup_seconds": round(_startup_time, 1),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
