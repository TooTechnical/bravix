from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --------------------------------------------------------
# 1️⃣ Create FastAPI instance
# --------------------------------------------------------
app = FastAPI(
    title="Bravix API",
    version="1.0",
    description="Backend for the Bravix Financial Analysis Demo",
)

# --------------------------------------------------------
# 2️⃣ Configure CORS
# --------------------------------------------------------
# During testing, we use "*" to allow all origins (so Vercel can reach it).
# Once confirmed working, replace "*" with your actual domains.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- temporarily allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------
# 3️⃣ Import routes (AFTER CORS middleware)
# --------------------------------------------------------
from app.routers import financial_analysis


# --------------------------------------------------------
# 4️⃣ Root endpoint for quick API check
# --------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Bravix Demo API running"}


# --------------------------------------------------------
# 5️⃣ Include all routers
# --------------------------------------------------------
app.include_router(financial_analysis.router)
