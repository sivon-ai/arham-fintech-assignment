import os
import logging
import time

from dotenv import load_dotenv
import requests
from sqlalchemy import func

from app.db.database import SessionLocal

from app.models.client import Client
from app.models.employee import Employee
from app.models.incentive import Incentive
from app.models.mapping import Mapping
from app.models.trade import Trade

load_dotenv()

MOCK_API = os.getenv("MOCK_API", "http://127.0.0.1:9000")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("BSE_REQUEST_TIMEOUT_SECONDS", 25))
MAX_RETRIES = int(os.getenv("BSE_MAX_RETRIES", 5))
INCENTIVE_RATE = float(os.getenv("INCENTIVE_RATE", 0.1))

logging.basicConfig(level=logging.INFO)

CLIENT_LIMIT = int(os.getenv("BSE_CLIENT_LIMIT", 100))
TRADE_LIMIT = int(os.getenv("BSE_TRADE_LIMIT", 500))


class SyncService:

    def fetch_with_retry(self, path, params=None):
        delay = 2
        url = f"{MOCK_API.rstrip('/')}{path}"

        for attempt in range(MAX_RETRIES):
            try:
                r = requests.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                r.raise_for_status()
                return r.json()
            except Exception as e:
                logging.warning(
                    "BSE fetch failed on attempt %s/%s for %s: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    url,
                    e,
                )
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(delay)
                delay *= 2

    def fetch_pages(self, path, limit, params=None):
        rows = []
        offset = 0
        params = dict(params or {})

        while True:
            payload = self.fetch_with_retry(
                path,
                {
                    **params,
                    "offset": offset,
                    "limit": limit,
                },
            )
            rows.extend(payload["data"])

            if not payload["has_more"]:
                break

            offset = payload["next_offset"]

        return rows

    def _delete_missing(self, db, model, id_column, ids):
        if ids:
            db.query(model).filter(~id_column.in_(ids)).delete(
                synchronize_session=False
            )
        else:
            db.query(model).delete()

    def _apply_snapshot(self, employees, mappings, clients, trades):
        with SessionLocal() as db:
            with db.begin():
                employee_ids = {row["employee_id"] for row in employees}
                client_ids = {row["client_id"] for row in clients}
                trade_ids = {row["trade_id"] for row in trades}

                for employee in employees:
                    db.merge(Employee(**employee))
                self._delete_missing(
                    db,
                    Employee,
                    Employee.employee_id,
                    employee_ids,
                )

                for client in clients:
                    db.merge(Client(**client))
                self._delete_missing(
                    db,
                    Client,
                    Client.client_id,
                    client_ids,
                )

                for trade in trades:
                    db.merge(Trade(**trade))
                self._delete_missing(
                    db,
                    Trade,
                    Trade.trade_id,
                    trade_ids,
                )

                db.query(Mapping).delete()
                db.add_all(
                    Mapping(
                        client_id=mapping["client_id"],
                        employee_id=mapping["employee_id"],
                    )
                    for mapping in mappings
                )

                self._recompute_incentives(db, employee_ids)

    def _recompute_incentives(self, db, employee_ids):
        db.flush()
        db.query(Incentive).delete()
        db.flush()

        aggregates = (
            db.query(
                Mapping.employee_id,
                func.coalesce(func.sum(Trade.brokerage), 0),
            )
            .join(Trade, Trade.client_id == Mapping.client_id)
            .group_by(Mapping.employee_id)
            .all()
        )
        brokerage_by_employee = {
            employee_id: float(brokerage or 0)
            for employee_id, brokerage in aggregates
        }

        db.add_all(
            Incentive(
                employee_id=employee_id,
                brokerage=round(brokerage_by_employee.get(employee_id, 0), 2),
                incentive=round(
                    brokerage_by_employee.get(employee_id, 0) * INCENTIVE_RATE,
                    2,
                ),
            )
            for employee_id in employee_ids
        )

    def sync_all(self):
        logging.info("Starting full BSE/internal snapshot sync")

        employees = self.fetch_with_retry("/employees")["data"]
        mappings = self.fetch_with_retry("/mappings")["data"]
        clients = self.fetch_pages("/clients", CLIENT_LIMIT)
        trades = self.fetch_pages("/trades", TRADE_LIMIT)

        self._apply_snapshot(employees, mappings, clients, trades)

        counts = {
            "employees": len(employees),
            "mappings": len(mappings),
            "clients": len(clients),
            "trades": len(trades),
        }
        logging.info("Sync completed: %s", counts)
        return counts
