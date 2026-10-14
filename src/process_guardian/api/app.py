"""FastAPI application factory for Process Guardian Service Layer."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from process_guardian.api.dependencies import get_service_container
from process_guardian.api.routes import ingestion, process, quality, interventions, recovery, demo, evidence, economics, qc, counterfactual, scenarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context ensuring database schema and seed data are initialized."""
    container = get_service_container()
    yield
    # Shutdown cleanups if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Process Guardian Closed-Loop Intervention Engine API",
        version="1.0.0",
        description="Vendor-neutral injection molding intervention engine providing early drift detection, calibrated risk prediction, constrained intervention optimization, recovery verification, and scrap containment.",
        lifespan=lifespan,
    )

    # CORS configuration for UI connection
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health Check
    @app.get("/api/health", tags=["System"])
    def health_check():
        container = get_service_container()
        return {
            "status": "HEALTHY",
            "service": "process-guardian-engine",
            "version": "1.0.0",
            "database": container.db_path,
            "machine_id": container.machine_id,
            "state": container.orchestrator.current_state.value if container.orchestrator else "UNKNOWN",
        }

    # Register API Routers
    app.include_router(ingestion.router, prefix="/api")
    app.include_router(process.router, prefix="/api")
    app.include_router(quality.router, prefix="/api")
    app.include_router(interventions.router, prefix="/api")
    app.include_router(recovery.router, prefix="/api")
    app.include_router(demo.router, prefix="/api")
    app.include_router(evidence.router, prefix="/api")
    app.include_router(economics.router, prefix="/api")
    app.include_router(qc.router, prefix="/api")
    app.include_router(counterfactual.router, prefix="/api")
    app.include_router(scenarios.router, prefix="/api")

    return app


app = create_app()
