from fastapi import FastAPI

from app.routes.clients import router as clients_router
from app.routes.trades import router as trades_router
from app.routes.employees import router as employees_router
from app.routes.mappings import router as mappings_router
from app.config import DELAY_SECONDS, FAILURE_RATE

app = FastAPI(
    title="Mock BSE API",
    version="1.0"
)

app.include_router(clients_router)
app.include_router(trades_router)
app.include_router(employees_router)
app.include_router(mappings_router)


@app.get("/")
def home():

    return {

        "message": "Mock BSE API Running"

    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "delay_seconds": DELAY_SECONDS,
        "failure_rate": FAILURE_RATE,
    }
