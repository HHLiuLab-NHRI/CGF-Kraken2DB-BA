#!/usr/bin/env python3
import os
import math

FILELIST = "../results/fastani/filelist.txt"
CHUNK_DIR = "../results/fastani/chunks"
N_CHUNKS = 20  # 20 Q-chunks and 20 R-chunks

os.makedirs(CHUNK_DIR, exist_ok=True)

with open(FILELIST) as f:
    genomes = [line.strip() for line in f if line.strip()]

n = len(genomes)
print(f"[INFO] Total genomes in filelist: {n}")

chunk_size = math.ceil(n / N_CHUNKS)

chunks = [
    genomes[i * chunk_size:(i + 1) * chunk_size]
    for i in range(N_CHUNKS)
]

# Write Q_XX.list and R_XX.list (same splits for both)
for i, ch in enumerate(chunks):
    q_name = os.path.join(CHUNK_DIR, f"Q_{i:02d}.list")
    r_name = os.path.join(CHUNK_DIR, f"R_{i:02d}.list")
    with open(q_name, "w") as fq, open(r_name, "w") as fr:
        for g in ch:
            fq.write(g + "\n")
            fr.write(g + "\n")
    print(f"[INFO] Wrote Q_{i:02d}.list and R_{i:02d}.list with {len(ch)} genomes")

print("[DONE] Split into 20 Q-chunks and 20 R-chunks.")

