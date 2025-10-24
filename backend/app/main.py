"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from app.routes import upload, analyze, financial_analysis, test_connection

app = FastAPI(
    title="Bravix AI Backend",
    version="1.4",
    description="AI-powered financial analysis and credit evaluation backend for Bravix (Vercel).",
)

# ✅ CORS configuration — supports all Vercel environments + localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bravix.vercel.app",
        "https://braivix.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://(bravix|braivix)(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routers
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])

# ✅ Universal preflight handler for OPTIONS requests
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    """
    Handles OPTIONS requests (CORS preflight) for all paths.
    """
    origin = request.headers.get("origin", "*")
    print(f"🌀 Preflight CORS request from {origin} for /{full_path}")
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, X-API-Key, x-api-key",
            "Access-Control-Allow-Credentials": "true",
        },
    )

# ✅ Root route
@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is running.")
    return {
        "status": "online",
        "message": "Welcome to Bravix FastAPI backend (Vercel deployment).",
        "version": "1.4",
    }

# ✅ Health check route (for frontend / uptime check)
@app.get("/health")
def health():
    return {"status": "ok", "service": "bravix-backend", "version": "1.4"}

# ✅ Debug upload test route
@app.post("/api/debug-upload")
async def debug_upload(request: Request):
    """
    Simple debug endpoint to confirm upload routing on Vercel.
    """
    print("🧩 Debug upload route hit.")
    try:
        body = await request.body()
        print(f"📦 Received {len(body)} bytes")
        return {"status": "ok", "bytes_received": len(body)}
    except Exception as e:
        print("⚠️ Upload test failed:", str(e))
        return {"status": "error", "message": str(e)}

# ✅ Startup event for diagnostics
@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started with full CORS + preflight + upload debug routes.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
