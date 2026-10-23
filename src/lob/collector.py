"""Fault-tolerant collector for Binance partial-book depth streams.

Design choices:
- The depth20@100ms partial-book stream sends complete top-20 snapshots, so
  no diff/sequence reconciliation is needed -- every message stands alone,
  which makes gaps harmless: a dropped connection loses time, never
  consistency (the same defer-don't-fabricate stance as any honest pipeline).
- Reconnect with capped exponential backoff; invalid snapshots are counted
  and dropped, never written.
"""

import asyncio
import json
import time

import pandas as pd
import websockets

from lob.validate import flatten, validate_snapshot

WS_URL = "wss://stream.binance.com:9443/ws/{symbol}@depth20@100ms"
RECV_TIMEOUT_S = 10  # this long with no message means the link is dead
MAX_BACKOFF_S = 30.0


async def collect(symbol: str, duration_s: float, out_path: str) -> dict:
    deadline = time.time() + duration_s
    rows: list[dict] = []
    dropped = 0
    reconnects = -1
    backoff = 1.0
    while time.time() < deadline:
        reconnects += 1
        try:
            async with websockets.connect(WS_URL.format(symbol=symbol)) as ws:
                backoff = 1.0
                while time.time() < deadline:
                    raw = await asyncio.wait_for(ws.recv(), timeout=RECV_TIMEOUT_S)
                    msg = json.loads(raw)
                    bids = [(float(p), float(q)) for p, q in msg.get("bids", [])]
                    asks = [(float(p), float(q)) for p, q in msg.get("asks", [])]
                    if validate_snapshot(bids, asks):
                        rows.append(flatten(int(time.time() * 1000), bids, asks))
                    else:
                        dropped += 1
        except (OSError, TimeoutError, json.JSONDecodeError, websockets.WebSocketException):
            await asyncio.sleep(min(backoff, MAX_BACKOFF_S))
            backoff *= 2
    if rows:
        pd.DataFrame(rows).to_parquet(out_path)
    return {
        "symbol": symbol,
        "rows": len(rows),
        "dropped": dropped,
        "reconnects": max(reconnects, 0),
        "out": out_path,
    }
