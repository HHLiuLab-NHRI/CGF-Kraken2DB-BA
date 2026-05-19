#!/usr/bin/env python3
import os
import glob

# Where your RefSeq fungal genomes live
REFSEQ = "../data/refseq_fungi/*.fna.gz"

# Output
OUT = "../refCalibrationResults/fastani/filelist_refseq.txt"

def main():
    files = sorted(glob.glob(REFSEQ))
    if not files:
        raise SystemExit(f"No files matched pattern: {REFSEQ}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    with open(OUT, "w") as f:
        for fn in files:
            f.write(os.path.abspath(fn) + "\n")

    print(f"[INFO] Wrote {len(files)} ref genomes → {OUT}")

if __name__ == "__main__":
    main()

