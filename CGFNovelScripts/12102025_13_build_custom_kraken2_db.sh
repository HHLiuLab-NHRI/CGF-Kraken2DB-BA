#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================
DB_NAME="../Kraken2_DB"
THREADS=128

echo "====================================================================="
echo " Starting Custom Kraken 2 Fungal Database Build (OFFLINE MODE)"
echo " Database path: $DB_NAME"
echo " Threads: $THREADS"
echo "====================================================================="

# ==============================================================================
# STEP 1: Add ALL Formatted Genomes (Novel + RefSeq) to the Library
# ==============================================================================
echo ""
echo "[INFO] STEP 1: Adding formatted FASTAs to the Kraken 2 library..."
echo "       (This includes your novel CGFs and your local RefSeq genomes)"

count=0
for fasta_file in "$DB_NAME"/library/added/*.fna; do
    if [[ -f "$fasta_file" ]]; then
        kraken2-build --add-to-library "$fasta_file" --db "$DB_NAME" > /dev/null
        count=$((count + 1))
    fi
done

if [[ "$count" -eq 0 ]]; then
    echo "[ERROR] No .fna files found in $DB_NAME/library/added to add."
    exit 1
else
    echo "[INFO] Successfully added $count genomes to the library."
fi

# ==============================================================================
# STEP 2: Build the Database
# ==============================================================================
echo ""
echo "[INFO] STEP 2: Building the Kraken 2 Database..."
echo "       (This will use all $THREADS threads and heavily utilize RAM)"
kraken2-build --build --db "$DB_NAME" --threads "$THREADS"

echo ""
echo "====================================================================="
echo " [SUCCESS] Custom Kraken 2 database is built and ready for use!"
echo "====================================================================="
