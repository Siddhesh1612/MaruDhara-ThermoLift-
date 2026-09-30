import pandas as pd
import pytest
from src.db.adapter import DataAdapter

def test_validation_splits_chronological_no_leakage():
    """Verify strictly chronological splits with zero temporal leakage."""
    adapter = DataAdapter()
    df = adapter.get_observations_history()
    assert not df.empty, "Observations history should not be empty"

    # Convert timestamps
    df["ts"] = pd.to_datetime(df["timestamp"])

    # Extract cycles
    c1_2 = df[df["cycle_id"].isin([1, 2])]
    c3 = df[df["cycle_id"] == 3]
    c4 = df[df["cycle_id"] == 4]

    assert not c1_2.empty
    assert not c3.empty
    assert not c4.empty

    max_c1_2_ts = c1_2["ts"].max()
    min_c3_ts = c3["ts"].min()
    max_c3_ts = c3["ts"].max()
    min_c4_ts = c4["ts"].min()

    # Assert strict chronological progression (no temporal overlap / leakage)
    assert max_c1_2_ts < min_c3_ts, (
        f"Temporal leakage detected between fit cycles (max {max_c1_2_ts}) and validation cycle 3 (min {min_c3_ts})"
    )
    assert max_c3_ts < min_c4_ts, (
        f"Temporal leakage detected between validation cycle 3 (max {max_c3_ts}) and test cycle 4 (min {min_c4_ts})"
    )

    # Verify each cycle internally is monotonically increasing
    for cid in [1, 2, 3, 4]:
        cdf = df[df["cycle_id"] == cid]
        assert cdf["ts"].is_monotonic_increasing, f"Cycle {cid} timestamps are not strictly increasing"
