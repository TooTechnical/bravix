"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

import re, os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# 🧩 Import all routes
from app.routes import (
    upload,
    analyze,
    financial_analysis,
    test_connection,
    report,  # ✅ includes /api/report/download
)

# -----------------------------------------------------------
# ⚙️ Initialize FastAPI
# -----------------------------------------------------------
app = FastAPI(
    title="Bravix AI Backend",
    version="1.9",
    description="AI-powered financial analysis, rating classification, and PDF report generation for Bravix.",
)

# -----------------------------------------------------------
# 🌐 Dynamic CORS Configuration
# -----------------------------------------------------------
ALLOWED_STATIC_ORIGINS = {
    # ✅ Official production domains
    "https://bravix.vercel.app",
    "https://braivix.vercel.app",
    # ✅ Common Vercel preview + localhost
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

# ✅ Regex match for any Vercel preview deployment
VERCEL_REGEX = re.compile(r"^https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app$")

def is_allowed_origin(origin: str) -> bool:
    return bool(origin and (origin in ALLOWED_STATIC_ORIGINS or VERCEL_REGEX.match(origin)))

# ✅ Global CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_STATIC_ORIGINS),
    allow_origin_regex=r"https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Always-add-CORS middleware even on internal 500 errors
class EnsureCORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        try:
            response = await call_next(request)
        except Exception as e:
            print(f"❌ Exception caught by middleware: {e}")
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
# 🧩 Handle Preflight OPTIONS
# -----------------------------------------------------------
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
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
# 🌍 Root + Health Endpoints
# -----------------------------------------------------------
@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is live.")
    return {
        "status": "online",
        "message": "Bravix backend running with full AI, CORS, and PDF reporting.",
        "version": "1.9",
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "bravix-backend", "version": "1.9"}

# -----------------------------------------------------------
# 🚀 Lifecycle Events
# -----------------------------------------------------------
@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started successfully with all modules active.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
