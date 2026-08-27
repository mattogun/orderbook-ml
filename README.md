# Limit Order Book ML

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
