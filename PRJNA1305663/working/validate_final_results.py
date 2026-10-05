#!/usr/bin/env python3
"""Validate direct-CI outputs against the final manuscript analysis."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED = {
    ("default", "R1"): {"genera": 65, "fdr001": 11},
    ("default", "R2"): {"genera": 65, "fdr001": 8},
    ("enhanced", "R1"): {"genera": 295, "fdr001": 27},
    ("enhanced", "R2"): {"genera": 295, "fdr001": 23},
    ("nonenhanced", "R1"): {"genera": 69, "fdr001": 11},
    ("nonenhanced", "R2"): {"genera": 69, "fdr001": 7},
}

KEY = {
    ("enhanced", "R1", "Penicillium"): {"fdr": 0.0075727260760048, "r": 0.420, "lo": 0.2059248225679843, "hi": 0.6340751774320156},
    ("enhanced", "R2", "Penicillium"): {"fdr": 0.0081941137919873, "r": 0.423, "lo": 0.2083040650160035, "hi": 0.6366959349839967},
    ("enhanced", "R1", "Aspergillus"): {"fdr": 0.0454689597078306, "r": 0.333, "lo": 0.1036520492219472, "hi": 0.5623479507780527},
    ("enhanced", "R2", "Aspergillus"): {"fdr": 0.0484631041411409, "r": 0.321, "lo": 0.0898586714690393, "hi": 0.5521413285309605},
}


def require_close(actual, expected, label, atol=5e-10):
    if not np.isclose(actual, expected, atol=atol, rtol=0):
        raise AssertionError(f"{label}: expected {expected}, observed {actual}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stats_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "statistics_direct_ci",
    )
    args = parser.parse_args()

    for (db, read), expected in EXPECTED.items():
        path = args.stats_dir / f"{db}_EffectSizes_DirectCI_{read}.csv"
        data = pd.read_csv(path)
        n_sig = int((data["FDR_adj_p"] < 0.01).sum())
        if len(data) != expected["genera"] or n_sig != expected["fdr001"]:
            raise AssertionError(
                f"{db} {read}: expected {expected}, observed "
                f"genera={len(data)}, fdr001={n_sig}"
            )
        print(f"PASS {db:11s} {read}: {len(data)} genera; {n_sig} at FDR<0.01")

    for (db, read, genus), expected in KEY.items():
        path = args.stats_dir / f"{db}_EffectSizes_DirectCI_{read}.csv"
        data = pd.read_csv(path)
        row = data.loc[data["Genus"] == genus]
        if len(row) != 1:
            raise AssertionError(f"Expected one {genus} row in {path}")
        row = row.iloc[0]
        require_close(float(row["FDR_adj_p"]), expected["fdr"], f"{genus} {read} FDR")
        require_close(float(row["Rank_Biserial_Effect"]), expected["r"], f"{genus} {read} r", atol=5e-4)
        require_close(float(row["Rank_Biserial_CI95_Lower"]), expected["lo"], f"{genus} {read} CI low")
        require_close(float(row["Rank_Biserial_CI95_Upper"]), expected["hi"], f"{genus} {read} CI high")
        print(
            f"PASS {genus:11s} {read}: FDR={row['FDR_adj_p']:.6g}, "
            f"r={row['Rank_Biserial_Effect']:.3f}, "
            f"95% CI={row['Rank_Biserial_CI95_Lower']:.3f} to {row['Rank_Biserial_CI95_Upper']:.3f}"
        )

    print("All final-analysis checks passed.")


if __name__ == "__main__":
    main()
