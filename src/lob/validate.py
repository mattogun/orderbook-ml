"""Order book snapshot validation.

A snapshot that fails any of these checks is corrupt and must be dropped,
not stored: a bad book poisons every feature computed downstream.
"""


def validate_snapshot(bids: list, asks: list) -> bool:
    """bids/asks: lists of (price, qty) as floats. True iff the book is sane."""
    if not bids or not asks:
        return False
    bp = [p for p, _ in bids]
    ap = [p for p, _ in asks]
    if any(q <= 0 for _, q in bids) or any(q <= 0 for _, q in asks):
        return False
    if bp != sorted(bp, reverse=True):  # bids must descend from best
        return False
    if ap != sorted(ap):  # asks must ascend from best
        return False
    return bp[0] < ap[0]  # book must not be crossed


def flatten(ts_ms: int, bids: list, asks: list, depth: int = 20) -> dict:
    """One snapshot -> one flat row: ts, b_px_i, b_qty_i, a_px_i, a_qty_i."""
    row = {"ts_ms": ts_ms}
    for i in range(depth):
        bp, bq = bids[i] if i < len(bids) else (0.0, 0.0)
        ap, aq = asks[i] if i < len(asks) else (0.0, 0.0)
        row[f"b_px_{i}"] = bp
        row[f"b_qty_{i}"] = bq
        row[f"a_px_{i}"] = ap
        row[f"a_qty_{i}"] = aq
    return row
