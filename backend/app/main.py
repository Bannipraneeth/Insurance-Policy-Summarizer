"""
FastAPI Main Application.
AI-Based Policy & T&C Summarization System Backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.database import init_db
from app.api import documents_router, summaries_router, export_router, feedback_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Policy Summarizer API",
    description="AI-Based Policy & T&C Summarization System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router)
app.include_router(summaries_router)
app.include_router(export_router)
app.include_router(feedback_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting Policy Summarizer API...")
    init_db()
    logger.info("Database initialized")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Policy Summarizer API",
        "version": "1.0.0",
        "description": "AI-Based Policy & T&C Summarization System",
        "docs": "/docs",
        "endpoints": {
            "documents": "/api/documents",
            "summaries": "/api/summaries",
            "export": "/api/export",
            "feedback": "/api/feedback"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
