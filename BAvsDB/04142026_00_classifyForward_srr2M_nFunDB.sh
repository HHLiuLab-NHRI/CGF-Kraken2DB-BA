#!/bin/bash

# Set the parent directories
# INPUT: The directory containing numbered folders (1, 2, 3...)
INPUT_PARENT_DIR="../srr2Mreads/"
# OUTPUT: Where R1 results will go
# OUTPUT_PARENT_DIR="../kraken2Output_R1/"
OUTPUT_PARENT_DIR="../kraken2Output_R1_nFunDB/"
# KRAKEN2_DB="$HOME/share/db/kraken2/fungi/"
KRAKEN2_DB="../Kraken2_DB/"

# Create the output parent directory if it doesn't exist
mkdir -p "$OUTPUT_PARENT_DIR"

echo "Starting Kraken2 analysis for FORWARD reads (R1)..."

# Loop through all subdirectories (1, 2, 3, 4, 5) in the input parent directory
for sub_dir in "$INPUT_PARENT_DIR"/*/; do
  # Get the directory name (e.g., "1", "2")
  sub_dir_name=$(basename "$sub_dir")
  
  echo "Processing iteration: $sub_dir_name"
  
  # Create the corresponding subdirectory in the output parent directory
  output_sub_dir="$OUTPUT_PARENT_DIR/$sub_dir_name"
  mkdir -p "$output_sub_dir"
  
  # Loop specifically through *_1.fastq.gz files (Forward reads)
  for fastq_file in "$sub_dir"/*_1.fastq.gz; do
    # Check if file exists to avoid errors if folder is empty
    [ -e "$fastq_file" ] || continue

    # Get the base name (e.g., SRR35008927_1.fastq.gz)
    base_name=$(basename "$fastq_file")
    
    # Set the output file name (e.g., SRR35008927_1.fastq.gz.k2)
    output_file="$output_sub_dir/${base_name}.k2"
    report_file="$output_sub_dir/${base_name}.report"
    
    # Run Kraken2
    # Added --gzip-compressed explicitly since inputs are .gz
    kraken2 --db "$KRAKEN2_DB" "$fastq_file" --gzip-compressed \
            --output "$output_file" --report "$report_file" \
            --threads 64 --use-names
  done
done

echo "Forward read classification complete."
