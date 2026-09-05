import datetime as dt
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- watchlist ----------

class WatchlistAdd(BaseModel):
    symbol: str


class WatchlistItemOut(BaseModel):
    id: int
    symbol: str
    added_at: dt.datetime
    last_seen_at: Optional[dt.datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- market / quote ----------

class QuoteOut(BaseModel):
    symbol: str
    ts: dt.datetime

    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    ltp: Optional[float] = None
    change: Optional[float] = None
    pct_change: Optional[float] = None
    volume: Optional[float] = None
    value_crores: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None

    mcs_score: Optional[float] = None
    mcs_reason: Optional[str] = None
    mcs_z_score: Optional[float] = None
    mcs_volume_ratio: Optional[float] = None
    mcs_vs_index: Optional[float] = None
    mcs_near_52w: Optional[float] = None

    data_mode: str = "live"
    source_session_date: Optional[str] = None

    # populated per-user, not stored on the snapshot itself
    since_last_seen_change: Optional[float] = None
    since_last_seen_pct: Optional[float] = None
    is_new_since_last_visit: bool = False


class HistoryPoint(BaseModel):
    ts: dt.datetime
    ltp: float
    mcs_score: Optional[float] = None
