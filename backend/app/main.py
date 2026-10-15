import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api.routes import memories, agents, search, analytics, onboarding
from app.core.config import settings
from app.db.qdrant import init_qdrant

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_qdrant()
    yield


app = FastAPI(
    title="Agent Memory OS",
    description="Persistent memory layer for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled request error: %s %s", request.method, request.url.path)
    origin = request.headers.get("origin")
    allowed_origins = {
        *settings.ALLOWED_ORIGINS,
        "https://agent-memory-frontend.onrender.com",
        "https://agent-memory-os-frontend.onrender.com",
    }
    headers = {}
    if origin in allowed_origins:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return JSONResponse(
        status_code=500,
        content={"detail": "The backend could not complete the request. Check the Render logs."},
        headers=headers,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        *settings.ALLOWED_ORIGINS,
        "https://agent-memory-frontend.onrender.com",
        "https://agent-memory-os-frontend.onrender.com",
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memories.router, prefix="/api/v1/memories", tags=["memories"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
