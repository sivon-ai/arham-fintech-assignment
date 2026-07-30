from app.db.database import engine

from app.db.base import Base

from app.models.client import Client
from app.models.trade import Trade
from app.models.employee import Employee
from app.models.mapping import Mapping
from app.models.incentive import Incentive

Base.metadata.create_all(engine)

print("Tables Created")