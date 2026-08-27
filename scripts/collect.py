"""Collect live L2 depth snapshots: python scripts/collect.py --symbol btcusdt --seconds 60"""

import argparse
import asyncio

from lob.collector import collect


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="btcusdt")
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or f"data/{args.symbol}_depth20.parquet"
    stats = asyncio.run(collect(args.symbol, args.seconds, out))
    print(stats)


if __name__ == "__main__":
    main()
