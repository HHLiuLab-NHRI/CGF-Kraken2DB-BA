#!/usr/bin/env python3
import os, glob

PHF = "../data/PHF/*.fna"
CGF = "../data/CGF/*.fna"

files = sorted(glob.glob(PHF) + glob.glob(CGF))

out = "../results/fastani/filelist.txt"
os.makedirs(os.path.dirname(out), exist_ok=True)

with open(out, "w") as f:
    for fn in files:
        f.write(os.path.abspath(fn) + "\n")

print(f"Wrote {len(files)} genomes → {out}")

