#!/usr/bin/env bash
set -euo pipefail

########################################
# Paths
########################################
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
GENOME_DIR="$SCRIPT_DIR/../CGFNovelResults/genomes"
OUTDIR="$SCRIPT_DIR/../CGFNovelResults/busco_out"
SUMMARY_FILE="$SCRIPT_DIR/../CGFNovelResults/busco_summary.tsv"
TEMP_DIR="$SCRIPT_DIR/../CGFNovelResults/temp_decompressed"

# BUSCO Settings
BUSCO_DB="fungi_odb10"
THREADS=64                   # <--- UPDATED to 64
MODE="genome"

# ---------------------------------------------------------
# FIX: Suppress NumExpr/OpenMP Warnings and Force High Threads
# ---------------------------------------------------------
export NUMEXPR_MAX_THREADS=$THREADS
export OMP_NUM_THREADS=$THREADS

mkdir -p "$OUTDIR" "$TEMP_DIR"

echo "[INFO] Running BUSCO QC on genomes in: $GENOME_DIR"
echo "[INFO] Output directory: $OUTDIR"
echo "[INFO] Threads: $THREADS"

########################################
# Check if input directory exists
########################################
if [[ ! -d "$GENOME_DIR" ]]; then
    echo "[ERROR] Genome directory not found: $GENOME_DIR"
    exit 1
fi

########################################
# Run BUSCO on each genome
########################################
run_busco() {
    local genome_gz="$1"
    local out_dir="$2"
    
    # Extract basename
    local base
    base=$(basename "$genome_gz" .fna.gz)
    
    # Define paths
    local my_out="$out_dir/$base"
    local temp_fasta="$TEMP_DIR/${base}.fna"

    # Skip if done
    if [[ -f "$my_out/short_summary.specific.${BUSCO_DB}.${base}.txt" ]]; then
        echo "[SKIP] $base already processed."
        return
    fi

    # ---------------------------------------------------------
    # Decompress to temp file
    # ---------------------------------------------------------
    echo "[PREP] Decompressing $base..."
    gunzip -c "$genome_gz" > "$temp_fasta"

    echo "[RUN ] BUSCO for $base (Threads: $THREADS)"
    
    # Run BUSCO
    busco \
        -i "$temp_fasta" \
        -o "$base" \
        --out_path "$out_dir" \
        -l "$BUSCO_DB" \
        -m "$MODE" \
        -c "$THREADS" \
        --quiet \
        --force

    # Cleanup temp file
    rm "$temp_fasta"

    if [[ -f "$my_out/short_summary.specific.${BUSCO_DB}.${base}.txt" ]]; then
        echo "[DONE] $base"
    else
        echo "[FAIL] $base (See logs in $my_out)"
    fi
}

export -f run_busco
export BUSCO_DB THREADS MODE TEMP_DIR

########################################
# Execute
########################################
count=$(find "$GENOME_DIR" -name "*.fna.gz" | wc -l)
if [[ "$count" -eq 0 ]]; then
    echo "[ERROR] No .fna.gz files found in $GENOME_DIR"
    exit 1
fi

echo "[INFO] Found $count genomes."

# Sequential loop
for f in "$GENOME_DIR"/*.fna.gz; do
    run_busco "$f" "$OUTDIR"
done

# Cleanup temp dir
rmdir "$TEMP_DIR" 2>/dev/null || true

########################################
# Aggregate Results
########################################
echo "[INFO] Aggregating summaries..."
echo -e "Genome\tComplete\tSingle\tDuplicated\tFragmented\tMissing\tTotal_BUSCOs" > "$SUMMARY_FILE"

for f in "$GENOME_DIR"/*.fna.gz; do
    base=$(basename "$f" .fna.gz)
    summary="$OUTDIR/$base/short_summary.specific.${BUSCO_DB}.${base}.txt"
    
    if [[ -f "$summary" ]]; then
        # Extract C: score string
        score_line=$(grep "C:" "$summary" | head -n 1 | sed 's/^\s*//')
        echo -e "${base}\t${score_line}" >> "$SUMMARY_FILE"
    else
        echo -e "${base}\tNA" >> "$SUMMARY_FILE"
    fi
done

echo "[DONE] Summary saved to $SUMMARY_FILE"
