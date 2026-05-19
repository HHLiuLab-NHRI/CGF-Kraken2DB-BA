#!/usr/bin/env python3
import os
import sys

CGF_ACC_FILE = "../meta/cgf_accessions.txt"
REFSEQ_LIST = "../refCalibrationResults/fastani/filelist_refseq.txt"
OUT_DIR = "../CGFvsRefResults"
OUT_FILE = os.path.join(OUT_DIR, "filelist_cgf.txt")

DATA_DIR = "../data/fungi_all"

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Helper to extract accession (GCA_XXXXX or GCF_XXXXX)
# ---------------------------------------------------------
def extract_acc(filename):
    """Extract accession from a full path or filename."""
    base = os.path.basename(filename)
    if base.startswith(("GCA_", "GCF_")):
        return base.split(".")[0]   # GCA_00012345.1.fna.gz → GCA_00012345
    return None

# ---------------------------------------------------------
# Load CGF accessions
# ---------------------------------------------------------
with open(CGF_ACC_FILE) as f:
    cgf_acc = [line.strip() for line in f if line.strip()]

print(f"[INFO] Loaded {len(cgf_acc)} CGF accessions")

# ---------------------------------------------------------
# Load RefSeq accessions
# ---------------------------------------------------------
refseq_acc = set()
with open(REFSEQ_LIST) as f:
    for line in f:
        acc = extract_acc(line.strip())
        if acc:
            refseq_acc.add(acc)

print(f"[INFO] Loaded {len(refseq_acc)} RefSeq accessions")

# ---------------------------------------------------------
# Check for overlaps (should NOT happen)
# ---------------------------------------------------------
duplicates = sorted(set(cgf_acc) & refseq_acc)

if duplicates:
    print("\n[ALERT] WARNING: ACCESSIONS PRESENT IN BOTH CGF AND REFSEQ!!")
    for d in duplicates:
        print("   DUPLICATE:", d)
    print("[ALERT] Resolve duplication before running FastANI.")
else:
    print("[INFO] No CGF–RefSeq duplicates found.")

# ---------------------------------------------------------
# Build the CGF file list
# ---------------------------------------------------------
missing = []
paths = []

for acc in cgf_acc:
    fname = f"{acc}.fna.gz"
    fullpath = os.path.join(DATA_DIR, fname)
    if os.path.exists(fullpath):
        paths.append(fullpath)
    else:
        missing.append(acc)

# Report missing genomes
if missing:
    print("\n[WARNING] Missing CGF genomes (not found in ../data/fungi_all/):")
    for m in missing:
        print("   MISSING:", m)
else:
    print("[INFO] All CGF genomes found in fungi_all directory.")

# ---------------------------------------------------------
# Write output list
# ---------------------------------------------------------
with open(OUT_FILE, "w") as out:
    for p in paths:
        out.write(p + "\n")

print(f"\n[INFO] Wrote CGF file list: {OUT_FILE}")
print(f"[INFO] Total CGF files written: {len(paths)}")

# ---------------------------------------------------------
# Final summary
# ---------------------------------------------------------
print("\n===== SUMMARY =====")
print("CGF accessions loaded:", len(cgf_acc))
print("RefSeq accessions loaded:", len(refseq_acc))
print("Duplicates:", len(duplicates))
print("Missing CGF files:", len(missing))
print("Final entries in filelist_cgf.txt:", len(paths))
print("===================")

