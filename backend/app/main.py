"""
Smart Waste Segregation and Recycling Recommendation System - FastAPI Main Application.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.database.connection import db_manager
from backend.app.api.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events: startup and graceful shutdown."""
    logger.info("Initializing Smart Waste Segregation API server...")
    # Initialize database
    await db_manager.connect()
    logger.info(f"Database status: {db_manager.get_status()}")
    
    yield
    
    logger.info("Shutting down API server...")
    await db_manager.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent AI-driven waste segregation, multi-object detection, localized recycling guidance, and carbon/energy impact estimation.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Static File Mount for uploaded and annotated images
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Mount built React frontend if available
if settings.FRONTEND_DIST.exists():
    app.mount("/ui", StaticFiles(directory=str(settings.FRONTEND_DIST), html=True), name="ui")

# 3. Include API Routers under /api
app.include_router(api_router, prefix=settings.API_V1_STR)


# 4. Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        errors.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": errors}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please try again later."}
    )


# 5. Root Entry Point
@app.get("/", tags=["Root"])
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "analyze": f"{settings.API_V1_STR}/analyze",
            "history": f"{settings.API_V1_STR}/history",
            "analytics": f"{settings.API_V1_STR}/analytics",
            "health": f"{settings.API_V1_STR}/health",
            "auth_register": f"{settings.API_V1_STR}/auth/register",
            "auth_login": f"{settings.API_V1_STR}/auth/login",
            "ui": "/ui" if settings.FRONTEND_DIST.exists() else None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

