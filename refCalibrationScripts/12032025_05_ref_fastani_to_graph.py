#!/usr/bin/env python3

import os
import glob

MATRIX_DIR    = "../refCalibrationResults/fastani/matrix"
OUTFILE       = "../refCalibrationResults/fastani/edges_ref.tsv"

# You can later sweep these thresholds if you wish
ANI_THRESHOLD_SPECIES = 95.0  # default species-like
# (you can add higher-level thresholds separately later)

def normalize(path: str) -> str:
    """Return filename only (basename)."""
    return os.path.basename(path)

def main():
    edge_count = 0
    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

    with open(OUTFILE, "w") as outfile:
        for fname in sorted(glob.glob(os.path.join(MATRIX_DIR, "Q_*_R_*.out"))):

            if os.path.getsize(fname) == 0:
                print(f"[WARN] Empty file: {os.path.basename(fname)}")
                continue

            with open(fname) as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) < 3:
                        continue

                    q, r, ani_str = parts[0], parts[1], parts[2]

                    try:
                        ani = float(ani_str)
                    except ValueError:
                        continue

                    if ani < ANI_THRESHOLD_SPECIES:
                        continue

                    q_norm = normalize(q)
                    r_norm = normalize(r)
                    outfile.write(f"{q_norm}\t{r_norm}\t{ani}\n")
                    edge_count += 1

    print(f"[INFO] Merged edges: {edge_count} (ANI ≥ {ANI_THRESHOLD_SPECIES})")
    print(f"[INFO] Wrote: {OUTFILE}")

if __name__ == "__main__":
    main()

