from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Create FastAPI App ---
app = FastAPI(title="Bravix API", version="1.0")

# --- CORS Setup (Allow Everything Temporarily) ---
# This guarantees Vercel can talk to Render.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporary wildcard — full open access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Import Routers AFTER Middleware ---
try:
    from app.routers import financial_analysis
    app.include_router(financial_analysis.router)
except Exception as e:
    print(f"⚠️ Router load failed: {e}")

# --- Root Endpoint for Quick Check ---
@app.get("/")
def root():
    return {"message": "Bravix Demo API running (CORS Enabled)"}
