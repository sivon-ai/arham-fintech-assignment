# Arham Fintech Internal Operations Portal

This repository contains both parts of the assessment:

- `mock-api`: a FastAPI BSE simulator with delayed, chunked clients/trades endpoints and instant internal employee/mapping endpoints.
- `backend`: a FastAPI internal backend that syncs BSE data in the background, stores a local read cache, computes incentives, and publishes live update events.
- `frontend`: a Vite/React portal for clients, trades, my clients, employees, and incentives.

## Local Links

- Mock BSE API: `http://127.0.0.1:9000`
- Internal backend API: `http://127.0.0.1:8000`
- Internal dashboard: `http://127.0.0.1:5173`

## 1. Mock BSE API

```powershell
cd mock-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.services.generator
uvicorn app.main:app --reload --port 9000
```

Optional environment settings:

```powershell
$env:DELAY_SECONDS="3"
$env:FAILURE_RATE="0.2"
$env:CLIENT_CHUNK_SIZE="100"
$env:TRADE_CHUNK_SIZE="500"
```

Useful endpoints:

- `GET /clients?offset=0&limit=100`
- `GET /trades?client_id=1&start_date=2026-01-01&end_date=2026-07-30`
- `GET /employees`
- `GET /mappings`
- `GET /health`

`/clients` and `/trades` also accept `delay_seconds` and `failure_rate` query parameters for demos.

## 2. Internal Backend

Start the mock API first, then:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Defaults work without a `.env` file:

```powershell
$env:DATABASE_URL="sqlite:///./arham_cache.db"
$env:MOCK_API="http://127.0.0.1:9000"
$env:BSE_REQUEST_TIMEOUT_SECONDS="25"
$env:BSE_MAX_RETRIES="5"
$env:INCENTIVE_RATE="0.1"
```

The backend starts even if BSE is slow or down. Screens read from the local cache and return immediately. A background sync runs at startup and every minute; a manual sync is available at:

```text
POST http://127.0.0.1:8000/api/sync/run
```

## 3. Frontend Dashboard

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Optional:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
```

Open `http://127.0.0.1:5173`.

## Verification

```powershell
cd frontend
npm run build
```

```powershell
cd backend
venv\Scripts\python.exe -m py_compile app\main.py app\services\sync.py app\routes\api.py
```

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md).
