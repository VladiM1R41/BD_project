import os
import redis
from dotenv import load_dotenv

load_dotenv("env.env")

for key in ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]:
    value = os.getenv(key)
    print(f"{key}: {value}")


DB_CONFIG = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD", None),
    "decode_responses": True
}

POOL_MIN_CONN = int(os.getenv("POOL_MIN_CONN", 1))
POOL_MAX_CONN = int(os.getenv("POOL_MAX_CONN", 10))

REDIS_KEY_PREFIX = "aviapp:"
TOKEN_TTL = int(os.getenv("REDIS_TOKEN_TTL", 3600))
SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", 1800))

CITIES_TTL = int(os.getenv("REDIS_TOKEN_TTL", 86400 * 7))
AIRPORTS_TTL = int(os.getenv("REDIS_TOKEN_TTL", 86400 * 7))
def get_redis():
    return redis.Redis(**REDIS_CONFIG)