from fastapi import APIRouter
from app.services.loader import load_json

router = APIRouter(
    prefix="/mappings",
    tags=["Mappings"]
)


@router.get("")
def get_mappings():

    mappings = load_json("mappings.json")

    return {

        "total": len(mappings),

        "data": mappings

    }