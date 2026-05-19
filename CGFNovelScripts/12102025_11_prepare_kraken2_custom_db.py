#!/usr/bin/env python3
import os
import pandas as pd
import gzip
import shutil

# ================= CONFIGURATION =================
# Inputs
NOVEL_ASSIGNMENTS = "../CGFNovelResults/novel_taxonomy_assignments.tsv"
NCBI_NODES        = "../refCalibrationResults/taxdump/nodes.dmp"
NCBI_NAMES        = "../refCalibrationResults/taxdump/names.dmp"
GENOME_DIR        = "../CGFNovelResults/genomes"

# Outputs
CUSTOM_TAXDUMP_DIR = "../Kraken2_DB/taxonomy"
CUSTOM_LIBRARY_DIR = "../Kraken2_DB/library/added"
os.makedirs(CUSTOM_TAXDUMP_DIR, exist_ok=True)
os.makedirs(CUSTOM_LIBRARY_DIR, exist_ok=True)

# Custom TaxID starting block (safe from NCBI overlap)
START_TAXID = 3000000000
# =================================================

def resolve_genome_path(base_name, search_dir):
    """
    Checks multiple common extensions to find the actual physical file.
    """
    extensions = [".fna.gz", ".fna", ".fasta.gz", ".fasta", ".fa.gz", ".fa", ".gz", ""]
    for ext in extensions:
        candidate = os.path.join(search_dir, base_name + ext)
        if os.path.exists(candidate):
            return candidate
    return None

def rewrite_fasta_for_kraken(input_path, output_path, taxid):
    """
    Reads a gzipped or uncompressed FASTA and writes an uncompressed FASTA
    with the kraken:taxid tag injected into every header.
    """
    open_func = gzip.open if input_path.endswith('.gz') else open
    mode = 'rt' if input_path.endswith('.gz') else 'r'
    
    with open_func(input_path, mode) as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            if line.startswith(">"):
                # Split at the first space to inject the taxid cleanly
                parts = line.strip().split(" ", 1)
                seq_id = parts[0]
                rest = parts[1] if len(parts) > 1 else ""
                
                # Format: >SequenceID|kraken:taxid|12345 Rest of header
                new_header = f"{seq_id}|kraken:taxid|{taxid} {rest}\n"
                f_out.write(new_header)
            else:
                f_out.write(line)

def main():
    print("--- Preparing Custom Kraken 2 Database Files ---")
    
    # 1. Load Novel Assignments
    try:
        df = pd.read_csv(NOVEL_ASSIGNMENTS, sep='\t')
    except Exception as e:
        print(f"[ERROR] Could not read assignments: {e}")
        return
        
    print(f"[INFO] Loaded {len(df)} novel clusters for TaxID minting.")

    # 2. Copy original NCBI taxdump files to our custom directory
    custom_nodes = os.path.join(CUSTOM_TAXDUMP_DIR, "nodes.dmp")
    custom_names = os.path.join(CUSTOM_TAXDUMP_DIR, "names.dmp")
    
    print("[INFO] Copying base NCBI taxonomy files...")
    shutil.copyfile(NCBI_NODES, custom_nodes)
    shutil.copyfile(NCBI_NAMES, custom_names)

    # 3. Mint TaxIDs, append to dumps, and process FASTAs
    current_taxid = START_TAXID
    success_count = 0
    
    print("[INFO] Minting TaxIDs, patching dumps, and rewriting FASTAs...")
    
    with open(custom_nodes, "a") as f_nodes, open(custom_names, "a") as f_names:
        for _, row in df.iterrows():
            cluster_name = str(row['Novel_Cluster'])
            parent_taxid = row['Parent_TaxID']
            genome_file_base = str(row['Query_Genome'])
            
            # Use fallback parent if missing or NaN
            if pd.isna(parent_taxid) or str(parent_taxid) == "None":
                parent_taxid = 4751 # Fungi kingdom
            else:
                parent_taxid = int(float(parent_taxid)) # Handle potential floats

            taxid = current_taxid
            current_taxid += 1
            
            # --- A. Append to nodes.dmp ---
            # Kraken2 requires taxid, parent_taxid, and rank. The rest are dummy filler fields to match NCBI format.
            node_line = f"{taxid}\t|\t{parent_taxid}\t|\tspecies\t|\t\t|\t0\t|\t0\t|\t1\t|\t0\t|\t1\t|\t0\t|\t0\t|\t0\t|\t\t|\n"
            f_nodes.write(node_line)
            
            # --- B. Append to names.dmp ---
            name_line = f"{taxid}\t|\t{cluster_name}\t|\t\t|\tscientific name\t|\n"
            f_names.write(name_line)
            
            # --- C. Rewrite FASTA ---
            input_path = resolve_genome_path(genome_file_base, GENOME_DIR)
                
            if input_path:
                out_fasta_name = f"{cluster_name}_{taxid}.fna"
                output_path = os.path.join(CUSTOM_LIBRARY_DIR, out_fasta_name)
                rewrite_fasta_for_kraken(input_path, output_path, taxid)
                success_count += 1
            else:
                print(f"   [WARN] Could not find genome file for {cluster_name} using base name: {genome_file_base}")

    print("-" * 50)
    print(f"[DONE] Successfully added {success_count} new species to taxonomy and processed their FASTAs.")
    print(f"[DONE] Processed FASTA files are ready in: {CUSTOM_LIBRARY_DIR}")

if __name__ == "__main__":
    main()
