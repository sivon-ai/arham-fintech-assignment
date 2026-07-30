from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import Base
from app.db.database import engine
from app.models.client import Client
from app.models.employee import Employee
from app.models.incentive import Incentive
from app.models.mapping import Mapping
from app.models.trade import Trade
from app.routes.api import router as api_router
from app.routes.live import router as live_router
from app.scheduler.scheduler import start_scheduler, stop_scheduler
from app.services.live import live_hub


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    live_hub.set_loop(asyncio.get_running_loop())

    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(

    title="Arham Backend",

    lifespan=lifespan

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(live_router)


@app.get("/")
def home():

    return {

        "status": "Backend Running"

    }
