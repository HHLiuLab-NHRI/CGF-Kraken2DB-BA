#!/usr/bin/env python3
import os
import subprocess
import time

# ============================================================
# CONFIGURATION
# ============================================================

accession_file = "../meta/cgf_accessions.txt"
output_dir = "../data/CGF/"
log_dir = "../data/logs/CGF/"
log_file = os.path.join(log_dir, "download.log")

# Set to an integer for test mode (e.g., 5).  None for full run.
TEST_MODE_LIMIT = None     # Example: TEST_MODE_LIMIT = 5

# ============================================================
# LOGGING SETUP
# ============================================================

os.makedirs(output_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)

def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

log("=== Starting CGF genome download (wget + NCBI API v2) ===")

# ============================================================
# READ THE ACCESSION LIST
# ============================================================

if not os.path.exists(accession_file):
    log(f"ERROR: accession file not found: {accession_file}")
    exit(1)

with open(accession_file) as f:
    accessions = [x.strip() for x in f if x.strip()]

log(f"Loaded {len(accessions)} CGF accessions.")

# Test mode truncation
if TEST_MODE_LIMIT is not None:
    accessions = accessions[:TEST_MODE_LIMIT]
    log(f"TEST MODE ENABLED: only downloading first {TEST_MODE_LIMIT} genomes.")

# ============================================================
# FUNCTION TO BUILD NCBI FASTA-ONLY DOWNLOAD URL
# ============================================================

def build_ncbi_api_url(acc):
    """
    NCBI Datasets API v2 endpoint:
    downloads only FASTA (GENOME_FASTA) as a zip.
    """
    return (
        f"https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/{acc}/download"
        f"?include_annotation_type=GENOME_FASTA&filename={acc}.zip"
    )

# ============================================================
# MAIN DOWNLOAD LOOP
# ============================================================

for acc in accessions:

    # final output FASTA (we rename after extraction)
    final_fna = os.path.join(output_dir, f"{acc}.fna.gz")
    final_fna_raw = os.path.join(output_dir, f"{acc}.fna")

    # Skip if already downloaded
    if os.path.exists(final_fna) or os.path.exists(final_fna_raw):
        log(f"SKIP: {acc} already downloaded.")
        continue

    log(f"Downloading {acc}...")

    # Step 1: Download ZIP from API
    zip_path = os.path.join(output_dir, f"{acc}.zip")
    url = build_ncbi_api_url(acc)

    cmd_download = f"wget -q -O {zip_path} '{url}'"
    result = subprocess.call(cmd_download, shell=True)

    if result != 0 or not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        log(f"ERROR: failed to download ZIP for {acc}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        continue

    # Step 2: Extract ZIP to temporary folder
    extract_dir = os.path.join(output_dir, f"{acc}_tmp")
    os.makedirs(extract_dir, exist_ok=True)

    cmd_unzip = f"unzip -o {zip_path} -d {extract_dir}"
    result = subprocess.call(cmd_unzip, shell=True)

    if result != 0:
        log(f"ERROR: unzip failed for {acc}")
        os.remove(zip_path)
        subprocess.call(f"rm -rf {extract_dir}", shell=True)
        continue

    # Step 3: Find the FASTA inside extracted folder
    fna_found = None
    for root, dirs, files in os.walk(extract_dir):
        for fname in files:
            if fname.endswith(".fna") or fname.endswith(".fna.gz"):
                fna_found = os.path.join(root, fname)
                break
        if fna_found:
            break

    # Check for FASTA existence
    if not fna_found:
        log(f"ERROR: FASTA not found inside {acc}.zip")
        os.remove(zip_path)
        subprocess.call(f"rm -rf {extract_dir}", shell=True)
        continue

    # Step 4: Move FASTA to final directory
    if fna_found.endswith(".gz"):
        os.rename(fna_found, final_fna)
        log(f"SUCCESS: {acc} downloaded as {acc}.fna.gz")
    else:
        os.rename(fna_found, final_fna_raw)
        log(f"SUCCESS: {acc} downloaded as {acc}.fna")

    # Cleanup
    os.remove(zip_path)
    subprocess.call(f"rm -rf {extract_dir}", shell=True)

log("=== CGF genome download complete ===")

