#!/bin/bash

# --- CONFIGURATION ---
INPUT_DIR="../sra"
OUTPUT_BASE="../srr2Mreads"
BASE_SEED=42
LOG_FILE="subsample_process.log"

# TARGET READS (2 Million)
TARGET_READS=2000000
# TARGET LINES = Reads * 4
TARGET_LINES_MAX=$((TARGET_READS * 4))

# PARALLEL SETTINGS
MAX_JOBS=4
PIGZ_THREADS=8 

# ---------------------

# 1. SETUP LOGGING
# Redirect all stdout (1) and stderr (2) to a pipe that feeds 'tee'.
# 'tee -a' appends to the file and writes to the screen simultaneously.
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================================"
echo "Run started at: $(date)"
echo "Config: Max Jobs=$MAX_JOBS, Threads/Job=$PIGZ_THREADS"
echo "Logging to: $LOG_FILE"
echo "========================================================"

if ! command -v pigz &> /dev/null; then echo "Error: pigz not found."; exit 1; fi

process_sample() {
    local r1_file="$1"
    
    local filename=$(basename "$r1_file")
    local sample_name="${filename%_1.fastq.gz}"
    local r2_file="$INPUT_DIR/${sample_name}_2.fastq.gz"

    # Timestamp for the logs
    local ts=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts] >> [Analysis Started] $sample_name"

    # 2. Determine Expected Output Size
    # We count lines in the SOURCE file first to handle small samples correctly.
    local source_lines=$(pigz -dc -p 4 "$r1_file" | wc -l)
    source_lines=$(echo $source_lines | xargs) # trim whitespace

    local expected_lines=$TARGET_LINES_MAX
    
    if [ "$source_lines" -lt "$TARGET_LINES_MAX" ]; then
        echo "[$ts]    [Info] $sample_name is small ($((source_lines/4)) reads). Will output all reads."
        expected_lines=$source_lines
    fi

    for i in {1..5}; do
        mkdir -p "$OUTPUT_BASE/$i"

        local current_seed=$((BASE_SEED + i))
        local out1="$OUTPUT_BASE/$i/${sample_name}_1.fastq.gz"
        local out2="$OUTPUT_BASE/$i/${sample_name}_2.fastq.gz"
        
        # 3. Verification Step
        local skip=0
        if [ -f "$out1" ]; then
            local existing_lines=$(pigz -dc -p 2 "$out1" | wc -l)
            existing_lines=$(echo $existing_lines | xargs)

            if [ "$existing_lines" -eq "$expected_lines" ]; then
                skip=1
            else
                local ts_now=$(date '+%H:%M:%S')
                echo "[$ts_now]    [Redo] $sample_name Rep $i incomplete ($existing_lines lines). Re-running..."
            fi
        fi

        # 4. Execution Step
        if [ "$skip" -eq 0 ]; then
             seqtk sample -s $current_seed "$r1_file" $TARGET_READS | pigz -p $PIGZ_THREADS > "$out1" &
             seqtk sample -s $current_seed "$r2_file" $TARGET_READS | pigz -p $PIGZ_THREADS > "$out2" &
             wait 
             local ts_done=$(date '+%H:%M:%S')
             echo "[$ts_done]    [Done] $sample_name Rep $i generated."
        else
             local ts_skip=$(date '+%H:%M:%S')
             echo "[$ts_skip]    [Skip] $sample_name Rep $i is valid."
        fi
    done
    
    local ts_end=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$ts_end] << [Job Finished] $sample_name"
}

# Array to store worker PIDs
pids=()

# Main Loop
counter=0
for r1_file in "$INPUT_DIR"/*_1.fastq.gz; do
    
    while [ $(jobs -r | wc -l) -ge $MAX_JOBS ]; do
        sleep 1
    done

    # Run background job
    process_sample "$r1_file" &
    
    # Capture the PID of the job we just launched
    pids+=($!)
    
    ((counter++))
done

# --- FIXED WAIT COMMAND ---
# Instead of 'wait' (which waits for everything including tee),
# we wait explicitly for the worker PIDs.
wait "${pids[@]}"

echo "========================================================"
echo "All processing complete at: $(date)"
echo "========================================================"
