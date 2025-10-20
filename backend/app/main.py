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
# 3️⃣ CORS configuration (Restricted + Local Dev)
# -------------------------------------------------
ALLOWED_ORIGINS = [
    "https://bravix.vercel.app",
    "https://bravix-pi.vercel.app",
    "https://bravix-1rr5nkf0f-tootechnicals-projects.vercel.app",
    "https://bravix-nxch5n4g6-tootechnicals-projects.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 4️⃣ Simple API Key Security Layer
# -------------------------------------------------
API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"  # 🔐 Change before production

async def verify_api_key(x_api_key: str = Header(None)):
    """Ensures that every request includes the correct API key header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# -------------------------------------------------
# 5️⃣ Include Routers (Financial + AI + Upload)
# -------------------------------------------------
# Financial analysis routes
app.include_router(
    financial_analysis.router,
    prefix="/api/financial",
    tags=["Financial Analysis"],
    dependencies=[Depends(verify_api_key)],
)

# Upload routes
app.include_router(
    upload.router,
    prefix="/api",
    tags=["File Upload"],
    dependencies=[Depends(verify_api_key)],
)

# AI analysis routes
app.include_router(
    analyze.router,
    prefix="/api",
    tags=["AI Analysis"],
    dependencies=[Depends(verify_api_key)],
)

# -------------------------------------------------
# 6️⃣ Alias route (for old frontend endpoint)
# -------------------------------------------------
alias_router = APIRouter()

@alias_router.post("/api/financial-analysis")
async def alias_financial_analysis(payload: dict, x_api_key: str = Header(None)):
    """
    Temporary alias endpoint for backward compatibility with old frontend.
    Redirects to the main /api/financial/analysis route.
    """
    from app.routes.financial_analysis import analyze_financial_data
    return await analyze_financial_data(payload)

app.include_router(alias_router)

# -------------------------------------------------
# 7️⃣ Root & Utility Endpoints
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
    return {"status": "ok", "service": "Bravix.Ai backend healthy"}
