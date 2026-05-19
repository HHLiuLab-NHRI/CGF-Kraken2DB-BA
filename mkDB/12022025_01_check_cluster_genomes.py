#!/usr/bin/env python3
import os
import sys
import pandas as pd
import re

CLUSTER_FILE = "../results/clusters/01_components.tsv"
DATA_DIR = "../data/fungi_all"

def load_downloaded_accessions(dirpath):
    """Load all downloaded genomes: GCA_xxx.x.fna.gz -> GCA_xxx.x"""
    accs = set()
    for fn in os.listdir(dirpath):
        if fn.endswith(".fna.gz"):
            base = fn.replace(".fna.gz", "")   # keep GCA_xxx.x
            accs.add(base)
    return accs

def normalize_accession(s):
    """Convert strings like 'GCA_000225625.2.fna' -> 'GCA_000225625.2'"""
    s = s.strip()
    s = s.replace(".fna.gz", "")
    s = s.replace(".fna", "")
    # keep only valid GCA/GCF pattern
    m = re.search(r"(GC[AF]_\d+\.\d+)", s)
    return m.group(1) if m else None

def main():
    if not os.path.exists(CLUSTER_FILE):
        print(f"ERROR: Cannot find cluster file: {CLUSTER_FILE}")
        sys.exit(1)

    if not os.path.isdir(DATA_DIR):
        print(f"ERROR: Cannot find data directory: {DATA_DIR}")
        sys.exit(1)

    print(f"[1] Loading clusters from {CLUSTER_FILE}")
    df = pd.read_csv(CLUSTER_FILE, sep="\t", header=None,
                     names=["cluster", "components"])

    all_accs = set()

    # Each row may contain multiple comma-separated .fna entries
    for comp in df["components"]:
        if pd.isna(comp):
            continue
        items = str(comp).split(",")
        for item in items:
            acc = normalize_accession(item)
            if acc:
                all_accs.add(acc)

    print(f"   - Total unique accessions in clusters = {len(all_accs)}")

    # Load downloaded genomes
    print(f"[2] Checking downloaded genomes in {DATA_DIR}")
    dl_accs = load_downloaded_accessions(DATA_DIR)
    print(f"   - Total .fna.gz files = {len(dl_accs)}")

    missing = sorted(all_accs - dl_accs)
    present = sorted(all_accs & dl_accs)
    extra = sorted(dl_accs - all_accs)

    print("\n=== SUMMARY ===")
    print(f"Cluster-defined accessions : {len(all_accs)}")
    print(f"Downloaded (present)       : {len(present)}")
    print(f"Missing                    : {len(missing)}")
    print(f"Extra not in clusters      : {len(extra)}")

    if missing:
        print("\n=== MISSING ACCESSIONS ===")
        for acc in missing:
            print(acc)

    if extra:
        print("\n=== EXTRA DOWNLOADED FILES ===")
        for acc in extra:
            print(acc)

if __name__ == "__main__":
    main()

