"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import re

# Import routes
from app.routes import (
    upload,
    analyze,
    financial_analysis,
    test_connection,
    report,  # ✅ includes /api/report/download for PDF export
)

# -----------------------------------------------------------
# ⚙️ Initialize FastAPI
# -----------------------------------------------------------
app = FastAPI(
    title="Bravix AI Backend",
    version="1.8",
    description="AI-powered financial analysis and credit evaluation backend for Bravix (Vercel).",
)

# -----------------------------------------------------------
# 🌐 Dynamic CORS Configuration (supports all Vercel preview URLs)
# -----------------------------------------------------------
ALLOWED_STATIC_ORIGINS = {
    "https://bravix.vercel.app",
    "https://braivix.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

VERCEL_REGEX = re.compile(r"^https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app$")

def is_allowed_origin(origin: str) -> bool:
    """Return True if request origin is explicitly or dynamically allowed."""
    return bool(origin and (origin in ALLOWED_STATIC_ORIGINS or VERCEL_REGEX.match(origin)))


# ✅ Base CORS middleware for all normal requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_STATIC_ORIGINS),
    allow_origin_regex=r"https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Extra middleware to ensure CORS headers on 500 errors
class EnsureCORSHeaderMiddleware(BaseHTTPMiddleware):
    """Guarantees that even unhandled exceptions still return valid CORS headers."""

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        try:
            response = await call_next(request)
        except Exception as e:
            print(f"❌ Exception caught: {e}")
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
app.include_router(report.router, prefix="/api", tags=["Report Download"])  # ✅ renamed tag


# -----------------------------------------------------------
# 🧩 Handle Preflight OPTIONS requests globally
# -----------------------------------------------------------
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    """Handle all preflight (OPTIONS) CORS checks globally."""
    origin = request.headers.get("origin", "")
    allow_origin = origin if is_allowed_origin(origin) else "*"
    print(f"🌀 CORS preflight from: {origin} → /{full_path}")

    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, X-API-Key, x-api-key",
            "Access-Control-Allow-Credentials": "true",
        },
    )


# -----------------------------------------------------------
# 🌍 Basic Root + Health Endpoints
# -----------------------------------------------------------
@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is running.")
    return {
        "status": "online",
        "message": "Bravix FastAPI backend active with AI + report PDF generation.",
        "version": "1.8",
    }


@app.get("/health")
def health():
    """Simple uptime check endpoint."""
    return {"status": "ok", "service": "bravix-backend", "version": "1.8"}


# -----------------------------------------------------------
# 🚀 Lifecycle Events
# -----------------------------------------------------------
@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started with AI, CORS, and report generation modules.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
