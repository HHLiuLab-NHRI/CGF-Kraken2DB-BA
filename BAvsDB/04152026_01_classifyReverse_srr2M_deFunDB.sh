#!/bin/bash

# Set the parent directories
INPUT_PARENT_DIR="../srr2Mreads/"
# OUTPUT: Where R2 results will go (Separate directory)
# OUTPUT_PARENT_DIR="../kraken2Output_R2/"
OUTPUT_PARENT_DIR="../kraken2Output_R2_deFunDB/"
# KRAKEN2_DB="$HOME/share/db/kraken2/fungi/"
KRAKEN2_DB="../k2_fungi_default/"

mkdir -p "$OUTPUT_PARENT_DIR"

echo "Starting Kraken2 analysis for REVERSE reads (R2)..."

for sub_dir in "$INPUT_PARENT_DIR"/*/; do
  sub_dir_name=$(basename "$sub_dir")
  
  echo "Processing iteration: $sub_dir_name"
  
  output_sub_dir="$OUTPUT_PARENT_DIR/$sub_dir_name"
  mkdir -p "$output_sub_dir"
  
  # Loop specifically through *_2.fastq.gz files (Reverse reads)
  for fastq_file in "$sub_dir"/*_2.fastq.gz; do
    [ -e "$fastq_file" ] || continue

    base_name=$(basename "$fastq_file")
    
    output_file="$output_sub_dir/${base_name}.k2"
    report_file="$output_sub_dir/${base_name}.report"
    
    kraken2 --db "$KRAKEN2_DB" "$fastq_file" --gzip-compressed \
            --output "$output_file" --report "$report_file" \
            --threads 64 --use-names
  done
done

echo "Reverse read classification complete."
