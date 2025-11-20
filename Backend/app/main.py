from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.routers import modules, training, auth, user_management, Reports, leaderboard, progress
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="E-Learning Comics API",
    description="Comic-based English learning with AI",
    version="2.0.0"
)

# CORS Configuration - MUST BE BEFORE ROUTERS!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Added for current frontend port
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",  # Added for current frontend port
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # expose_headers=["*"]
)

# Include routers
app.include_router(auth.router)
app.include_router(modules.router)
app.include_router(training.router)
app.include_router(user_management.router)
app.include_router(Reports.router)
app.include_router(leaderboard.router)
app.include_router(progress.router, prefix="/api")


logger.info("✅ All routers registered")

@app.get("/")
async def root():
    return {
        "message": "E-Learning Comics API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Application started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)