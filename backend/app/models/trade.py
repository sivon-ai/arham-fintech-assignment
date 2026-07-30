from sqlalchemy import Column, Integer, String, Float

from app.db.base import Base


class Trade(Base):

    __tablename__ = "trades"

    trade_id = Column(Integer, primary_key=True)

    client_id = Column(Integer, index=True)

    stock = Column(String, index=True)

    quantity = Column(Integer)

    brokerage = Column(Float)

    trade_date = Column(String, index=True)
