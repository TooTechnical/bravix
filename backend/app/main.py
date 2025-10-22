import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request, Header, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routes import financial_analysis, upload, analyze
from dotenv import load_dotenv

# -------------------------------------------------
# 1️⃣ Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# 2️⃣ Create FastAPI instance
# -------------------------------------------------
app = FastAPI(
    title="Bravix API",
    version="1.4",
    description="Secure backend for Bravix Financial Analysis & AI Demo",
)

# -------------------------------------------------
# 3️⃣ CORS Configuration (Dynamic + Static)
# -------------------------------------------------
STATIC_ALLOWED_ORIGINS = [
    "https://bravix-ai.vercel.app",
    "https://bravix-pi.vercel.app",
    "https://bravix.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

def is_allowed_origin(origin: str) -> bool:
    """Allow dynamic Vercel previews automatically."""
    if not origin:
        return False
    if origin.endswith(".vercel.app"):
        return True
    return origin in STATIC_ALLOWED_ORIGINS

@app.middleware("http")
async def dynamic_cors_middleware(request: Request, call_next):
    """
    Dynamically attach CORS headers so OPTIONS never fails
    even before reaching the route logic.
    """
    # Handle preflight requests immediately
    if request.method == "OPTIONS":
        origin = request.headers.get("origin")
        from fastapi.responses import Response
        response = Response()
        if origin and is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-API-Key, x-api-key"
            )
        return response

    # For normal requests
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin and is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Add base middleware for safety — ensures CORS always passes through
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 4️⃣ API Key Security
# -------------------------------------------------
API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"

async def verify_api_key(x_api_key: str = Header(None)):
    """Ensures each request includes the correct API key."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# -------------------------------------------------
# 5️⃣ Include Routers (Financial + Upload + Analyze)
# -------------------------------------------------
app.include_router(
    financial_analysis.router,
    prefix="/api/financial",
    tags=["Financial Analysis"],
    dependencies=[Depends(verify_api_key)],
)

app.include_router(
    upload.router,
    prefix="/api",
    tags=["File Upload"],
    dependencies=[Depends(verify_api_key)],
)

app.include_router(
    analyze.router,
    prefix="/api",
    tags=["AI Analysis"],
    dependencies=[Depends(verify_api_key)],
)

# -------------------------------------------------
# 6️⃣ Alias route (for backward compatibility)
# -------------------------------------------------
alias_router = APIRouter()

@alias_router.post("/api/financial-analysis")
async def alias_financial_analysis(payload: dict, x_api_key: str = Header(None)):
    """
    Redirects /api/financial-analysis requests to /api/financial/financial-analysis.
    """
    try:
        from app.routes.financial_analysis import financial_analysis
        return await financial_analysis(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alias route failed: {str(e)}")

app.include_router(alias_router)

# -------------------------------------------------
# 7️⃣ Utility & Health Check Endpoints
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "Bravix Demo API running (Dynamic CORS + API Key Secured)"}

@app.get("/debug-cors")
async def debug_cors(request: Request):
    origin = request.headers.get("origin")
    return {
        "your_origin_header": origin,
        "allowed_origins": STATIC_ALLOWED_ORIGINS + ["*.vercel.app"],
        "message": "Dynamic CORS and API key system active",
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Bravix.AI backend healthy"}
