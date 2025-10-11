from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import financial_analysis

app = FastAPI(title="Bravix API", version="1.0")

# Allow both localhost and 127.0.0.1
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Bravix Demo API running"}

# Include your financial analysis routes
app.include_router(financial_analysis.router)
