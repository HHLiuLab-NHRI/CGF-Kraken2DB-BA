#!/usr/bin/env python3
import os
import time
import subprocess

# ============================================================
# Configuration
# ============================================================

accession_file = "../meta/phf_accessions.txt"
output_dir = "../data/PHF/"
log_dir = "../data/logs/PHF/"
log_file = os.path.join(log_dir, "download.log")

# TEST MODE (set to integer or None)
TEST_MODE_LIMIT = None  # e.g., 5

# ============================================================
# Logging
# ============================================================

def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

# ============================================================
# Build new NCBI API download URL
# ============================================================

def build_ncbi_api_url(acc):
    # Official API endpoint for genome FASTA only
    url = (
        f"https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{acc}/download"
        "?include_annotation_type=GENOME_FASTA&filename="
        f"{acc}.zip"
    )
    return url

# ============================================================
# Setup
# ============================================================

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

log("=== Starting PHF genome download (NCBI API v2) ===")

# ============================================================
# Load accession list
# ============================================================

with open(accession_file) as f:
    accessions = [x.strip() for x in f if x.strip()]

log(f"Loaded {len(accessions)} accession IDs.")

if TEST_MODE_LIMIT is not None:
    accessions = accessions[:TEST_MODE_LIMIT]
    log(f"TEST MODE ENABLED: {TEST_MODE_LIMIT} genomes.")

# ============================================================
# Download loop
# ============================================================

for acc in accessions:
    out_zip = os.path.join(output_dir, f"{acc}.zip")
    out_fasta = os.path.join(output_dir, f"{acc}.fna")   # will find and rename later

    # Skip if .fna already exists
    if os.path.exists(out_fasta) or os.path.exists(out_fasta + ".gz"):
        log(f"SKIP: {acc} already downloaded.")
        continue

    log(f"Downloading {acc} ...")

    url = build_ncbi_api_url(acc)

    # Download the ZIP containing FASTA
    cmd = f"wget -q -O {out_zip} '{url}'"
    res = subprocess.call(cmd, shell=True)
    if res != 0 or not os.path.exists(out_zip):
        log(f"ERROR: Failed to download ZIP for {acc}")
        continue

    # Extract ZIP
    extract_dir = os.path.join(output_dir, acc)
    os.makedirs(extract_dir, exist_ok=True)

    res = subprocess.call(f"unzip -o {out_zip} -d {extract_dir}", shell=True)
    if res != 0:
        log(f"ERROR: Failed to unzip {acc}")
        os.remove(out_zip)
        continue

    # Locate FASTA inside expanded structure
    fna_path = None
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            if f.endswith(".fna") or f.endswith(".fna.gz"):
                fna_path = os.path.join(root, f)
                break

    if fna_path is None:
        log(f"ERROR: No FASTA file found for {acc}")
        continue

    # Move and rename to consistent path
    final_fna = os.path.join(output_dir, f"{acc}.fna.gz") if fna_path.endswith(".gz") else os.path.join(output_dir, f"{acc}.fna")
    os.rename(fna_path, final_fna)

    # Cleanup
    os.remove(out_zip)
    subprocess.call(f"rm -rf {extract_dir}", shell=True)

    log(f"SUCCESS: {acc} downloaded.")

log("=== PHF genome download script complete ===")
