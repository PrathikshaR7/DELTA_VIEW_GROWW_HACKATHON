import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.quote_ingest import get_index_pct_change, process_symbol

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[schemas.WatchlistItemOut])
def list_watchlist(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    return (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == user.id)
        .order_by(models.WatchlistItem.added_at.asc())
        .all()
    )


@router.post("", response_model=schemas.WatchlistItemOut, status_code=201)
def add_symbol(
    payload: schemas.WatchlistAdd,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    symbol = payload.symbol.upper().strip()
    existing = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.user_id == user.id, models.WatchlistItem.symbol == symbol)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")

    item = models.WatchlistItem(user_id=user.id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)

    # Prime the quote cache right away instead of waiting for the next
    # background ingestion cycle (up to `ingest_interval_seconds` later).
    # Best-effort: if the fetch fails here, the worker will pick this
    # symbol up on its next regular cycle regardless.
    try:
        process_symbol(db, symbol, get_index_pct_change())
    except Exception:
        pass

    return item


@router.delete("/{item_id}", status_code=204)
def remove_symbol(
    item_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    item = (
        db.query(models.WatchlistItem)
        .filter(models.WatchlistItem.id == item_id, models.WatchlistItem.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return None


@router.post("/mark-seen", status_code=200)
def mark_seen(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """Called when the user opens/refreshes the dashboard. Snapshots the
    current ltp/score for every tracked symbol as 'last seen' so that on
    the NEXT visit we can show exactly what changed in between - this is
    the 'return later and see what has changed' requirement, scoped per
    user rather than per market session."""
    from app.redis_client import get_latest_quotes

    items = (
        db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == user.id).all()
    )
    symbols = [i.symbol for i in items]
    quotes = get_latest_quotes(symbols)

    for item in items:
        q = quotes.get(item.symbol)
        if q:
            item.last_seen_at = dt.datetime.utcnow()
            item.last_seen_ltp = q.get("ltp")
            item.last_seen_score = q.get("mcs_score")
    db.commit()
    return {"updated": len(items)}
