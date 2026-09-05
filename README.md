# Smart Market Watchlist

Built for the Groww "What to build?" hackathon brief. This is not the obvious
watchlist - it's an **attention allocator**: given a list of stocks, it tells
you which ones actually deserve a look right now, and explains why in plain
language.

## The core idea: Meaningful Change Score (MCS)

A raw "% change" number treats a 2% move in a sleepy PSU bank the same as a
2% move in a small-cap that swings that much every day. MCS instead asks:
*relative to how this stock normally behaves, is today's move actually
unusual - and is anything corroborating it?*

Four signals, each explainable on their own, combined into one 0-100 score
(see `backend/app/scoring.py`):

| Signal | What it measures |
|---|---|
| Volatility z-score | Is `\|% change\|` large vs. this stock's own trailing 20-day volatility? |
| Volume ratio | Is volume unusually high vs. its trailing average (conviction, not just noise)? |
| 52-week proximity | Is the move pushing the stock toward/through a real breakout level, in the direction it's already moving? |
| Index divergence | Is the stock doing something different from Nifty 50 (idiosyncratic vs. "the whole market moved")? |

The weights are simple, documented constants - not a hidden model - so the
score stays explainable. Clicking any stock shows the score, a plain-English
reason (e.g. *"Up 6.2% - a 5.6x larger move than its usual daily swing; on
5.0x average volume; near its 52-week high"*), a breakdown bar per signal,
and a price chart.

## "What changed since you last checked"

Every watchlist row stores a per-user `last_seen_ltp` / `last_seen_score`,
updated a few seconds after each dashboard load (`/watchlist/mark-seen`).
The next time you open the app, `/market/quotes` diffs the current price
against *your* last visit - not against market open - so two users checking
the same stock at different times each see their own "what's new" delta.

## Handling the weekend / stale-data problem honestly

Real intraday tick data disappears outside NSE market hours (9:15-15:30 IST,
Mon-Fri). Rather than faking numbers, the ingestion worker:

- During market hours: fetches real live quotes (Twelve Data if
  `TWELVEDATA_API_KEY` is set, otherwise yfinance - no key required).
- Outside market hours: **replays a real historical session** for each
  symbol. It picks one of that stock's actual past trading days and walks
  LTP smoothly through its *real* open -> high -> low -> close path and
  real volume ramp. No number is invented - everything comes from a real
  historical bar.
- The UI always shows which mode is active (`live` vs `replay`, plus the
  real date being replayed) so nothing is presented as live when it isn't.
  This is deliberate: Groww's "Responsible" and "Transparent" values mean
  the system should never quietly misrepresent data freshness.

## Architecture

```
Market data API (yfinance / Twelve Data)
        v
Ingestion worker  --writes-->  Redis (latest quote cache + pub/sub)
        |                              |
        writes                          v
        v                       API server (FastAPI, REST + WebSocket)
   Postgres (users, watchlists,          |
   per-user last-seen, snapshot history) v
                                 React frontend (dark teal UI)
```

- **Redis** is the hot path: the API server never talks to the market data
  provider directly, it just reads the latest cached quote. Adding more
  users doesn't add more provider calls - only adding more *distinct
  symbols* does.
- **Postgres** holds durable state: accounts, per-user watchlists, and a
  timestamped snapshot history per symbol (used for the chart and for
  auditing what the score was at any past moment).
- **WebSocket** clients subscribe once; the worker's Redis publish fans out
  to every connected browser without each client polling the API.
- This scales by sharding ingestion across symbol ranges and adding stateless
  API server replicas behind Redis pub/sub - user growth and symbol growth
  scale independently.

## Running it step by step

**Prerequisites:** Docker Desktop (includes Docker Compose) installed and running.

1. **Get the code.**
   ```bash
   git clone https://github.com/<your-username>/groww-watchlist.git
   cd groww-watchlist
   ```

2. **Create your backend env file.** Compose reads `backend/.env`, which is
   not committed to git (see `.gitignore`) - you create it once locally:
   ```bash
   cp backend/.env.example backend/.env
   ```
   The defaults in that file work with zero API keys (falls back to
   yfinance / the replay engine). Leave it as-is unless you're adding a
   real provider key (see below).

3. **Build and start everything.** From the repo root:
   ```bash
   docker compose up --build
   ```
   This starts five containers: `postgres`, `redis`, `backend` (FastAPI),
   `worker` (ingestion loop), and `frontend` (nginx serving the built React app).
   First run takes a few minutes to build images; subsequent runs are fast.

4. **Open the app.**
   - Frontend: http://localhost:5173
   - API docs (Swagger): http://localhost:8000/docs

5. **Register an account** on the frontend, log in, then click **+ Add
   symbol** and add a few NSE symbols (`RELIANCE`, `HDFCBANK`, `TATASTEEL`,
   `INFY`, ...).

6. **Wait for data to populate.** A newly added symbol is fetched
   immediately when you add it; the worker then keeps refreshing every
   `INGEST_INTERVAL_SECONDS` (default 15s). Prices and scores appear
   within a few seconds.

7. **Shut it down** when you're done:
   ```bash
   docker compose down          # stop containers, keep DB data
   docker compose down -v       # also wipe the Postgres volume
   ```

### Using a real API key (optional)

By default the system runs with **zero API keys** using yfinance. To use a
real provider key instead:

1. Get a free key at https://twelvedata.com/
2. Open `backend/.env` (the one you created in step 2 above) and set
   `TWELVEDATA_API_KEY=<your key>`
3. `docker compose up --build` (rebuild isn't strictly required for an env
   change, but `docker compose restart backend worker` is enough if you'd
   rather not rebuild)

### Forcing replay mode for a demo

Set `DATA_PROVIDER=replay` in `backend/.env` to always use the real-history
replay engine, regardless of actual market hours - useful for rehearsing a
demo on a weekend without waiting for Monday.

### Troubleshooting

- **A newly added symbol shows dashes for a bit** - normal for the first
  few seconds; the row is a placeholder until the first fetch completes.
  If it never fills in, check `docker compose logs worker` for fetch errors.
- **Chart says "only a few data points so far"** - the price chart is
  built from snapshots taken every ingestion cycle, so a symbol added a
  minute ago will only have a handful of points; it fills in as the app
  keeps running.
- **Port already in use** - something else on your machine is using 5173,
  8000, 5432, or 6379; stop that process or change the port mapping in
  `docker-compose.yml`.

## What was deliberately left out

Order placement, push/SMS alerts, portfolio P&L, and social features were
all left out on purpose. None of them were asked for in the brief, and each
would dilute the one thing this project is trying to do well: help you
notice what actually matters, quickly, and trust why.

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, JWT auth
- **Worker**: standalone Python process, shares the backend's codebase
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts
- **Infra**: Docker Compose (5 services: postgres, redis, backend, worker, frontend)
