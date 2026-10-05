#!/usr/bin/env bash
set -euo pipefail

SANKEY_DIR="../sankey"
NONENHANCED_DB="${NONENHANCED_KRAKEN_DB:-../../k2_fungi_default/}"
ENHANCED_DB="${ENHANCED_KRAKEN_DB:-../../Kraken2_DB/}"
THREADS="${THREADS:-64}"

command -v kraken2 >/dev/null 2>&1 || { echo "[ERROR] kraken2 not found" >&2; exit 1; }
[[ -d "$NONENHANCED_DB" ]] || { echo "[ERROR] Non-enhanced DB not found: $NONENHANCED_DB" >&2; exit 1; }
[[ -d "$ENHANCED_DB" ]] || { echo "[ERROR] Enhanced DB not found: $ENHANCED_DB" >&2; exit 1; }
mkdir -p "$SANKEY_DIR"

run_pair() {
    local read="$1"
    local input="${SANKEY_DIR}/pooled_${read}.fastq"
    [[ -f "$input" ]] || { echo "[ERROR] Missing pooled input: $input" >&2; exit 1; }

    echo "Running ${read} against locally rebuilt non-enhanced fungal DB..."
    kraken2 --db "$NONENHANCED_DB" \
      --threads "$THREADS" \
      --report "${SANKEY_DIR}/nonenhanced_${read}_report.txt" \
      --output "${SANKEY_DIR}/nonenhanced_${read}.txt" \
      "$input"

    echo "Running ${read} against CGF/PHF-enhanced fungal DB..."
    kraken2 --db "$ENHANCED_DB" \
      --threads "$THREADS" \
      --report "${SANKEY_DIR}/enhanced_${read}_report.txt" \
      --output "${SANKEY_DIR}/enhanced_${read}.txt" \
      "$input"
}

run_pair R1
run_pair R2

echo "Kraken2 Sankey runs complete. Outputs are in ${SANKEY_DIR}/"
