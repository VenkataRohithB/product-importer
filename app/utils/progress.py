import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL, decode_responses=True)

PREFIX = "progress:"

def set_progress(task_id: str, pct: int, msg: str):
    r.set(f"{PREFIX}{task_id}", f"{pct}|{msg}")

def get_progress(task_id: str):
    value = r.get(f"{PREFIX}{task_id}")
    if not value:
        return (0, "not found")
    pct, msg = value.split("|", 1)
    return int(pct), msg
