"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, analyze, financial_analysis, test_connection
from starlette.responses import JSONResponse

app = FastAPI(
    title="Bravix AI Backend",
    version="1.2",
    description="AI-powered financial analysis and credit evaluation backend for Bravix.",
)

# ✅ Dynamic and wildcard CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bravix.vercel.app",
        "https://braivix.vercel.app",
    ],
    allow_origin_regex=r"https://bravix(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include API routes
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])

# ✅ Gracefully handle OPTIONS requests (CORS preflights)
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    return JSONResponse(content={"detail": "CORS preflight OK"}, status_code=200)

# ✅ Root endpoint for quick testing / health verification
@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is running.")
    return {
        "status": "online",
        "message": "Welcome to Bravix FastAPI backend (Vercel deployment).",
        "version": "1.2",
    }

@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started with full CORS + preflight support.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
