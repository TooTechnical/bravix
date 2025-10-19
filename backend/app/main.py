from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes import financial_analysis
from app.routes import upload, analyze  # 🆕 New imports
from dotenv import load_dotenv

load_dotenv()


# -------------------------------------------------
# 1️⃣ Create FastAPI instance
# -------------------------------------------------
app = FastAPI(
    title="Bravix API",
    version="1.2",
    description="Secure backend for Bravix Financial Analysis & AI Demo"
)

# -------------------------------------------------
# 2️⃣ CORS configuration (Restricted + Local Dev)
# -------------------------------------------------
ALLOWED_ORIGINS = [
    "https://bravix.vercel.app",
    "https://bravix-pi.vercel.app",
    "https://bravix-1rr5nkf0f-tootechnicals-projects.vercel.app",
    "https://bravix-nxch5n4g6-tootechnicals-projects.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 3️⃣ Simple API Key Security Layer
# -------------------------------------------------
API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"  # 🔐 Change this before production

async def verify_api_key(x_api_key: str = Header(None)):
    """Ensures that every request includes the correct API key header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# -------------------------------------------------
# 4️⃣ Include routers (financial + AI + upload)
# -------------------------------------------------
# Apply API key check globally to the protected endpoints
app.include_router(
    financial_analysis.router,
    prefix="/api/financial",
    tags=["Financial Analysis"],
    dependencies=[Depends(verify_api_key)],
)

# 🧠 AI & File Upload Routes (secured the same way)
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
# 5️⃣ Root endpoint
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "Bravix Demo API running (CORS + API Key Secured)"}

# -------------------------------------------------
# 6️⃣ Debug endpoint (optional)
# -------------------------------------------------
@app.get("/debug-cors")
async def debug_cors(request: Request):
    origin = request.headers.get("origin")
    return {
        "your_origin_header": origin,
        "allowed_origins": ALLOWED_ORIGINS,
        "message": "CORS and API key system active"
    }

# -------------------------------------------------
# 7️⃣ Health check endpoint (for Render / monitoring)
# -------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Bravix.Ai backend healthy"}
