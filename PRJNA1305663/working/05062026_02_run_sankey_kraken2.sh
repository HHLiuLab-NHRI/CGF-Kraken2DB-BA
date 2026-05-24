#!/bin/bash

# Define directories and databases based on your uploaded scripts
SANKEY_DIR="../sankey"
DE_FUN_DB="../../k2_fungi_default/"
N_FUN_DB="../../Kraken2_DB/"
THREADS=64  # Adjust based on your server capacity

echo "Starting Kraken2 Sankey runs..."

# ------------------------------------------------------------------
# READ 1 RUNS
# ------------------------------------------------------------------
echo "Running Read 1 against Default Fungi DB..."
kraken2 --db "$DE_FUN_DB" \
  --threads $THREADS \
  --report "${SANKEY_DIR}/default_R1_report.txt" \
  --output "${SANKEY_DIR}/default_R1.txt" \
  "${SANKEY_DIR}/pooled_R1.fastq"

echo "Running Read 1 against Enhanced Fungi DB..."
kraken2 --db "$N_FUN_DB" \
  --threads $THREADS \
  --report "${SANKEY_DIR}/enhanced_R1_report.txt" \
  --output "${SANKEY_DIR}/enhanced_R1.txt" \
  "${SANKEY_DIR}/pooled_R1.fastq"

# ------------------------------------------------------------------
# READ 2 RUNS
# ------------------------------------------------------------------
echo "Running Read 2 against Default Fungi DB..."
kraken2 --db "$DE_FUN_DB" \
  --threads $THREADS \
  --report "${SANKEY_DIR}/default_R2_report.txt" \
  --output "${SANKEY_DIR}/default_R2.txt" \
  "${SANKEY_DIR}/pooled_R2.fastq"

echo "Running Read 2 against Enhanced Fungi DB..."
kraken2 --db "$N_FUN_DB" \
  --threads $THREADS \
  --report "${SANKEY_DIR}/enhanced_R2_report.txt" \
  --output "${SANKEY_DIR}/enhanced_R2.txt" \
  "${SANKEY_DIR}/pooled_R2.fastq"

echo "Kraken2 runs complete! All outputs are in ${SANKEY_DIR}/"
