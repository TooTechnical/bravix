"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, analyze, financial_analysis, test_connection

# ✅ Initialize FastAPI application
app = FastAPI(
    title="Bravix AI Backend",
    version="1.1",
    description="AI-powered financial analysis and credit evaluation backend for Bravix.",
)

# ✅ CORS configuration
allowed_origins = [
    "https://bravix.vercel.app",       # Primary frontend
    "https://bravix-ai.vercel.app",    # Alternate frontend domain
    "http://localhost:5173",           # Local development
    "http://127.0.0.1:5173",           # Alternate local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include all route modules under /api prefix
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])

# ✅ Root endpoint for quick testing / health verification
@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is running.")
    return {
        "status": "online",
        "message": "Welcome to Bravix FastAPI backend (Vercel deployment).",
        "version": "1.1",
    }

# ✅ Startup event for logging
@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend is starting up – routes and CORS ready.")

# ✅ Shutdown event for graceful cleanup
@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
