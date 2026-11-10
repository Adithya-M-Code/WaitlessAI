"""
FastAPI Main Application Entry Point for Waitless AI.
Configures CORS, life-cycle handlers, consistent error management, and mounts all route modules.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import (
    routes,
    vehicles,
    prediction,
    journey,
    recommend,
    explain,
    whatif,
    health_index,
    arena,
    feedback,
    admin,
    places,
    plan,
    shapes,
    streams,
    labs
)
from backend.models_runtime.registry import ModelRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure baseline registry is loaded
    reg = ModelRegistry()
    _ = reg.get_registry()
    yield
    # Shutdown

app = FastAPI(
    title="Waitless AI API",
    version="2.0.0",
    description="Reliability, Crowd, and Disruption Intelligence for Chennai Buses (MTC)",
    lifespan=lifespan
)

# CORS Configuration
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", tags=["Health"])
def health():
    reg = ModelRegistry()
    return {
        "status": "ok",
        "version": "2.0.0",
        "champion_delay": reg.get_champion_id("delay"),
        "champion_crowd": reg.get_champion_id("crowding"),
        "data_mode": os.getenv("DATA_MODE", "synthetic"),
        "torch_available": True
    }

# Mount modular routers
app.include_router(routes.router)
app.include_router(vehicles.router)
app.include_router(prediction.router)
app.include_router(journey.router)
app.include_router(recommend.router)
app.include_router(explain.router)
app.include_router(whatif.router)
app.include_router(health_index.router)
app.include_router(arena.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(places.router)
app.include_router(plan.router)
app.include_router(shapes.router)
app.include_router(streams.router)
app.include_router(labs.router)

