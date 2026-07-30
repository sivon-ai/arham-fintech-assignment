from fastapi import APIRouter, Query
from app.services.loader import load_json
from app.services.simulator import simulate_network
from app.config import TRADE_CHUNK_SIZE

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.get("")
async def get_trades(

    offset: int = Query(0, ge=0),

    limit: int = Query(TRADE_CHUNK_SIZE, ge=1),

    client_id: int | None = None,

    start_date: str | None = None,

    end_date: str | None = None,

    delay_seconds: float | None = Query(None, ge=0),

    failure_rate: float | None = Query(None, ge=0, le=1)

):

    await simulate_network(delay_seconds, failure_rate)

    trades = load_json("trades.json")

    if client_id:

        trades = [

            t

            for t in trades

            if t["client_id"] == client_id

        ]

    if start_date:

        trades = [

            t

            for t in trades

            if t["trade_date"] >= start_date

        ]

    if end_date:

        trades = [

            t

            for t in trades

            if t["trade_date"] <= end_date

        ]

    total = len(trades)

    chunk = trades[offset: offset + limit]

    return {

        "total": total,

        "offset": offset,

        "limit": limit,

        "next_offset": (

            offset + limit

            if offset + limit < total

            else None

        ),

        "has_more": offset + limit < total,

        "data": chunk

    }
