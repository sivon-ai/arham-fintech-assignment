from sqlalchemy import Column, Integer, String

from app.db.base import Base


class Client(Base):

    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True)

    name = Column(String, index=True)

    pan = Column(String, index=True)

    phone = Column(String)

    email = Column(String)

    city = Column(String, index=True)
