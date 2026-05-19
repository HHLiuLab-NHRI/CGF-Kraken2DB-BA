#!/usr/bin/env python3
import os
import gzip
import pandas as pd

# ================= CONFIGURATION =================
REFSEQ_DIR = "../data/refseq_fungi"
SUMMARY_FILE = "../meta/fungi_all/assembly_summary_fungi_refseq.txt"
CUSTOM_LIBRARY_DIR = "../Kraken2_DB/library/added"
# =================================================

def main():
    print("--- Formatting Local RefSeq Genomes for Kraken 2 ---")
    
    if not os.path.exists(SUMMARY_FILE):
        print(f"[ERROR] Cannot find summary file: {SUMMARY_FILE}")
        return
        
    os.makedirs(CUSTOM_LIBRARY_DIR, exist_ok=True)

    # 1. Load the RefSeq metadata to map Accession -> TaxID
    print("[INFO] Loading NCBI Assembly Summary...")
    taxid_map = {}
    with open(SUMMARY_FILE) as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) > 5:
                accession = parts[0]  # e.g., GCF_000146045.2
                taxid = parts[5]      # The official NCBI TaxID
                taxid_map[accession] = taxid

    # 2. Find all local RefSeq files
    local_files = [f for f in os.listdir(REFSEQ_DIR) if f.endswith(".fna.gz") or f.endswith(".fna")]
    print(f"[INFO] Found {len(local_files)} local RefSeq genomes in {REFSEQ_DIR}")

    # 3. Process each file
    success_count = 0
    for fname in local_files:
        # Extract the accession (e.g., remove .fna.gz or .fna)
        acc = fname.replace(".fna.gz", "").replace(".fna", "")
        
        if acc not in taxid_map:
            print(f"   [WARN] No TaxID mapping found for {acc}, skipping.")
            continue
            
        taxid = taxid_map[acc]
        in_path = os.path.join(REFSEQ_DIR, fname)
        out_path = os.path.join(CUSTOM_LIBRARY_DIR, f"RefSeq_{acc}_{taxid}.fna")
        
        # Read the genome and rewrite headers
        open_func = gzip.open if in_path.endswith('.gz') else open
        mode = 'rt' if in_path.endswith('.gz') else 'r'
        
        with open_func(in_path, mode) as f_in, open(out_path, 'w') as f_out:
            for line in f_in:
                if line.startswith(">"):
                    parts = line.strip().split(" ", 1)
                    seq_id = parts[0]
                    rest = parts[1] if len(parts) > 1 else ""
                    # Inject Kraken tag
                    f_out.write(f"{seq_id}|kraken:taxid|{taxid} {rest}\n")
                else:
                    f_out.write(line)
        
        success_count += 1
        if success_count % 50 == 0:
            print(f"   [PROGRESS] Processed {success_count}/{len(local_files)} genomes...")

    print("-" * 50)
    print(f"[DONE] Successfully formatted {success_count} local RefSeq genomes.")
    print(f"[INFO] All files (Novel + RefSeq) are now ready in: {CUSTOM_LIBRARY_DIR}")

if __name__ == "__main__":
    main()
