"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import re

from app.routes import upload, analyze, financial_analysis, test_connection, report

app = FastAPI(
    title="Bravix AI Backend",
    version="1.6",
    description="AI-powered financial analysis and credit evaluation backend for Bravix (Vercel).",
)

# -------------------------------------------------------------------
# ✅ Dynamic CORS configuration — works for all Vercel preview domains
# -------------------------------------------------------------------
ALLOWED_STATIC_ORIGINS = {
    "https://bravix.vercel.app",
    "https://braivix.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

VERCEL_REGEX = re.compile(r"^https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app$")

def is_allowed_origin(origin: str) -> bool:
    if origin in ALLOWED_STATIC_ORIGINS:
        return True
    if origin and VERCEL_REGEX.match(origin):
        return True
    return False

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_origins=list(ALLOWED_STATIC_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# ✅ Routers
# -------------------------------------------------------------------
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])
app.include_router(report.router, prefix="/api", tags=["Report Fetch"])

# -------------------------------------------------------------------
# ✅ Universal OPTIONS handler (handles all preflight requests)
# -------------------------------------------------------------------
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    origin = request.headers.get("origin", "")
    print(f"🌀 CORS preflight from: {origin} -> /{full_path}")

    allow_origin = origin if is_allowed_origin(origin) else "*"
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

# -------------------------------------------------------------------
# ✅ Root + Health
# -------------------------------------------------------------------
@app.get("/")
def root():
    print("🌐 Backend root accessed.")
    return {
        "status": "online",
        "message": "Bravix FastAPI backend active (Vercel-compatible dynamic CORS).",
        "version": "1.6",
    }

@app.get("/health")
def health():
    return {"status": "ok", "service": "bravix-backend", "version": "1.6"}

# -------------------------------------------------------------------
# ✅ Lifecycle hooks
# -------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started with dynamic CORS + AI routes.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Backend shutting down gracefully.")
