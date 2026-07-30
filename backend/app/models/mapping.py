from sqlalchemy import Column, Integer, UniqueConstraint

from app.db.base import Base


class Mapping(Base):

    __tablename__ = "mappings"
    __table_args__ = (
        UniqueConstraint("client_id", name="uq_mappings_client_id"),
    )

    id = Column(Integer, primary_key=True)

    client_id = Column(Integer, index=True)

    employee_id = Column(Integer, index=True)
