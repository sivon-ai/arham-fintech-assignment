from fastapi import APIRouter
from app.services.loader import load_json

router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


@router.get("")
def get_employees():

    employees = load_json("employees.json")

    return {

        "total": len(employees),

        "data": employees

    }