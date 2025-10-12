from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import financial_analysis

# -------------------------------------------------
# 1️⃣ Create FastAPI instance
# -------------------------------------------------
app = FastAPI(
    title="Bravix API",
    version="1.1",
    description="Secure backend for Bravix Financial Analysis Demo"
)

# -------------------------------------------------
# 2️⃣ CORS configuration (Restricted + Local Dev)
# -------------------------------------------------
ALLOWED_ORIGINS = [
    "https://bravix.vercel.app",
    "https://bravix-1rr5nkf0f-tootechnicals-projects.vercel.app",
    "https://bravix-nxch5n4g6-tootechnicals-projects.vercel.app",
    "http://localhost:5173"
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
API_KEY = "BRAVIX-DEMO-SECURE-KEY-2025"  # change this value later

async def verify_api_key(x_api_key: str = Header(None)):
    """Ensures that every request includes the correct API key header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

# -------------------------------------------------
# 4️⃣ Include routers (protected)
# -------------------------------------------------
# Apply API key check globally to financial_analysis routes
app.include_router(
    financial_analysis.router,
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
