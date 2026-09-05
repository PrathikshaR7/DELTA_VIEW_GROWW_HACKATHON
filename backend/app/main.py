from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, watchlist, market
from app.ws_manager import manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Market Watchlist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(watchlist.router)
app.include_router(market.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/quotes")
async def ws_quotes(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # keep the connection alive; clients don't need to send anything
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
