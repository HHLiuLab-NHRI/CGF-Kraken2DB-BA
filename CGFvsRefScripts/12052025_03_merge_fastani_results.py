#!/usr/bin/env python3
import os
import sys
import glob
import pandas as pd
from tqdm import tqdm

"""
Correct merge script for CGF × RefSeq FastANI results.
Handles 5-column FastANI output:

query  reference  ANI  fragments_mapped  fragments_total
"""

# ------------------------------------------------------------------
# Input / Output locations
# ------------------------------------------------------------------
FASTANI_DIR = "../CGFvsRefResults/fastani_out"
OUT_FILE = "../CGFvsRefResults/CGFvsRefSeq_merged.tsv"

# ------------------------------------------------------------------
# Column names expected in FastANI output
# ------------------------------------------------------------------
COLS = ["query", "reference", "ani", "fragments_mapped", "fragments_total"]

# ------------------------------------------------------------------
# Main merge logic
# ------------------------------------------------------------------
def read_fastani_file(path):
    """Read a single FastANI result file, with validation."""
    try:
        df = pd.read_csv(
            path,
            sep="\t",
            header=None,
            names=COLS,
            dtype=str,
            engine="python"
        )

        # Skip empty output
        if df.shape[0] == 0:
            return None

        # Ensure it has exactly 5 columns
        if df.shape[1] != 5:
            print(f"[WARN] Skipping malformed file: {path} (columns={df.shape[1]})")
            return None

        return df

    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        return None


def main():
    print(f"[INFO] Looking for chunk output files in: {FASTANI_DIR}")

    files = sorted(glob.glob(os.path.join(FASTANI_DIR, "Q_*__R_*.tsv")))
    print(f"[INFO] Found {len(files)} chunk files.")

    merged = []

    for f in tqdm(files, desc="Merging"):
        df = read_fastani_file(f)
        if df is not None:
            merged.append(df)

    if len(merged) == 0:
        print("[ERROR] No valid files found. Exiting.")
        sys.exit(1)

    merged_df = pd.concat(merged, ignore_index=True)
    print(f"[INFO] Total rows merged: {len(merged_df)}")

    merged_df.to_csv(OUT_FILE, sep="\t", index=False)
    print(f"[INFO] Written merged output to: {OUT_FILE}")


if __name__ == "__main__":
    main()

