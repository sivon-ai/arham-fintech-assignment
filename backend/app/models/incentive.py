from sqlalchemy import Column, Float, Integer

from app.db.base import Base


class Incentive(Base):

    __tablename__ = "incentives"

    employee_id = Column(Integer, primary_key=True)

    brokerage = Column(Float, default=0)

    incentive = Column(Float, default=0)
