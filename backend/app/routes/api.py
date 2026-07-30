from threading import Thread

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.client import Client
from app.models.employee import Employee
from app.models.incentive import Incentive
from app.models.mapping import Mapping
from app.models.trade import Trade
from app.scheduler.jobs import sync_job
from app.scheduler.state import state

router = APIRouter(prefix="/api", tags=["Portal API"])


def client_dict(client):
    return {
        "client_id": client.client_id,
        "name": client.name,
        "pan": client.pan,
        "phone": client.phone,
        "email": client.email,
        "city": client.city,
    }


def employee_dict(employee):
    return {
        "employee_id": employee.employee_id,
        "name": employee.name,
        "email": employee.email,
        "department": employee.department,
    }


def trade_dict(trade, client_names=None):
    row = {
        "trade_id": trade.trade_id,
        "client_id": trade.client_id,
        "stock": trade.stock,
        "quantity": trade.quantity,
        "brokerage": trade.brokerage,
        "trade_date": trade.trade_date,
    }
    if client_names is not None:
        row["client_name"] = client_names.get(trade.client_id)
    return row


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/sync/status")
def sync_status(db: Session = Depends(get_db)):
    snapshot = state.snapshot()
    snapshot["cache_counts"] = {
        "clients": db.query(Client).count(),
        "trades": db.query(Trade).count(),
        "employees": db.query(Employee).count(),
        "mappings": db.query(Mapping).count(),
    }
    return snapshot


@router.post("/sync/run", status_code=202)
def trigger_sync():
    snapshot = state.snapshot()
    if not snapshot["sync_running"]:
        Thread(target=sync_job, daemon=True).start()

    return {
        "accepted": not snapshot["sync_running"],
        "sync_running": True,
    }


@router.get("/clients")
def clients(
    search: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Client)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Client.name.ilike(pattern),
                Client.pan.ilike(pattern),
                Client.email.ilike(pattern),
                Client.city.ilike(pattern),
            )
        )

    total = query.count()
    rows = (
        query.order_by(Client.client_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": [client_dict(row) for row in rows],
    }


@router.get("/trades")
def trades(
    client_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    stock: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(Trade)
    filters = []

    if client_id:
        filters.append(Trade.client_id == client_id)
    if start_date:
        filters.append(Trade.trade_date >= start_date)
    if end_date:
        filters.append(Trade.trade_date <= end_date)
    if stock:
        filters.append(Trade.stock.ilike(f"%{stock}%"))

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    rows = (
        query.order_by(Trade.trade_date.desc(), Trade.trade_id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    client_ids = {row.client_id for row in rows}
    client_names = {
        row.client_id: row.name
        for row in db.query(Client)
        .filter(Client.client_id.in_(client_ids))
        .all()
    }

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": [trade_dict(row, client_names) for row in rows],
    }


@router.get("/employees")
def employees(db: Session = Depends(get_db)):
    rows = db.query(Employee).order_by(Employee.employee_id).all()
    client_counts = dict(
        db.query(Mapping.employee_id, func.count(Mapping.client_id))
        .group_by(Mapping.employee_id)
        .all()
    )
    incentives = {
        row.employee_id: row
        for row in db.query(Incentive).all()
    }

    data = []
    for employee in rows:
        incentive = incentives.get(employee.employee_id)
        data.append(
            {
                **employee_dict(employee),
                "client_count": client_counts.get(employee.employee_id, 0),
                "brokerage": incentive.brokerage if incentive else 0,
                "incentive": incentive.incentive if incentive else 0,
            }
        )

    return {"total": len(data), "data": data}


@router.get("/my-clients")
def my_clients(
    employee_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Client)
        .join(Mapping, Mapping.client_id == Client.client_id)
        .filter(Mapping.employee_id == employee_id)
        .order_by(Client.name)
        .all()
    )
    client_ids = [row.client_id for row in rows]
    trade_stats = dict(
        db.query(
            Trade.client_id,
            func.count(Trade.trade_id),
        )
        .filter(Trade.client_id.in_(client_ids))
        .group_by(Trade.client_id)
        .all()
    )
    brokerage_stats = dict(
        db.query(
            Trade.client_id,
            func.coalesce(func.sum(Trade.brokerage), 0),
        )
        .filter(Trade.client_id.in_(client_ids))
        .group_by(Trade.client_id)
        .all()
    )

    data = []
    for row in rows:
        data.append(
            {
                **client_dict(row),
                "trade_count": trade_stats.get(row.client_id, 0),
                "brokerage": round(
                    float(brokerage_stats.get(row.client_id, 0) or 0),
                    2,
                ),
            }
        )

    return {"total": len(data), "data": data}


@router.get("/incentives")
def incentives(
    role: str = Query("employee", pattern="^(employee|management)$"),
    employee_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Employee, Incentive)
        .outerjoin(Incentive, Incentive.employee_id == Employee.employee_id)
        .order_by(Employee.employee_id)
    )

    if role != "management":
        if employee_id is None:
            return {"total": 0, "data": []}
        query = query.filter(Employee.employee_id == employee_id)

    client_counts = dict(
        db.query(Mapping.employee_id, func.count(Mapping.client_id))
        .group_by(Mapping.employee_id)
        .all()
    )

    data = []
    for employee, incentive in query.all():
        data.append(
            {
                **employee_dict(employee),
                "client_count": client_counts.get(employee.employee_id, 0),
                "brokerage": incentive.brokerage if incentive else 0,
                "incentive": incentive.incentive if incentive else 0,
            }
        )

    return {"total": len(data), "data": data}
