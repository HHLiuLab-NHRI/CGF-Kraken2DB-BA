#!/usr/bin/env python3
import pandas as pd
import subprocess
import os
import sys
import gzip
import shutil

# ================= CONFIGURATION =================
# Input/Output
INPUT_TSV = "../CGFNovelResults/novel_representatives.tsv"
OUTPUT_TSV = "../CGFNovelResults/final_validated_representatives.tsv"
GENOME_DIR = "../CGFNovelResults/genomes"
BUSCO_OUT_DIR = "../CGFNovelResults/busco_out_microsporidia"
LOG_FILE = "filtering_log.txt"

# Thresholds
MIN_FUNGI_SCORE = 50.0        
MIN_MICROSPORIDIA_SCORE = 65.0 
THREADS = 64

# [FIX] Force NumExpr/OpenMP to use 64 threads to avoid bottlenecks/warnings
os.environ["NUMEXPR_MAX_THREADS"] = str(THREADS)
os.environ["OMP_NUM_THREADS"] = str(THREADS)
os.environ["MKL_NUM_THREADS"] = str(THREADS)
# =================================================

def resolve_genome_path(filename, search_dir):
    """
    Tries to find the genome file, handling potential .gz mismatch.
    """
    path = os.path.join(search_dir, filename)
    if os.path.exists(path):
        return path
    
    if filename.endswith(".gz"):
        unpacked_name = filename[:-3] 
        path = os.path.join(search_dir, unpacked_name)
        if os.path.exists(path):
            return path
            
    path = os.path.join(search_dir, filename + ".gz")
    if os.path.exists(path):
        return path

    return None

def run_busco_microsporidia(genome_path, genome_name):
    """Runs BUSCO with microsporidia_odb10 lineage, handling .gz automatically."""
    print(f"   [RESCUE] Running Microsporidia check on {genome_name}...")
    
    if not os.path.exists(BUSCO_OUT_DIR):
        os.makedirs(BUSCO_OUT_DIR)
        
    # ---------------------------------------------------------
    # FIX: Handle .gz decompression internally
    # ---------------------------------------------------------
    run_path = genome_path
    temp_file = None
    
    try:
        if genome_path.endswith(".gz"):
            # Create a temp file path
            temp_dir = os.path.join(BUSCO_OUT_DIR, "temp_decompressed")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Remove .gz from filename for the temp file
            base_clean = os.path.basename(genome_path).replace(".gz", "")
            temp_file = os.path.join(temp_dir, base_clean)
            
            print(f"   [PREP] Decompressing to temporary file: {temp_file}")
            
            # Decompress
            with gzip.open(genome_path, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            run_path = temp_file

        # ---------------------------------------------------------
        # Run BUSCO on the (potentially decompressed) file
        # ---------------------------------------------------------
        cmd = [
            "busco",
            "-i", run_path,
            "-l", "microsporidia_odb10",
            "-o", genome_name,
            "--out_path", BUSCO_OUT_DIR,
            "-m", "genome",
            "-c", str(THREADS),
            "--quiet",
            "--force"
        ]
        
        subprocess.run(cmd, check=True)
        
        # Parse Results
        res_dir = os.path.join(BUSCO_OUT_DIR, genome_name)
        summary_file = None
        
        if os.path.exists(res_dir):
            for f in os.listdir(res_dir):
                if f.startswith("short_summary.specific.microsporidia_odb10"):
                    summary_file = os.path.join(res_dir, f)
                    break
        
        if not summary_file or not os.path.exists(summary_file):
            print(f"   [WARNING] BUSCO finished but summary file not found in {res_dir}")
            return 0.0
            
        with open(summary_file, 'r') as f:
            for line in f:
                if "C:" in line and "%" in line:
                    score_str = line.split("C:")[1].split("%")[0]
                    return float(score_str)
        return 0.0

    except subprocess.CalledProcessError:
        print(f"   [ERROR] BUSCO failed for {genome_name}")
        return 0.0
    except Exception as e:
        print(f"   [ERROR] Unexpected error: {e}")
        return 0.0
    finally:
        # ---------------------------------------------------------
        # Cleanup: Remove the temp file if we created one
        # ---------------------------------------------------------
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

def main():
    print(f"--- Starting QC Pipeline (Threads: {THREADS}) ---")
    
    try:
        df = pd.read_csv(INPUT_TSV, sep='\t')
    except Exception as e:
        print(f"Error reading {INPUT_TSV}: {e}")
        sys.exit(1)

    required_cols = ['representative', 'busco_comp']
    if not all(col in df.columns for col in required_cols):
        print(f"Error: Input file must contain columns: {required_cols}")
        sys.exit(1)
        
    print(f"Loaded {len(df)} candidates from {INPUT_TSV}")
    
    final_rows = []
    
    with open(LOG_FILE, "w") as log:
        log.write("Validation Log\n")
    
    for index, row in df.iterrows():
        raw_filename = row['representative']
        genome_path = resolve_genome_path(raw_filename, GENOME_DIR)
        
        if not genome_path:
            print(f"[MISSING] Could not find file for {raw_filename}")
            continue

        genome_name = os.path.basename(genome_path)
        fungi_score = float(row['busco_comp'])
        
        if fungi_score >= MIN_FUNGI_SCORE:
            row['Final_Type'] = 'Fungi'
            row['Final_Score'] = fungi_score
            row['Status'] = 'Keep'
            row['Real_Path'] = genome_path 
            final_rows.append(row)
        else:
            print(f"[LOW SCORE] {genome_name} is {fungi_score}%. Checking Microsporidia...")
            micro_score = run_busco_microsporidia(genome_path, genome_name)
            
            if micro_score >= MIN_MICROSPORIDIA_SCORE:
                print(f"   -> RESCUED! Microsporidia Score: {micro_score}%")
                row['Final_Type'] = 'Microsporidia'
                row['Final_Score'] = micro_score
                row['Status'] = 'Keep'
                row['Real_Path'] = genome_path
                final_rows.append(row)
            else:
                print(f"   -> DISCARD. Score: {micro_score}%")
                with open(LOG_FILE, "a") as log:
                    log.write(f"DISCARDED: {genome_name}\n")

    final_df = pd.DataFrame(final_rows)
    final_df.to_csv(OUTPUT_TSV, sep='\t', index=False)
    
    print("\n" + "="*40)
    print(f"Pipeline Complete. Saved to: {OUTPUT_TSV}")

if __name__ == "__main__":
    main()
