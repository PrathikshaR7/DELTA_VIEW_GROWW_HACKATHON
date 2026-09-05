import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.redis_client import get_latest_quotes
from app.symbols import NSE_SYMBOL_UNIVERSE

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/search")
def search_symbols(q: str = Query(default="", min_length=0)):
    q = q.upper().strip()
    if not q:
        return NSE_SYMBOL_UNIVERSE[:20]
    return [s for s in NSE_SYMBOL_UNIVERSE if q in s["symbol"] or q in s["name"].upper()][:20]


@router.get("/quotes", response_model=list[schemas.QuoteOut])
def get_quotes(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    items = (
        db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == user.id).all()
    )
    symbols = [i.symbol for i in items]
    quotes = get_latest_quotes(symbols)

    out = []
    for item in items:
        q = quotes.get(item.symbol)

        if not q:
            # No cached quote yet (e.g. just added and the first fetch is
            # still in flight). Return a placeholder row instead of
            # dropping the symbol entirely, so it still shows up in the
            # table and gets picked up by the next websocket update.
            out.append(schemas.QuoteOut(
                symbol=item.symbol,
                ts=item.added_at,
                is_new_since_last_visit=True,
            ))
            continue

        quote = schemas.QuoteOut(**q)

        if item.last_seen_ltp is not None and q.get("ltp") is not None:
            diff = q["ltp"] - item.last_seen_ltp
            quote.since_last_seen_change = round(diff, 2)
            quote.since_last_seen_pct = (
                round(diff / item.last_seen_ltp * 100, 2) if item.last_seen_ltp else None
            )
        else:
            quote.is_new_since_last_visit = True
        out.append(quote)
    return out


@router.get("/history/{symbol}", response_model=list[schemas.HistoryPoint])
def get_history(
    symbol: str,
    hours: int = 6,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    since = dt.datetime.utcnow() - dt.timedelta(hours=hours)
    rows = (
        db.query(models.PriceSnapshot)
        .filter(models.PriceSnapshot.symbol == symbol.upper(), models.PriceSnapshot.ts >= since)
        .order_by(models.PriceSnapshot.ts.asc())
        .all()
    )
    return [
        schemas.HistoryPoint(ts=r.ts, ltp=r.ltp, mcs_score=r.mcs_score)
        for r in rows
        if r.ltp is not None
    ]
