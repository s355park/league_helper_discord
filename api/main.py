"""FastAPI application entry point."""
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import users, teams
from config import Config

# Set up logging to file with forced flushing
file_handler = logging.FileHandler('api_debug.log', mode='w')
file_handler.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[file_handler, stream_handler],
    force=True
)

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# Force immediate flush
for handler in logging.root.handlers:
    handler.flush()

# Disable output buffering for immediate logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your .env file")

app = FastAPI(
    title="Discord League Team Generator API",
    description="API for generating balanced League of Legends teams",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("[FastAPI] SERVER STARTED")
    logger.info("[FastAPI] Middleware is active")
    logger.info("[FastAPI] Listening on http://127.0.0.1:8000")
    logger.info("=" * 60)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"[FastAPI] GLOBAL EXCEPTION HANDLER caught: {exc}")
    logger.error(f"[FastAPI] Request: {request.method} {request.url.path}")
    import traceback
    logger.error(f"[FastAPI] Full traceback:\n{traceback.format_exc()}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Log all requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"[FastAPI] Incoming {request.method} request to {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"[FastAPI] Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"[FastAPI] ERROR in middleware: {e}")
        import traceback
        logger.error(f"[FastAPI] Full traceback:\n{traceback.format_exc()}")
        raise

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(teams.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Discord League Team Generator API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)

