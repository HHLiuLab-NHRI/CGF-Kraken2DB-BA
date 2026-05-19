#!/usr/bin/env python3
import os
import pandas as pd
import sys

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
ASSIGNMENT_FILE = "../CGFvsRefResults/CGF_species_assignment.tsv"
DATA_DIR        = "../data/fungi_all"
OUT_DIR         = "../CGFNovelResults"
OUT_FILE        = os.path.join(OUT_DIR, "filelist_novel.txt")

os.makedirs(OUT_DIR, exist_ok=True)

def main():
    print(f"[INFO] Reading assignment file: {ASSIGNMENT_FILE}")
    if not os.path.exists(ASSIGNMENT_FILE):
        print(f"[ERROR] Assignment file not found: {ASSIGNMENT_FILE}")
        sys.exit(1)

    # Load assignments
    df = pd.read_csv(ASSIGNMENT_FILE, sep='\t')
    
    # ---------------------------------------------------------
    # CRITICAL UPDATE: Filter for ALL Novel types
    # Captures "Novel" AND "Novel (No Hits)"
    # ---------------------------------------------------------
    novel_df = df[df['status'].str.startswith('Novel')]
    
    if novel_df.empty:
        print("[WARN] No genomes with status starting with 'Novel' found. Exiting.")
        sys.exit(0)
        
    print(f"[INFO] Found {len(novel_df)} novel genomes (including 0-hit genomes).")

    # Build paths
    paths = []
    missing = []
    
    for filename in novel_df['query_genome']:
        # Ensure filename is the full path
        # The assignment file usually has just the basename (e.g. GCA_000.fna.gz)
        full_path = os.path.join(DATA_DIR, filename)
        
        if os.path.exists(full_path):
            paths.append(full_path)
        else:
            missing.append(filename)

    # Report
    if missing:
        print(f"[WARN] {len(missing)} files missing from data dir:")
        for m in missing[:5]: print(f"  - {m}")
        if len(missing) > 5: print("  ... and more.")
    else:
        print("[INFO] All novel genome files found.")
    
    # Write output
    with open(OUT_FILE, "w") as f:
        for p in paths:
            f.write(p + "\n")
            
    print(f"[INFO] Wrote {len(paths)} paths to: {OUT_FILE}")

if __name__ == "__main__":
    main()
