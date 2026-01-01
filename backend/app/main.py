from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config.database import connect_to_mongo, close_mongo_connection
from app.config.settings import settings
from app.utils.logger import logger
import os
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.rate_limiter import limiter

# Import routes (will be created)
# from app.routes import auth, chat, crm

# Import workers
# Summarizer removed - using MongoDB triggers instead

# Import RAG initialization
from app.services.rag.vector_store import vector_store
from app.services.rag.embedding_service import embedding_service

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Abbotsford Road Coffee Specialists - AI Chatbot and CRM System"
)

# Rate Limiting Setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL, 
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Abbotsford API...")
    
    # Verify API key is loaded correctly
    api_key = settings.OPENAI_API_KEY
    if api_key:
        masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 11 else "***"
        logger.info(f"✅ OpenAI API Key loaded: {masked_key}")
        if api_key.endswith("920A"):
            logger.error("❌ INVALID API KEY: Using old key ending in 920A!")
            logger.error("❌ Please update backend/.env with correct OPENAI_API_KEY")
            raise ValueError("Invalid OpenAI API key - update .env file")
    else:
        logger.error("❌ OPENAI_API_KEY not found in environment!")
        raise ValueError("OPENAI_API_KEY not configured")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Initialize RAG services
    logger.info("Initializing RAG services...")
    embedding_service.initialize_model()
    vector_store.load_index()
    
    # Background worker removed - using MongoDB triggers instead
    
    logger.info("✅ Abbotsford API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Abbotsford API...")
    await close_mongo_connection()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "message": "Abbotsford API is running",
        "version": "1.0.0",
        "status": "healthy",
        "database": "connected",
        "rag": {
            "embedding_model": "loaded",
            "vector_store_size": vector_store.get_index_size()
        }
    }


# Include routers
from app.routes import chat, auth, crm, heygen

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
app.include_router(heygen.router, prefix="/api/heygen", tags=["HeyGen"])

# Serve static files (frontend build)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    # Mount static files for assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    
    # Catch-all route for SPA - must be last
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes"""
        # If it's a file request (has extension), try to serve it
        if "." in full_path.split("/")[-1]:
            file_path = os.path.join(static_dir, full_path)
            if os.path.exists(file_path):
                return FileResponse(file_path)
        
        # Otherwise serve index.html for client-side routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        
        return {"message": "Frontend not built yet. Run: cd frontend && npm run build"}


if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Cloud Run compatibility, default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        reload_excludes=["**/test_*.py", "**/*_test.py"] if settings.DEBUG else None
    )
