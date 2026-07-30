import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"


def load_json(filename):

    with open(DATA_DIR / filename, "r") as f:

        return json.load(f)