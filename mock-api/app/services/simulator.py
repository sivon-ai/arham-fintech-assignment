import asyncio
import random

from fastapi import HTTPException

from app.config import (
    DELAY_SECONDS,
    FAILURE_RATE
)


async def simulate_network(delay_seconds=None, failure_rate=None):
    delay = DELAY_SECONDS if delay_seconds is None else delay_seconds
    failure = FAILURE_RATE if failure_rate is None else failure_rate

    await asyncio.sleep(delay)

    if random.random() < failure:

        raise HTTPException(

            status_code=500,

            detail="Simulated BSE mid-pull network failure"

        )
