#!/usr/bin/env python3
import os
import math

FILELIST  = "../refCalibrationResults/fastani/filelist_refseq.txt"
CHUNK_DIR = "../refCalibrationResults/fastani/chunks"

# 665 genomes → 16 chunks is fine (tweak if you like)
N_CHUNKS = 16

def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)

    with open(FILELIST) as f:
        genomes = [line.strip() for line in f if line.strip()]

    n = len(genomes)
    print(f"[INFO] Total genomes in filelist_refseq: {n}")

    if n == 0:
        raise SystemExit("[ERROR] No genomes in filelist_refseq")

    chunk_size = math.ceil(n / N_CHUNKS)

    chunks = [
        genomes[i * chunk_size:(i + 1) * chunk_size]
        for i in range(N_CHUNKS)
    ]

    for i, ch in enumerate(chunks):
        q_name = os.path.join(CHUNK_DIR, f"Q_{i:02d}.list")
        r_name = os.path.join(CHUNK_DIR, f"R_{i:02d}.list")
        with open(q_name, "w") as fq, open(r_name, "w") as fr:
            for g in ch:
                fq.write(g + "\n")
                fr.write(g + "\n")
        print(f"[INFO] Wrote Q_{i:02d}.list and R_{i:02d}.list with {len(ch)} genomes")

    print("[DONE] Split into Q/R chunks.")

if __name__ == "__main__":
    main()

