from lob.validate import flatten, validate_snapshot

GOOD_BIDS = [(100.0, 2.0), (99.5, 1.0), (99.0, 5.0)]
GOOD_ASKS = [(100.5, 1.5), (101.0, 3.0), (101.5, 2.0)]


def test_valid_book_passes():
    assert validate_snapshot(GOOD_BIDS, GOOD_ASKS)


def test_crossed_book_rejected():
    assert not validate_snapshot([(101.0, 1.0)], [(100.5, 1.0)])


def test_unsorted_bids_rejected():
    assert not validate_snapshot([(99.0, 1.0), (100.0, 1.0)], GOOD_ASKS)


def test_nonpositive_quantity_rejected():
    assert not validate_snapshot([(100.0, 0.0)], GOOD_ASKS)


def test_empty_side_rejected():
    assert not validate_snapshot([], GOOD_ASKS)


def test_flatten_pads_to_depth():
    row = flatten(123, GOOD_BIDS, GOOD_ASKS, depth=5)
    assert row["ts_ms"] == 123
    assert row["b_px_0"] == 100.0 and row["a_px_0"] == 100.5
    assert row["b_px_4"] == 0.0 and row["a_qty_4"] == 0.0
    assert len(row) == 1 + 4 * 5
