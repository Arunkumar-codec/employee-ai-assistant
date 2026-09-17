"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
(from inside the backend/ directory)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="RAG + Agentic Employee Assistant (Day 1 foundation)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "docs": "/docs"}
