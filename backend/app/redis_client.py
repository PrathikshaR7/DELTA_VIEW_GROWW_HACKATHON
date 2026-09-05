import json

import redis

from app.config import settings

_client = redis.from_url(settings.redis_url, decode_responses=True)

QUOTE_KEY_PREFIX = "quote:"
UPDATES_CHANNEL = "quote_updates"


def get_redis() -> redis.Redis:
    return _client


def set_latest_quote(symbol: str, payload: dict) -> None:
    _client.set(f"{QUOTE_KEY_PREFIX}{symbol}", json.dumps(payload, default=str))


def get_latest_quote(symbol: str) -> dict | None:
    raw = _client.get(f"{QUOTE_KEY_PREFIX}{symbol}")
    return json.loads(raw) if raw else None


def get_latest_quotes(symbols: list[str]) -> dict[str, dict]:
    if not symbols:
        return {}
    pipe = _client.pipeline()
    for s in symbols:
        pipe.get(f"{QUOTE_KEY_PREFIX}{s}")
    results = pipe.execute()
    out = {}
    for symbol, raw in zip(symbols, results):
        if raw:
            out[symbol] = json.loads(raw)
    return out


def publish_update(symbol: str, payload: dict) -> None:
    _client.publish(UPDATES_CHANNEL, json.dumps({"symbol": symbol, **payload}, default=str))
