import filecmp
from pathlib import Path
import tempfile
import pandas as pd
import pytest

from src.data_generator import generate_data, SEED

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DATA_DIR = PROJECT_ROOT / "data"

def test_reproducibility_seed_26120():
    """Verify that seed 26120 reproduces identical CSV data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        df_new, sc_new = generate_data(seed=SEED, output_dir=tmp_path)

        orig_well_csv = CANONICAL_DATA_DIR / "synthetic_well.csv"
        new_well_csv = tmp_path / "synthetic_well.csv"

        orig_sc_csv = CANONICAL_DATA_DIR / "scenario_catalogue.csv"
        new_sc_csv = tmp_path / "scenario_catalogue.csv"

        assert orig_well_csv.exists(), "Original synthetic_well.csv missing"
        assert orig_sc_csv.exists(), "Original scenario_catalogue.csv missing"

        # Compare DataFrames for numerical and structural identity
        orig_df = pd.read_csv(orig_well_csv)
        new_well_df = pd.read_csv(new_well_csv)
        pd.testing.assert_frame_equal(orig_df, new_well_df, check_exact=True)

        orig_sc = pd.read_csv(orig_sc_csv)
        new_sc_df = pd.read_csv(new_sc_csv)
        pd.testing.assert_frame_equal(orig_sc, new_sc_df, check_exact=True)

        # Byte comparison
        orig_bytes = orig_well_csv.read_bytes().replace(b"\r\n", b"\n")
        new_bytes = new_well_csv.read_bytes().replace(b"\r\n", b"\n")
        assert orig_bytes == new_bytes, "synthetic_well.csv is not byte-identical under normalized line endings"
