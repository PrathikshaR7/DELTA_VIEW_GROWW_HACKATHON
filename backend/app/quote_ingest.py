import datetime as dt
import logging

from sqlalchemy.orm import Session

from app import models
from app.data_source import MarketDataProvider
from app.redis_client import publish_update, set_latest_quote
from app.scoring import ScoreInputs, compute_mcs
from app.symbols import INDEX_SYMBOL

log = logging.getLogger(__name__)

# Shared provider instance so the live-quote cache / rate limiter is reused
# by both the worker process and any in-process API call.
provider = MarketDataProvider()


def get_index_pct_change() -> float:
    try:
        q = provider.fetch(INDEX_SYMBOL)
        if q.prev_close:
            return (q.ltp - q.prev_close) / q.prev_close * 100
    except Exception as e:
        log.warning("could not fetch index quote, defaulting divergence baseline to 0: %s", e)
    return 0.0


def process_symbol(db: Session, symbol: str, index_pct_change: float) -> dict | None:
    """Fetch, score, cache and publish a single symbol's quote. Returns the
    payload that was cached, or None if the fetch failed."""
    try:
        raw = provider.fetch(symbol)
    except Exception as e:
        log.warning("skip %s: %s", symbol, e)
        return None

    change = raw.ltp - raw.prev_close
    pct_change = (change / raw.prev_close * 100) if raw.prev_close else 0.0
    value_crores = (raw.ltp * raw.volume) / 1e7

    result = compute_mcs(ScoreInputs(
        pct_change=pct_change,
        trailing_daily_std_pct=raw.trailing_daily_std_pct,
        volume=raw.volume,
        trailing_avg_volume=raw.trailing_avg_volume,
        ltp=raw.ltp,
        week52_high=raw.week52_high,
        week52_low=raw.week52_low,
        index_pct_change=index_pct_change,
    ))

    payload = {
        "symbol": symbol,
        "ts": dt.datetime.utcnow().isoformat(),
        "open": raw.open, "high": raw.high, "low": raw.low,
        "prev_close": raw.prev_close, "ltp": raw.ltp,
        "change": round(change, 2), "pct_change": round(pct_change, 2),
        "volume": raw.volume, "value_crores": round(value_crores, 2),
        "week52_high": raw.week52_high, "week52_low": raw.week52_low,
        "mcs_score": result.score, "mcs_reason": result.reason,
        "mcs_z_score": result.components["volatility_z"],
        "mcs_volume_ratio": result.components["volume_ratio"],
        "mcs_vs_index": result.components["index_divergence"],
        "mcs_near_52w": result.components["proximity_52w"],
        "data_mode": raw.data_mode,
        "source_session_date": raw.source_session_date,
    }

    set_latest_quote(symbol, payload)
    publish_update(symbol, payload)

    snapshot = models.PriceSnapshot(
        symbol=symbol, ts=dt.datetime.utcnow(),
        open=raw.open, high=raw.high, low=raw.low, prev_close=raw.prev_close,
        ltp=raw.ltp, change=change, pct_change=pct_change, volume=raw.volume,
        value_crores=value_crores, week52_high=raw.week52_high, week52_low=raw.week52_low,
        mcs_score=result.score, mcs_reason=result.reason,
        mcs_z_score=result.components["volatility_z"],
        mcs_volume_ratio=result.components["volume_ratio"],
        mcs_vs_index=result.components["index_divergence"],
        mcs_near_52w=result.components["proximity_52w"],
        data_mode=raw.data_mode, source_session_date=raw.source_session_date,
    )
    db.add(snapshot)
    db.commit()

    log.info("%s ltp=%.2f pct=%.2f score=%.1f mode=%s", symbol, raw.ltp, pct_change,
              result.score, raw.data_mode)

    return payload
