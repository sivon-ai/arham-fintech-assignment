from sqlalchemy import Column, Integer, String

from app.db.base import Base


class Employee(Base):

    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True)

    name = Column(String, index=True)

    email = Column(String)

    department = Column(String)
