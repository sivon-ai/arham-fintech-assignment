import json
from pathlib import Path

CHECKPOINT_FILE = Path("app/data/checkpoint.json")


def _load():

    if not CHECKPOINT_FILE.exists():

        return {}

    with open(CHECKPOINT_FILE) as f:

        return json.load(f)


def save_offset(resource, offset):

    data = _load()

    data[resource] = offset

    with open(CHECKPOINT_FILE, "w") as f:

        json.dump(data, f, indent=4)


def get_offset(resource):

    data = _load()

    return data.get(resource, 0)


def reset(resource):

    data = _load()

    data[resource] = 0

    with open(CHECKPOINT_FILE, "w") as f:

        json.dump(data, f, indent=4)