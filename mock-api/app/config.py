import os
from dotenv import load_dotenv

load_dotenv()

DELAY_SECONDS = float(os.getenv("DELAY_SECONDS", 3))

FAILURE_RATE = float(os.getenv("FAILURE_RATE", 0.2))

CLIENT_CHUNK_SIZE = int(
    os.getenv("CLIENT_CHUNK_SIZE", 100)
)

TRADE_CHUNK_SIZE = int(
    os.getenv("TRADE_CHUNK_SIZE", 500)
)
