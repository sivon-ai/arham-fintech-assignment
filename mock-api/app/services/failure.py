import random
import asyncio
from fastapi import HTTPException
from app.config import DELAY_SECONDS, FAILURE_RATE

async def simulate_failure():

    await asyncio.sleep(DELAY_SECONDS)

    if random.random() < FAILURE_RATE:
        raise HTTPException(
            status_code=500,
            detail="Simulated BSE failure"
        )