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
