from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.routes import memories, agents, search, analytics
from app.core.config import settings
from app.db.qdrant import init_qdrant


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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
