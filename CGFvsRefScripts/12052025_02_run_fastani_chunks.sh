#!/usr/bin/env bash
set -euo pipefail

########################################
# Paths (relative to this script)
########################################
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

CHUNK_DIR="$SCRIPT_DIR/../CGFvsRefResults/chunks"
OUTDIR="$SCRIPT_DIR/../CGFvsRefResults/fastani_out"
LOGDIR="$SCRIPT_DIR/../CGFvsRefResults/logs"

mkdir -p "$OUTDIR" "$LOGDIR"

########################################
# Parallel settings
########################################
THREADS=16      # threads per fastANI job
JOBS=8          # concurrent jobs (16 x 8 = 128 cores on your EPYC)

echo "[INFO] Using chunks in: $CHUNK_DIR"

########################################
# Collect query and ref chunk lists
########################################
queries=( "$CHUNK_DIR"/Q_*.list )
refs=( "$CHUNK_DIR"/R_*.list )

# Validate queries
if [[ ${#queries[@]} -eq 0 || ! -f "${queries[0]}" ]]; then
    echo "[ERROR] No Q_*.list files found in $CHUNK_DIR"
    exit 1
fi

# Validate refs
if [[ ${#refs[@]} -eq 0 || ! -f "${refs[0]}" ]]; then
    echo "[ERROR] No R_*.list files found in $CHUNK_DIR"
    echo "        Did 01_split_filelists.py create R_*.list into a different directory?"
    exit 1
fi

echo "[INFO] Num query chunks: ${#queries[@]}"
echo "[INFO] Num reference chunks: ${#refs[@]}"
total_jobs=$(( ${#queries[@]} * ${#refs[@]} ))
echo "[INFO] Total jobs (Q×R): $total_jobs"
echo "[INFO] Parallel: $JOBS jobs × $THREADS threads/job"

########################################
# Worker function
########################################
run_one() {
    local q="$1"
    local r="$2"

    local qb rb out log
    qb=$(basename "$q" .list)
    rb=$(basename "$r" .list)

    out="$OUTDIR/${qb}__${rb}.tsv"
    log="$LOGDIR/${qb}__${rb}.log"

    # Resume-safe: skip if already done and non-empty
    if [[ -s "$out" ]]; then
        echo "[SKIP] $qb × $rb (exists)"
        return
    fi

    echo "[RUN ] $qb × $rb"

    fastANI \
        --ql "$q" \
        --rl "$r" \
        --threads "$THREADS" \
        --fragLen 3000 \
        --minFraction 0.1 \
        --output "$out" \
        >"$log" 2>&1

    if [[ ! -s "$out" ]]; then
        echo "[WARN] Empty result for $qb × $rb (see $log)"
    else
        echo "[DONE] $qb × $rb"
    fi
}

export -f run_one
export OUTDIR LOGDIR THREADS

########################################
# Launch grid of (Q,R) jobs via GNU parallel
########################################
echo "[INFO] Starting CGF×RefSeq FastANI job..."

# Generate all Q,R pairs and feed to parallel
{
    for q in "${queries[@]}"; do
        for r in "${refs[@]}"; do
            printf "%s\t%s\n" "$q" "$r"
        done
    done
} | parallel -j "$JOBS" --colsep '\t' run_one {1} {2}

echo "[ALL DONE] CGF×RefSeq FastANI jobs completed."
echo "[INFO] Results: $OUTDIR"
echo "[INFO] Logs:    $LOGDIR"

