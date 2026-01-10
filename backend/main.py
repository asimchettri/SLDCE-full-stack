from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import engine, Base
from api.routes import datasets, samples , models , experiments , detection , suggestions ,feedback

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Self-Learning Data Correction Engine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    datasets.router,
    prefix=f"{settings.API_V1_PREFIX}/datasets",
    tags=["datasets"]
)

# ← Add samples router
app.include_router(
    samples.router,
    prefix=f"{settings.API_V1_PREFIX}/samples",
    tags=["samples"]
)

app.include_router(
    models.router,
    prefix=f"{settings.API_V1_PREFIX}/models",
    tags=["models"]
)

app.include_router(
    experiments.router,
    prefix=f"{settings.API_V1_PREFIX}/experiments",
    tags=["experiments"]
)

app.include_router(
    detection.router,
    prefix=f"{settings.API_V1_PREFIX}/detection",
    tags=["detection"]
)

app.include_router(
    suggestions.router,
    prefix=f"{settings.API_V1_PREFIX}/suggestions",
    tags=["suggestions"]
)

app.include_router(
    feedback.router,
    prefix=f"{settings.API_V1_PREFIX}/feedback",
    tags=["feedback"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SLDCE API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}