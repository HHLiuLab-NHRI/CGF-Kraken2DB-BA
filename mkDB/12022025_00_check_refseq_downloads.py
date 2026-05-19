#!/usr/bin/env python3
import os
import sys

REFSEQ_FILE = "../meta/fungi_all/assembly_summary_fungi_refseq.txt"
DATA_DIR = "../data/fungi_all"

def load_refseq_accessions(path):
    accs = set()
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) > 0:
                acc = parts[0]   # GCF_XXXXX
                if acc:
                    accs.add(acc)
    return accs


def load_downloaded_accessions(dirpath):
    accs = set()
    for fn in os.listdir(dirpath):
        if fn.endswith(".fna.gz"):
            # expecting something like: GCF_00012345.1.fna.gz
            base = fn.replace(".fna.gz", "")
            accs.add(base)
    return accs


def main():
    if not os.path.exists(REFSEQ_FILE):
        print(f"ERROR: Cannot find RefSeq summary file: {REFSEQ_FILE}")
        sys.exit(1)
    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: Cannot find data directory: {DATA_DIR}")
        sys.exit(1)

    print("[1] Reading accessions from:", REFSEQ_FILE)
    refseq_accs = load_refseq_accessions(REFSEQ_FILE)
    print(f"   - Total RefSeq accessions = {len(refseq_accs)}")

    print("[2] Reading downloaded .fna.gz files from:", DATA_DIR)
    dl_accs = load_downloaded_accessions(DATA_DIR)
    print(f"   - Total .fna.gz files = {len(dl_accs)}")

    missing = sorted(refseq_accs - dl_accs)
    present = sorted(refseq_accs & dl_accs)
    extra = sorted(dl_accs - refseq_accs)

    print("\n=== SUMMARY ===")
    print(f"RefSeq accessions expected : {len(refseq_accs)}")
    print(f"Downloaded present         : {len(present)}")
    print(f"Missing                    : {len(missing)}")
    print(f"Extra (unexpected) files   : {len(extra)}")

    if missing:
        print("\n=== MISSING ACCESSIONS ===")
        for acc in missing:
            print(acc)

    if extra:
        print("\n=== EXTRA DOWNLOADED FILES (not in RefSeq list) ===")
        for acc in extra:
            print(acc)


if __name__ == "__main__":
    main()

