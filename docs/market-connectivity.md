# Market connectivity notes

How the collector (`src/lob/collector.py`) connects to Binance, stays
connected, and decides what to keep. Written against the code as it stands;
limitations are listed as plainly as the features.

## The connection

One websocket per symbol to Binance's public partial book depth stream:

```
wss://stream.binance.com:9443/ws/{symbol}@depth20@100ms
```

Unauthenticated market data: no API key, no account. Each message is a full
snapshot of the top 20 levels on both sides, pushed every 100ms.

**Why this stream and not the diff stream.** The `@depth` diff stream sends
incremental updates that must be applied in order to a REST snapshot, with
update IDs checked for gaps; one missed message silently corrupts the local
book until it is rebuilt. Full snapshots trade bandwidth and depth (20
levels, not the whole book) for a simpler guarantee: every message stands
alone, so a dropped connection loses time, never consistency.

## Staying connected

| Event | What the collector does |
| --- | --- |
| Connection opens | Resets the backoff to 1 second |
| No message for 10 seconds | `wait_for` times out; treated as a dead connection, reconnect |
| Socket error or server close | Caught (`OSError`, `TimeoutError`, `WebSocketException`); reconnect |
| Malformed JSON | Caught; also triggers a reconnect (see limitations) |
| Reconnect | Sleeps 1, 2, 4, 8, 16, then 30 seconds maximum between attempts |
| Deadline reached | Stops, writes parquet, returns counts |

A 10 second silence on a stream that should tick every 100ms is a strong
signal the connection is dead even if the socket has not said so. Binance
also documents that a single connection is only valid for 24 hours; the
reconnect loop covers that case with no special handling.

The run returns `rows`, `dropped` and `reconnects` so every collection says
how clean it was, not just how big.

## What gets kept

Every snapshot passes `validate_snapshot` (`src/lob/validate.py`) or is
counted in `dropped` and never written:

- both sides non-empty
- every quantity strictly positive
- bids strictly descending, asks strictly ascending from the best level
- best bid strictly below best ask (a crossed book is impossible in a
  matched market and poisons every feature computed from it)

Kept snapshots are flattened to one row: `ts_ms`, then price and quantity
for each of the 20 levels on each side (81 columns).

## Measured on the first run (27 Aug 2026, BTC/USDT)

| Measure | Value |
| --- | --- |
| Snapshots stored | 589 over 58.8 seconds |
| Rate | 10.02 per second |
| Median / worst inter-arrival | 100ms / 119ms |
| Crossed or zero-size books stored | 0 |

## Known limitations

1. **Receive time, not exchange time.** `ts_ms` is local receive time; the
   partial depth stream carries no event timestamp, so network latency and
   jitter are folded in.
2. **One bad message costs a reconnect.** A JSON decode error is handled at
   the connection level, so the socket is dropped and reopened instead of
   skipping just that message.
3. **Everything is held in memory until the end.** Rows are written to
   parquet once, when the run finishes: a crash loses the whole run, and very
   long runs grow memory linearly.
4. **The deadline can overshoot.** It is checked between messages, so a run
   can end up to 10 seconds late while waiting on a slow `recv`.
5. **No jitter on the backoff.** Fine for one collector; many collectors
   restarting together would reconnect in lockstep.
6. **Top 20 levels only.** Deeper liquidity is invisible by design.

## Next steps for connectivity

- Flush to parquet in rolling files (for example every few minutes) so a
  crash loses minutes, not the run.
- Skip malformed messages in place and count them, instead of reconnecting.
- Add jitter to the backoff.
- Collect several symbols over one combined-stream connection.
- If full depth is ever needed, move to the diff stream with snapshot
  bootstrapping and update-ID gap checks, and test the gap handling.
