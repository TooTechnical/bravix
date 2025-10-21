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
    version="1.3",
    description="Secure backend for Bravix Financial Analysis & AI Demo",
)

# -------------------------------------------------
# 3️⃣ CORS configuration (allow all temporarily for testing)
# -------------------------------------------------
# ⚠️ While debugging CORS in Render/Vercel, it's best to allow all origins.
# Once confirmed working, replace ["*"] with your explicit domains.
ALLOWED_ORIGINS = [
    "https://bravix-ai.vercel.app",
    "https://bravix-pi.vercel.app",
    "https://bravix.vercel.app",
    "https://bravix-bsjlvikyb-tootechnicals-projects.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],  # fallback for safety
    allow_credentials=True,
    allow_methods=["*"],  # include OPTIONS automatically
    allow_headers=["*"],  # includes Content-Type, x-api-key, etc.
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
    return {"message": "Bravix Demo API running (CORS + API Key Secured)"}

@app.get("/debug-cors")
async def debug_cors(request: Request):
    origin = request.headers.get("origin")
    return {
        "your_origin_header": origin,
        "allowed_origins": ALLOWED_ORIGINS,
        "message": "CORS and API key system active",
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Bravix.AI backend healthy"}
