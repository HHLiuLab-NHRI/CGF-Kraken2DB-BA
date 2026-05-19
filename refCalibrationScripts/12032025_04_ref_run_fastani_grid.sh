#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------
# Paths
# ----------------------------------------
FILELIST="../refCalibrationResults/fastani/filelist_refseq.txt"
CHUNK_DIR="../refCalibrationResults/fastani/chunks"
MATRIX_DIR="../refCalibrationResults/fastani/matrix"
LOG_DIR="../refCalibrationResults/fastani/logs"

mkdir -p "$MATRIX_DIR" "$LOG_DIR"

echo "[INFO] Using genome list: $FILELIST"
echo "[INFO] Number of genomes: $(wc -l < "$FILELIST")"

# ----------------------------------------
# Parallel settings (tuned for 64 cores / 128 threads)
# ----------------------------------------
THREADS=4      # fastANI threads per job
NJOBS=32       # number of concurrent jobs
echo "[INFO] Parallel: $NJOBS jobs × $THREADS threads = $((NJOBS * THREADS)) threads total"

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

        if [[ -f "$OUTFILE" ]]; then
            echo "[SKIP] $QBASE × $RBASE (exists)"
            continue
        fi

        # Clean stale tmp
        find "$MATRIX_DIR" -maxdepth 1 -name "${QBASE}_${RBASE}.out.tmp.*" -mmin +30 -delete 2>/dev/null || true

        # If some tmp is being written, skip for now
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

            mv "$TMPFILE" "$OUTFILE"

            if [[ ! -s "$OUTFILE" ]]; then
                echo "[NOTE] Empty ANI result (no similarities): ${QBASE}_${RBASE}" >> "$LOGFILE"
                echo "[EMPTY] $QBASE × $RBASE"
            else
                echo "[DONE]  $QBASE × $RBASE"
            fi
        ) &
    done
done

wait
echo "[ALL DONE] RefSeq 2D FastANI grid finished."

