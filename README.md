# Limit Order Book ML

![ci](https://github.com/mattogun/orderbook-ml/actions/workflows/ci.yml/badge.svg)

Predicting short-horizon mid-price direction from raw limit order book data.
The dataset is self-collected: a fault-tolerant websocket collector streams
live L2 depth (top 20 levels, 100ms) into validated parquet.

## Status

- [x] Collector: reconnecting websocket client, snapshot validation
      (rejects crossed/unsorted/empty books), integrity-tested
- [ ] DeepLOB (CNN+LSTM) reproduction against the published FI-2010 benchmark
- [ ] Same architecture on self-collected data + honest transaction-cost analysis

No profitable-strategy claims will ever appear here: predicting direction
above chance and surviving costs are different universes, and this project
measures the gap rather than pretending it away.

## Where the data comes from

Two sources, kept deliberately separate: a public benchmark to prove the
model implementation, and self-collected live depth to test it on.

### 1. Live L2 depth, self-collected from Binance (primary)

The collector subscribes to Binance's public **partial book depth** stream
for a spot symbol. No account, no API key: the stream is unauthenticated
market data.

```
wss://stream.binance.com:9443/ws/btcusdt@depth20@100ms
```

Each message is a complete snapshot of the top 20 price levels on both
sides, pushed every 100ms. An illustrative message (prices and quantities
arrive as strings):

```json
{
  "lastUpdateId": 71234567890,
  "bids": [["79430.72", "1.48248"], ["79430.71", "0.00013"], ...],
  "asks": [["79430.73", "0.29479"], ["79430.74", "0.00076"], ...]
}
```

Because every message is a full snapshot rather than a diff, there is no
sequence-number reconciliation to get wrong. A dropped connection loses
time, never consistency: the collector reconnects with capped exponential
backoff and carries on.

**Validation before storage.** Each snapshot passes `validate_snapshot`
(`src/lob/validate.py`) or is counted and dropped. Rejected books:

| Book | Why it is rejected |
|------|--------------------|
| empty bids or asks | nothing to compute a mid-price from |
| any quantity `<= 0` | a level with no size is not a level |
| bids not strictly descending from best | corrupt ordering |
| asks not strictly ascending from best | corrupt ordering |
| best bid `>=` best ask (crossed) | impossible in a matched book; a feature computed from it is poison |

**Storage.** Each valid snapshot is flattened to one row and written to
parquet with the schema `ts_ms, b_px_0, b_qty_0, a_px_0, a_qty_0, ...,
a_qty_19` (81 columns). Real rows from the first run, 27 Aug 2026, showing
the top two levels only:

| utc time (ms) | b_px_0 | b_qty_0 | a_px_0 | a_qty_0 | b_px_1 | b_qty_1 | a_px_1 | a_qty_1 |
|---|---|---|---|---|---|---|---|---|
| 11:39:16.690 | 79430.72 | 1.48248 | 79430.73 | 0.29479 | 79430.71 | 0.00013 | 79430.74 | 0.00076 |
| 11:39:16.790 | 79430.72 | 1.49248 | 79430.73 | 0.15158 | 79430.71 | 0.00013 | 79430.74 | 0.00076 |
| 11:39:16.891 | 79430.72 | 1.49248 | 79430.73 | 0.40170 | 79430.71 | 0.00027 | 79430.74 | 0.00076 |
| 11:39:46.709 | 79424.00 | 3.05540 | 79424.01 | 7.02509 | 79423.99 | 0.00091 | 79424.02 | 0.00013 |
| 11:40:15.489 | 79408.15 | 1.80557 | 79408.16 | 0.49997 | 79408.14 | 0.00036 | 79408.17 | 0.00013 |

That run in numbers: 589 snapshots over 58.8s (10.02/s, so the 100ms
cadence held), median inter-arrival 100ms, worst gap 119ms, zero crossed
books, zero non-positive quantities in the stored file. Mid-price moved
from 79440.76 to 79400.26 with the spread pinned at one tick (0.01) the
whole time, which is exactly why a one-minute BTC sample is a smoke test
and not a dataset.

**Known limitation.** `ts_ms` is the local receive time
(`int(time.time() * 1000)`), not the exchange's event time; the partial
depth stream does not carry one. Latency and jitter are therefore folded
into the timestamp. Fine for 100ms sampling, and stated here so nobody
mistakes it for exchange-clock data.

Collect your own:

```
python scripts/collect.py --symbol btcusdt --seconds 3600
python scripts/collect.py --symbol ethusdt --seconds 3600 --out data/ethusdt_depth20.parquet
```

Output goes to `data/`, which is git-ignored: the dataset is reproducible
from the command, not from the repo.

### 2. FI-2010 benchmark (for validating the model, not the thesis)

The DeepLOB reproduction is checked against the public **FI-2010** dataset
(Ntakaris et al., 2018, *Benchmark dataset for mid-price forecasting of
limit order book data with machine learning*): ten trading days in June
2010 of ten-level order book data for five NASDAQ Nordic stocks, with the
published normalisations and mid-price direction labels at several
horizons. It exists in this project for one reason: if the CNN+LSTM cannot
match the published numbers on the published data, any result on the
self-collected data is meaningless. FI-2010 is downloaded separately and
also lives under `data/`; it is not redistributed here.

## Next steps

Roughly in order:

1. **Deeper dataset.** Longer collection runs across several symbols and
   sessions; one afternoon of depth is a demo, not a dataset. The collector
   is built to run unattended, so this is mostly wall-clock time.
2. **Evaluation before models.** Same discipline as the knowledge-tracing
   repo: mid-price direction labels at fixed horizons, a strictly temporal
   train/test split, and leakage tests in CI before any network is trusted.
3. **DeepLOB reproduction.** CNN + LSTM from the paper against the published
   FI-2010 benchmark, to prove the implementation before pointing it at
   unfamiliar data.
4. **Same architecture on the collected data.** The interesting part:
   FI-2010 is Nordic equities from 2010; live crypto depth is a different
   regime, and the performance gap is the finding either way.
5. **Transaction cost analysis.** Direction-above-chance minus fees, spread
   and slippage. This is where honest projects usually die, which is why
   it is on the list.
6. **Later: port the collector to Rust.** Lower jitter at the 100ms sampling
   edge and a good excuse to learn the language properly.
