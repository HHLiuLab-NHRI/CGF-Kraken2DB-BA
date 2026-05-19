#!/usr/bin/env python3
import os
import gzip
import shutil
import multiprocessing as mp
from tqdm import tqdm

DATA_DIR = "../data/fungi_all"
BAD_LIST = "../results/double_gzip_list.txt"
LOG_FILE = "../results/double_gzip_fix.log"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


###############################
# Helper functions
###############################

def is_gzip_bytes(data: bytes) -> bool:
    """Check if data begins with gzip magic."""
    return len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B

def looks_like_fasta(data: bytes) -> bool:
    """Check if uncompressed data looks like FASTA/FASTQ."""
    if not data:
        return False
    return chr(data[0]) in [">", "@"]


def process_one(fname):
    """
    Validate and repair one file.
    Returns: (filename, status_string)
    """
    path = os.path.join(DATA_DIR, fname)

    if not os.path.exists(path):
        return (fname, "ERROR: file missing")

    # Stage 1: gunzip once to RAM
    try:
        with gzip.open(path, "rb") as f:
            level1 = f.read()
    except Exception as e:
        return (fname, f"ERROR: cannot gunzip once ({e})")

    # After first gunzip, contents should still be gzip if double-gzipped
    if not is_gzip_bytes(level1):
        return (fname, "SKIP: not actually double-gzipped")

    # Stage 2: decompress second layer
    try:
        level2 = gzip.decompress(level1)
    except Exception as e:
        return (fname, f"ERROR: second gunzip failed ({e})")

    # Validate FASTA content
    if not looks_like_fasta(level2):
        return (fname, "ERROR: final output not FASTA-like")

    # Stage 3: Write corrected single-gzip data
    tmp_path = path + ".tmp"

    try:
        with open(tmp_path, "wb") as f:
            f.write(level1)   # level1 is correct single-layer gzip

        shutil.move(tmp_path, path)
        return (fname, "FIXED")

    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return (fname, f"ERROR: failed to overwrite ({e})")


###############################
# Main
###############################

def main():
    print("=== Fixing double-gzipped fungal genomes (parallel) ===")

    # Load list
    targets = []
    with open(BAD_LIST) as f:
        for line in f:
            parts = line.strip().split("\t")
            if not parts:
                continue
            fname = parts[0]
            if fname.endswith(".fna.gz"):
                targets.append(fname)

    print(f"Files to inspect: {len(targets)}")

    # Process in parallel with progress bar
    results = []
    with mp.Pool(processes=64) as pool:
        for res in tqdm(pool.imap_unordered(process_one, targets),
                        total=len(targets),
                        desc="Repairing"):
            results.append(res)

    # Write log
    with open(LOG_FILE, "w") as log:
        for fname, msg in results:
            log.write(f"{fname}\t{msg}\n")

    print(f"\nLog written: {LOG_FILE}")
    print("=== Done ===")


if __name__ == "__main__":
    main()

