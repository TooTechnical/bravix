from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, analyze, financial_analysis, test_connection

app = FastAPI(title="Bravix API", version="1.0")

# ✅ CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bravix-ai.vercel.app",  # your frontend
        "https://bravix.vercel.app",     # alternate frontend name
        "http://localhost:5173"          # local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Route includes
app.include_router(upload.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(financial_analysis.router, prefix="/api")
app.include_router(test_connection.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Welcome to Bravix FastAPI backend (Vercel deployment)."}
