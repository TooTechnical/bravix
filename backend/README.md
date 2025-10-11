Bravix demo backend (FastAPI)

Install:
$ python -m venv .venv
$ source .venv/bin/activate    # mac/linux
$ .venv\Scripts\activate       # windows
$ pip install -r requirements.txt

Run locally:
$ uvicorn app.main:app --reload --port 8000

Endpoints:
GET  /                 -> health
POST /api/score        -> JSON body { "revenue": 120000, "profit": 15000, "debt": 40000 }
POST /api/score-from-csv -> form-file upload (CSV), see sample_data/example_company.csv
