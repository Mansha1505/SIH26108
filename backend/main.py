from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import recommendation, documents, reports
from backend.services.recommendation_service import service_instance
from backend.utils.logger import get_logger

logger = get_logger("Main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup & shutdown lifespan handler.
    Pre-indexes corpus on startup for fast endpoint response times.
    """
    logger.info("Initializing SIH26108 Standards Recommendation Engine Backend...")
    service_instance.initialize()
    logger.info("Pre-indexing complete. Backend ready to serve requests.")
    yield
    logger.info("Shutting down backend service.")

app = FastAPI(
    title="SIH26108 - Indian Standards Recommendation Engine API",
    description=(
        "AI-assisted recommendation system for identifying applicable Indian Standards (IS/BIS) "
        "for procurement specifications. This system provides search relevance recommendations "
        "and is NOT a legal compliance engine."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendation.router)
app.include_router(documents.router)
app.include_router(reports.router)


@app.get("/", summary="Root endpoint")
async def root():
    return {
        "message": "Welcome to SIH26108 Indian Standards Recommendation API",
        "docs": "/docs",
        "health": "/api/health",
        "recommend_endpoint": "/api/recommend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
