import json
import random

from faker import Faker

from pathlib import Path

from datetime import datetime, timedelta

fake = Faker("en_IN")
Faker.seed(20260714)
random.seed(20260714)

BASE = Path(__file__).resolve().parent.parent

DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

NUM_CLIENTS = 500

NUM_EMPLOYEES = 20

NUM_TRADES = 5000

stocks = [
    "TCS",
    "INFY",
    "RELIANCE",
    "SBIN",
    "HDFCBANK",
    "ICICIBANK",
    "ITC",
    "LT"
]


def save(name, data):

    with open(DATA / name, "w") as f:

        json.dump(data, f, indent=4)


employees = []

for i in range(1, NUM_EMPLOYEES + 1):

    employees.append({

        "employee_id": i,

        "name": fake.name(),

        "email": fake.email(),

        "department": "Relationship Manager"

    })


clients = []

for i in range(1, NUM_CLIENTS + 1):

    clients.append({

        "client_id": i,

        "name": fake.name(),

        "pan": fake.bothify(text="?????#####?"),

        "phone": fake.phone_number(),

        "email": fake.email(),

        "city": fake.city()

    })


mappings = []

for c in clients:

    mappings.append({

        "client_id": c["client_id"],

        "employee_id": random.randint(1, NUM_EMPLOYEES)

    })


trades = []

for i in range(1, NUM_TRADES + 1):

    trades.append({

        "trade_id": i,

        "client_id": random.randint(1, NUM_CLIENTS),

        "stock": random.choice(stocks),

        "quantity": random.randint(1, 200),

        "brokerage": round(random.uniform(25, 500), 2),

        "trade_date": (

            datetime.now()

            - timedelta(days=random.randint(0, 365))

        ).strftime("%Y-%m-%d")

    })


save("clients.json", clients)

save("employees.json", employees)

save("mappings.json", mappings)

save("trades.json", trades)

print("Fake data generated.")
