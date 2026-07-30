from fastapi import APIRouter, Query
from app.services.loader import load_json
from app.services.simulator import simulate_network
from app.config import CLIENT_CHUNK_SIZE

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("")
async def get_clients(
    offset: int = Query(0, ge=0),
    limit: int = Query(CLIENT_CHUNK_SIZE, ge=1),
    delay_seconds: float | None = Query(None, ge=0),
    failure_rate: float | None = Query(None, ge=0, le=1),
):
    await simulate_network(delay_seconds, failure_rate)

    clients = load_json("clients.json")

    total = len(clients)

    chunk = clients[offset: offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "next_offset": offset + limit if offset + limit < total else None,
        "has_more": offset + limit < total,
        "data": chunk
    }
