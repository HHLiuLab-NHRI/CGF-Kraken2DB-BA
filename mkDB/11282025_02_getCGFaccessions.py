#!/usr/bin/env python3
import os
import json
import subprocess
import time
import math

# ============================================================
# Configuration
# ============================================================

bioproject = "PRJNA833221"
output_dir = "../meta/"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, "cgf_accessions.txt")
log_file = os.path.join(output_dir, "cgf_accessions.log")

CHUNK_SIZE = 200   # ESummary limit-safe

# ============================================================
# Logging
# ============================================================

def log(msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    with open(log_file, "a") as lf:
        lf.write(line + "\n")

log("=== Fetching CGF genome accessions via NCBI E-utilities (chunked) ===")

# ============================================================
# Step 1 — ESearch to get ALL assembly UIDs
# ============================================================

esearch_url = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    f"?db=assembly&term={bioproject}[BioProject]&retmax=20000&retmode=json"
)

uids_file = "uids.json"
cmd = f"wget -q -O {uids_file} '{esearch_url}'"

log(f"Running ESearch:\n   {esearch_url}")
res = subprocess.call(cmd, shell=True)

if res != 0 or not os.path.exists(uids_file):
    log("ERROR: ESearch failed.")
    exit(1)

with open(uids_file) as f:
    data = json.load(f)

uids = data.get("esearchresult", {}).get("idlist", [])

log(f"Found {len(uids)} UIDs in BioProject {bioproject}.")

if len(uids) == 0:
    log("ERROR: No UIDs found. Exiting.")
    exit(1)

# Cleanup
os.remove(uids_file)

# ============================================================
# Step 2 — Chunked ESummary queries
# ============================================================

accessions = []

num_chunks = math.ceil(len(uids) / CHUNK_SIZE)
log(f"Processing in {num_chunks} chunks of size ≤ {CHUNK_SIZE}.")

for i in range(num_chunks):
    chunk = uids[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]
    chunk_str = ",".join(chunk)

    log(f"Fetching chunk {i+1}/{num_chunks} with {len(chunk)} IDs.")

    esummary_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=assembly&id={chunk_str}&retmode=json"
    )

    summary_file = f"summary_{i}.json"
    cmd = f"wget -q -O {summary_file} '{esummary_url}'"
    res = subprocess.call(cmd, shell=True)

    if res != 0 or not os.path.exists(summary_file):
        log(f"ERROR: ESummary failed on chunk {i+1}. Skipping.")
        continue

    with open(summary_file) as f:
        sdata = json.load(f)

    # Extract accessions
    result = sdata.get("result", {})
    for uid in chunk:
        entry = result.get(uid, {})
        acc = entry.get("assemblyaccession")
        if acc and (acc.startswith("GCA_") or acc.startswith("GCF_")):
            accessions.append(acc)

    os.remove(summary_file)

# ============================================================
# Finalize
# ============================================================

accessions = sorted(set(accessions))

with open(output_file, "w") as f:
    for acc in accessions:
        f.write(acc + "\n")

log(f"Extracted {len(accessions)} CGF assembly accessions.")
log(f"Saved to: {output_file}")
log("=== CGF accession retrieval complete ===")

