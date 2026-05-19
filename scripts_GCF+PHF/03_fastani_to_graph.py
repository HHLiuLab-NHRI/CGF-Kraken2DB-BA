#!/usr/bin/env python3

import os
import glob

MATRIX_DIR = "../results/fastani/matrix"
OUTFILE = "../results/fastani/edges.tsv"

def normalize(path):
    """Return filename only (basename)."""
    return os.path.basename(path)

edge_count = 0

with open(OUTFILE, "w") as outfile:
    for fname in sorted(glob.glob(os.path.join(MATRIX_DIR, "Q_*_R_*.out"))):

        # Skip completely empty output files
        if os.path.getsize(fname) == 0:
            print(f"[WARN] Empty file: {os.path.basename(fname)}")
            continue

        with open(fname) as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) < 3:
                    continue

                q, r, ani_str = parts[0], parts[1], parts[2]

                # Convert ANI value
                try:
                    ani = float(ani_str)
                except ValueError:
                    continue

                # *************** IMPORTANT ***************
                # Apply species-level ANI threshold here
                if ani < 95.0:
                    continue
                # ******************************************

                q_norm = normalize(q)
                r_norm = normalize(r)

                outfile.write(f"{q_norm}\t{r_norm}\t{ani}\n")
                edge_count += 1

print(f"[INFO] Finished merging ANI edges: {edge_count} edges (ANI ≥ 95 kept).")

