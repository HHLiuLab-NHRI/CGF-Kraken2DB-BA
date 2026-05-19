#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------
# Paths
# ----------------------------------------
FILELIST="../results/fastani/filelist.txt"
CHUNK_DIR="../results/fastani/chunks"
MATRIX_DIR="../results/fastani/matrix"
LOG_DIR="../results/fastani/logs"

mkdir -p "$MATRIX_DIR" "$LOG_DIR"

echo "[INFO] Using genome list: $FILELIST"
echo "[INFO] Number of genomes: $(wc -l < "$FILELIST")"

# ----------------------------------------
# Parallel settings (optimized for 64 cores / 128 threads)
# ----------------------------------------
THREADS=3
NJOBS=42
echo "[INFO] Parallel: $NJOBS jobs × $THREADS threads = $((NJOBS * THREADS)) threads total"

# ----------------------------------------
# Wait for an available job slot
# ----------------------------------------
wait_for_slot() {
    while true; do
        local running
        running=$(jobs -rp | wc -l)
        if [ "$running" -lt "$NJOBS" ]; then
            break
        fi
        sleep 3
    done
}

# ----------------------------------------
# Grid run
# ----------------------------------------
Q_CHUNKS=("$CHUNK_DIR"/Q_*.list)
R_CHUNKS=("$CHUNK_DIR"/R_*.list)

echo "[INFO] Found ${#Q_CHUNKS[@]} Q-chunks and ${#R_CHUNKS[@]} R-chunks"

for Q in "${Q_CHUNKS[@]}"; do
    QBASE=$(basename "$Q" .list)

    for R in "${R_CHUNKS[@]}"; do
        RBASE=$(basename "$R" .list)

        OUTFILE="$MATRIX_DIR/${QBASE}_${RBASE}.out"
        TMPFILE="$MATRIX_DIR/${QBASE}_${RBASE}.out.tmp.$$"
        LOGFILE="$LOG_DIR/${QBASE}_${RBASE}.log"

        # Skip if final output already exists
        if [[ -f "$OUTFILE" ]]; then
            echo "[SKIP] $QBASE × $RBASE (exists)"
            continue
        fi

        # Clean stale tmp files older than 30 minutes
        find "$MATRIX_DIR" -maxdepth 1 -name "${QBASE}_${RBASE}.out.tmp.*" -mmin +30 -delete 2>/dev/null || true

        # Skip if someone else is writing this file
        if ls "$MATRIX_DIR/${QBASE}_${RBASE}.out.tmp."* >/dev/null 2>&1; then
            echo "[WAIT] temp exists: ${QBASE}_${RBASE}"
            continue
        fi

        wait_for_slot

        echo "[RUN ] $QBASE × $RBASE"
        (
            fastANI \
                --ql "$Q" \
                --rl "$R" \
                --fragLen 3000 \
                --minFraction 0.10 \
                -t "$THREADS" \
                -o "$TMPFILE" \
                >"$LOGFILE" 2>&1

            # Always rename tmp to final, even if empty
            mv "$TMPFILE" "$OUTFILE"

            if [[ ! -s "$OUTFILE" ]]; then
                echo "[NOTE] Empty ANI result (no similarities): ${QBASE}_${RBASE}" >> "$LOGFILE"
                echo "[EMPTY] $QBASE × $RBASE"
            else
                echo "[DONE] $QBASE × $RBASE"
            fi
        ) &
    done
done

wait
echo "[ALL DONE] 2D FastANI grid finished."

