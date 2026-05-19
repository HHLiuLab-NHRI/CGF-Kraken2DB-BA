#!/usr/bin/env python3
import os
import gzip
import multiprocessing as mp
from functools import partial
from tqdm import tqdm

DATA_DIR = "../data/fungi_all"
OUT_LIST = "../results/double_gzip_list.txt"

os.makedirs(os.path.dirname(OUT_LIST), exist_ok=True)

########################################
# Helper function: detect double-gzip / corrupted
########################################
def check_one(path):
    fname = os.path.basename(path)

    # 1) Test gzip structure
    rc = os.system(f"gzip -t '{path}' > /dev/null 2>&1")
    if rc != 0:
        return (fname, "BROKEN_GZIP")

    try:
        # 2) Decompress a small chunk
        with gzip.open(path, "rb") as f:
            head = f.read(4096)
    except Exception:
        return (fname, "UNREADABLE_AFTER_GZIP")

    if len(head) == 0:
        return (fname, "EMPTY_AFTER_GZIP")

    # 3) Check FASTA / FASTQ magic
    first_char = chr(head[0])
    if first_char in [">", "@"]:
        return None  # OK file

    # Otherwise wrong content
    return (fname, "DOUBLE_GZIPPED_OR_BINARY")


########################################
# Main
########################################
def main():
    print("=== Scanning for double-gzipped FASTA files ===")

    files = sorted(
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.endswith(".fna.gz")
    )

    print(f"Total .fna.gz files found: {len(files)}")

    bad_entries = []

    # Multiprocessing pool
    with mp.Pool(processes=64) as pool:
        # Use tqdm for progress bar
        for result in tqdm(
            pool.imap_unordered(check_one, files),
            total=len(files),
            desc="Checking files",
        ):
            if result is not None:
                bad_entries.append(result)

    # Save
    with open(OUT_LIST, "w") as out:
        for fname, reason in bad_entries:
            out.write(f"{fname}\t{reason}\n")

    print(f"\nFound {len(bad_entries)} suspicious files.")
    print(f"List written to: {OUT_LIST}")
    print("=== Done ===")


if __name__ == "__main__":
    main()

