"""
Bravix – FastAPI Main Application Entry Point
---------------------------------------------
Handles API routing, middleware, and startup configuration for Vercel deployment.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from app.routes import upload, analyze, financial_analysis, test_connection

app = FastAPI(
    title="Bravix AI Backend",
    version="1.3",
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
    allow_origin_regex=r"https://bravix(-[a-zA-Z0-9-]+)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routers
app.include_router(upload.router, prefix="/api", tags=["File Upload"])
app.include_router(analyze.router, prefix="/api", tags=["AI Analysis"])
app.include_router(financial_analysis.router, prefix="/api", tags=["Financial Indicators"])
app.include_router(test_connection.router, prefix="/api", tags=["Health Check"])

# ✅ Fix: handle preflight requests directly
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    """
    Handles OPTIONS requests (CORS preflight) for all paths.
    """
    print(f"🌀 Preflight CORS request for: /{full_path}")
    return JSONResponse(
        content={"detail": f"CORS preflight accepted for /{full_path}"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, X-API-Key, x-api-key",
        },
        status_code=200,
    )

@app.get("/")
def root():
    print("🌐 Root endpoint accessed – backend is running.")
    return {
        "status": "online",
        "message": "Welcome to Bravix FastAPI backend (Vercel deployment).",
        "version": "1.3",
    }

@app.on_event("startup")
def on_startup():
    print("🚀 Bravix backend started with universal CORS preflight handler.")

@app.on_event("shutdown")
def on_shutdown():
    print("🛑 Bravix backend shutting down gracefully.")
