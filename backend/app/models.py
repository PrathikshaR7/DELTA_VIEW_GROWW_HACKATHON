import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    watchlist_items = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    """One symbol a user is tracking. Also stores per-user 'last seen'
    state for that symbol so we can compute 'what changed since you last
    checked' independently for every user, even for the same stock."""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    added_at = Column(DateTime, default=dt.datetime.utcnow)

    # snapshot of price/score the last time this user actually opened the app
    last_seen_at = Column(DateTime, nullable=True)
    last_seen_ltp = Column(Float, nullable=True)
    last_seen_score = Column(Float, nullable=True)

    user = relationship("User", back_populates="watchlist_items")


class PriceSnapshot(Base):
    """Periodic durable snapshot of a symbol's computed state, written by
    the ingestion worker. Used for history/sparklines and for auditing
    what the score was at any point in time."""

    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    ts = Column(DateTime, index=True, default=dt.datetime.utcnow)

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    prev_close = Column(Float)
    ltp = Column(Float)
    change = Column(Float)
    pct_change = Column(Float)
    volume = Column(Float)
    value_crores = Column(Float)
    week52_high = Column(Float)
    week52_low = Column(Float)

    mcs_score = Column(Float)
    mcs_reason = Column(String)
    mcs_z_score = Column(Float)
    mcs_volume_ratio = Column(Float)
    mcs_vs_index = Column(Float)
    mcs_near_52w = Column(Float)

    data_mode = Column(String, default="live")  # live | delayed | replay
    source_session_date = Column(String, nullable=True)  # for replay mode
