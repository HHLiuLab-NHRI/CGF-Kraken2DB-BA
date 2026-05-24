#!/usr/bin/env bash
set -Eeuo pipefail

THREADS=64
SRA_DIR="../sra"
SRR_LIST="../meta/srr_list.txt"

mkdir -p "$SRA_DIR"

command -v fasterq-dump >/dev/null 2>&1 || {
    echo "Error: fasterq-dump not found in PATH." >&2
    exit 1
}

command -v pigz >/dev/null 2>&1 || {
    echo "Error: pigz not found in PATH." >&2
    exit 1
}

command -v cmp >/dev/null 2>&1 || {
    echo "Error: cmp not found in PATH." >&2
    exit 1
}

compress_and_verify() {
    local fastq="$1"
    local gz="${fastq}.gz"
    local tmp_gz="${gz}.part"

    if [[ ! -f "$fastq" ]]; then
        echo "Error: expected FASTQ file not found: $fastq" >&2
        return 1
    fi

    rm -f -- "$tmp_gz"

    echo "Compressing: $fastq"
    pigz -p "$THREADS" -c -- "$fastq" > "$tmp_gz"

    echo "Testing gzip integrity: $tmp_gz"
    pigz -t -- "$tmp_gz"

    echo "Comparing decompressed content with original: $fastq"
    pigz -dc -- "$tmp_gz" | cmp -s -- "$fastq" -

    mv -- "$tmp_gz" "$gz"
    echo "Verified compressed file: $gz"
}

while IFS= read -r SRR || [[ -n "$SRR" ]]; do
    # Skip blank lines.
    [[ -z "$SRR" ]] && continue

    TMP_DIR="${SRA_DIR}/tmp_${SRR}"
    FASTQ_1="${SRA_DIR}/${SRR}_1.fastq"
    FASTQ_2="${SRA_DIR}/${SRR}_2.fastq"

    echo "========================================"
    echo "Downloading: $SRR"

    rm -rf -- "$TMP_DIR"

    if ! fasterq-dump "$SRR" \
        --outdir "$SRA_DIR" \
        --split-files \
        --threads "$THREADS" \
        --temp "$TMP_DIR" \
        --skip-technical \
        --progress; then

        echo "Error: fasterq-dump failed for $SRR" >&2
        rm -rf -- "$TMP_DIR"
        exit 1
    fi

    # Remove the fasterq-dump temporary directory after downloading.
    rm -rf -- "$TMP_DIR"
    echo "Removed temporary directory: $TMP_DIR"

    # Compress and verify both paired-end FASTQ files.
    # Originals are retained until both compressed files are successfully verified.
    if compress_and_verify "$FASTQ_1" && compress_and_verify "$FASTQ_2"; then
        rm -f -- "$FASTQ_1" "$FASTQ_2"
        echo "Removed verified original FASTQ files for: $SRR"
    else
        echo "Error: compression or verification failed for $SRR" >&2
        echo "Original FASTQ files were retained." >&2
        exit 1
    fi

    echo "Completed: $SRR"
done < "$SRR_LIST"

echo "========================================"
echo "All downloads were compressed and verified successfully."
