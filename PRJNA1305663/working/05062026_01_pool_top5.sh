#!/usr/bin/env bash
set -euo pipefail

SEED=100
READ_COUNT=2000000
SRA_DIR="../sra"
OUT_DIR="../sankey"
R1_LIST="${OUT_DIR}/top5_penicillium_R1.csv"
R2_LIST="${OUT_DIR}/top5_penicillium_R2.csv"

command -v seqtk >/dev/null 2>&1 || { echo "[ERROR] seqtk not found" >&2; exit 1; }
mkdir -p "$OUT_DIR"

pool_read() {
    local label="$1"
    local list_file="$2"
    local output_file="$3"

    [[ -f "$list_file" ]] || { echo "[ERROR] Missing $list_file. Run 05062026_00_find_top_penicillium.py first." >&2; exit 1; }
    mapfile -t ids < <(tail -n +2 "$list_file" | cut -d',' -f1 | sed '/^$/d')
    [[ ${#ids[@]} -eq 5 ]] || { echo "[ERROR] Expected 5 samples in $list_file; found ${#ids[@]}" >&2; exit 1; }

    : > "$output_file"
    echo "Pooling $label from samples selected in $list_file"
    for id in "${ids[@]}"; do
        fq="${SRA_DIR}/${id}.fastq.gz"
        [[ -f "$fq" ]] || { echo "[ERROR] Missing $fq" >&2; exit 1; }
        echo "  Subsampling ${READ_COUNT} reads from ${id}.fastq.gz"
        seqtk sample -s"$SEED" "$fq" "$READ_COUNT" >> "$output_file"
    done
}

pool_read "R1" "$R1_LIST" "${OUT_DIR}/pooled_R1.fastq"
pool_read "R2" "$R2_LIST" "${OUT_DIR}/pooled_R2.fastq"

echo "Done. Pooled files:"
echo "  ${OUT_DIR}/pooled_R1.fastq"
echo "  ${OUT_DIR}/pooled_R2.fastq"
