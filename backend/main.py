"""
main.py — CancerCopilot FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.database import engine, Base

# Import all models so Alembic/SQLAlchemy sees them
import models  # noqa: F401

# Routes
from api.routes import auth, cases, clinical, analysis, reports, pdf, analytics, notifications, second_opinion

# ─── Rate limiter ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dev only: auto-create tables (use Alembic in production)
    if settings.app_env == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="OnCopilot API",
    description="Clinical decision-support system for oncology.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail, "detail": str(exc.detail), "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc), "code": 500},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(clinical.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(pdf.router)
app.include_router(analytics.router)
app.include_router(notifications.router)
app.include_router(second_opinion.router)


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "CancerCopilot API", "version": "1.0.0"}


# ─── Dev: Dataset validation stats ───────────────────────────────────────────
if settings.app_env == "development":
    @app.get("/api/dev/dataset-stats", tags=["dev"])
    async def dataset_stats():
        from engine.biomarker_algorithm import validate_against_dataset
        return validate_against_dataset()


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
