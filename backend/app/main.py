"""
Bravix – FastAPI Main Application Entry Point (Render-ready)
------------------------------------------------------------
Ensures .env loading, CORS setup, and full backend stability on Render.
"""

import os, re
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from dotenv import load_dotenv

# ✅ Load environment variables early (fixes Render OpenAI key issue)
load_dotenv()

# Import routes
from app.routes import (
    upload,
    analyze,
    financial_analysis,
    test_connection,
    report,
)

# -----------------------------------------------------------
# ⚙️ Initialize FastAPI
# -----------------------------------------------------------
app = FastAPI(
    title="Bravix AI Backend",
    version="1.9",
    description="AI-powered financial analysis backend (Render version)",
)

# -----------------------------------------------------------
# 🌐 CORS (Render + local + Vercel frontends)
# -----------------------------------------------------------
ALLOWED_STATIC_ORIGINS = {
    "https://bravix.vercel.app",
    "https://braivix.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

def is_allowed_origin(origin: str) -> bool:
    """Return True if origin is allowed."""
    if not origin:
        return False
    for allowed in ALLOWED_STATIC_ORIGINS:
        if origin.startswith(allowed):
            return True
    return False

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_STATIC_ORIGINS),
    allow_origin_regex=r"https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnsureCORSHeaderMiddleware(BaseHTTPMiddleware):
    """Ensure CORS headers are present even on 500 errors."""
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        try:
            response = await call_next(request)
        except Exception as e:
            print(f"❌ Exception: {e}")
            response = JSONResponse({"error": str(e)}, status_code=500)
        if is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

app.add_middleware(EnsureCORSHeaderMiddleware)

# -----------------------------------------------------------
# 🔀 Include API Routers
# -----------------------------------------------------------
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])
app.include_router(report.router, prefix="/api", tags=["Report Download"])

# -----------------------------------------------------------
# 🌍 Root + Health
# -----------------------------------------------------------
@app.get("/")
def root():
    print("✅ Root accessed. Environment key loaded:", bool(os.getenv("OPENAI_API_KEY")))
    return {"status": "online", "version": "1.9"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "bravix-backend", "version": "1.9"}

@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started successfully on Render.")
    print("🔑 OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY")[:8] + "..." if os.getenv("OPENAI_API_KEY") else "❌ MISSING!")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
