#!/usr/bin/env python3
"""
Unified splitter for CGF queries AND RefSeq references.
Run from: CGFvsRefScripts/
Creates:
  ../CGFvsRefResults/chunks/Q_*.list   (CGF)
  ../CGFvsRefResults/chunks/R_*.list   (RefSeq)
"""

import os
import math

BASE = os.path.dirname(os.path.abspath(__file__))

# Input paths
CGF_FILELIST = os.path.join(BASE, "../CGFvsRefResults/filelist_cgf.txt")
REFSEQ_FILELIST = os.path.join(BASE, "../refCalibrationResults/fastani/filelist_refseq.txt")

# Output directory
OUTDIR = os.path.join(BASE, "../CGFvsRefResults/chunks")
os.makedirs(OUTDIR, exist_ok=True)


# -------------------------
# Helper
# -------------------------
def read_list(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] Missing file list: {path}")
    with open(path) as f:
        return [x.strip() for x in f if x.strip()]


def write_chunks(label, items, chunk_size, outdir):
    n = len(items)
    num_chunks = math.ceil(n / chunk_size)
    print(f"[INFO] Creating {num_chunks} {label}-chunks (chunk size={chunk_size})")

    for i in range(num_chunks):
        chunk_items = items[i * chunk_size : (i + 1) * chunk_size]
        out_path = os.path.join(outdir, f"{label}_{i+1}.list")
        with open(out_path, "w") as out:
            out.write("\n".join(chunk_items) + "\n")

    print(f"[DONE] {label}-chunks written → {outdir}")


# -------------------------
# Load lists
# -------------------------

print(f"[INFO] Reading CGF file list: {CGF_FILELIST}")
cgf_files = read_list(CGF_FILELIST)
print(f"[INFO] CGF genomes: {len(cgf_files)}")

print(f"[INFO] Reading RefSeq reference list: {REFSEQ_FILELIST}")
ref_files = read_list(REFSEQ_FILELIST)
print(f"[INFO] RefSeq reference genomes: {len(ref_files)}")


# -------------------------
# Warn if any accession overlaps
# -------------------------
cgf_accs = {os.path.basename(x).split(".")[0] for x in cgf_files}
ref_accs = {os.path.basename(x).split(".")[0] for x in ref_files}

overlap = sorted(cgf_accs & ref_accs)

if overlap:
    print("[WARNING] Overlapping accessions found between CGF and RefSeq!!")
    for acc in overlap:
        print("  -", acc)
    print("[WARNING] You should remove duplicates before running fastANI.")


# -------------------------
# Split CGF queries (Q_*)
# -------------------------
write_chunks("Q", cgf_files, chunk_size=50, outdir=OUTDIR)

# -------------------------
# Split RefSeq references (R_*)
# -------------------------
write_chunks("R", ref_files, chunk_size=100, outdir=OUTDIR)

print("\n[COMPLETE] All query and reference chunk lists generated.")

