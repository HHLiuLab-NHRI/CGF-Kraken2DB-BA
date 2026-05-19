#! /bin/bash

# Configuration
SEED=100
READ_COUNT=2000000
SRA_DIR="../sra"
OUT_DIR="../sankey"

# Ensure the output directory exists
mkdir -p "$OUT_DIR"

# -------------------------------
# READ 1 PROCESSING
# -------------------------------
echo "Starting Read 1 pooling..."
> "${OUT_DIR}/pooled_R1.fastq" # Initialize/clear the output file

for ID in SRR35008939_1 SRR35009027_1 SRR35008943_1 SRR35008946_1 SRR35008968_1; do
    echo "  Subsampling 2M reads from ${ID}.fastq.gz..."
    # seqtk outputs directly to stdout, so we append (>>) to our pooled file
    seqtk sample -s$SEED "${SRA_DIR}/${ID}.fastq.gz" $READ_COUNT >> "${OUT_DIR}/pooled_R1.fastq"
done

# -------------------------------
# READ 2 PROCESSING
# -------------------------------
echo -e "\nStarting Read 2 pooling..."
> "${OUT_DIR}/pooled_R2.fastq" # Initialize/clear the output file

for ID in SRR35008939_2 SRR35009027_2 SRR35008943_2 SRR35008946_2 SRR35008968_2; do
    echo "  Subsampling 2M reads from ${ID}.fastq.gz..."
    seqtk sample -s$SEED "${SRA_DIR}/${ID}.fastq.gz" $READ_COUNT >> "${OUT_DIR}/pooled_R2.fastq"
done

echo -e "\nDone! Your 10-million read pooled files are ready at:"
echo "  ${OUT_DIR}/pooled_R1.fastq"
echo "  ${OUT_DIR}/pooled_R2.fastq"
