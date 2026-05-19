#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
CHUNK_DIR="$SCRIPT_DIR/../CGFNovelResults/chunks"
OUTDIR="$SCRIPT_DIR/../CGFNovelResults/fastani_out"
LOGDIR="$SCRIPT_DIR/../CGFNovelResults/logs"

mkdir -p "$OUTDIR" "$LOGDIR"

THREADS=16
JOBS=8  # Parallel jobs

# Collect chunks (used as both Query and Reference)
chunks=( "$CHUNK_DIR"/chunk_*.list )

if [[ ${#chunks[@]} -eq 0 ]]; then
    echo "[ERROR] No chunks found in $CHUNK_DIR"
    exit 1
fi

echo "[INFO] Found ${#chunks[@]} chunks. Starting All-vs-All grid..."

run_one() {
    local q="$1"
    local r="$2"
    local qb=$(basename "$q" .list)
    local rb=$(basename "$r" .list)
    local out="$OUTDIR/${qb}_vs_${rb}.tsv"
    local log="$LOGDIR/${qb}_vs_${rb}.log"

    # Optimization: If qb > rb (lexicographically), we can skip if we assume symmetry, 
    # BUT FastANI is not perfectly symmetric. Safest to run full grid or q >= r.
    # For N=281, full grid is cheap.

    if [[ -s "$out" ]]; then return; fi

    echo "[RUN] $qb vs $rb"
    fastANI --ql "$q" --rl "$r" -t "$THREADS" --fragLen 3000 --minFraction 0.1 -o "$out" >"$log" 2>&1
}

export -f run_one
export OUTDIR LOGDIR THREADS

# Generate grid pairs
parallel -j "$JOBS" --colsep '\t' run_one {1} {2} ::: "${chunks[@]}" ::: "${chunks[@]}"

echo "[DONE] Results in $OUTDIR"
