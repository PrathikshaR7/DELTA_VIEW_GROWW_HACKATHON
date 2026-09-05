import logging
import time

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.data_source import is_market_open
from app.database import Base, SessionLocal, engine
from app.quote_ingest import get_index_pct_change, process_symbol

log = logging.getLogger(__name__)


def get_tracked_symbols(db: Session) -> list[str]:
    rows = db.query(models.WatchlistItem.symbol).distinct().all()
    symbols = sorted({r[0] for r in rows})
    return symbols or ["RELIANCE", "HDFCBANK", "ICICIBANK", "TATASTEEL", "INFY"]


def run_forever():
    Base.metadata.create_all(bind=engine)
    log.info("ingestion worker started (market_open=%s, provider=%s)",
              is_market_open(), settings.data_provider)
    while True:
        db = SessionLocal()
        try:
            symbols = get_tracked_symbols(db)
            index_pct_change = get_index_pct_change()
            for symbol in symbols:
                process_symbol(db, symbol, index_pct_change)
        except Exception as e:
            log.exception("ingestion cycle failed: %s", e)
        finally:
            db.close()
        time.sleep(settings.ingest_interval_seconds)


if __name__ == "__main__":
    run_forever()
