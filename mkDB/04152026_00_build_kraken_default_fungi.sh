#!/bin/bash
# Ref: /mnt/labData/2024/prKraken2Classify_2M_1/working/07112024-setup.py
## Warning: the above script not working any more after 2026

# ==============================================================================
# Fail-safe settings
# ==============================================================================
set -euo pipefail

# Configuration variables
DBNAME="../k2_fungi_default"
LOCAL_TAXDUMP_DIR="../refCalibrationResults/taxdump"
THREADS=16

# Progress reporting function
log_progress() {
    echo -e "\n[$(date +'%Y-%m-%d %H:%M:%S')] === $1 ==="
}

# Error handling trap
trap 'echo -e "\n[$(date +'\''%Y-%m-%d %H:%M:%S'\'')] ❌ ERROR: Script failed at line $LINENO. Exiting." >&2' ERR

log_progress "Starting Kraken2 Fungi Database Build"
log_progress "Target Database Directory: $DBNAME"
log_progress "Allocated Threads: $THREADS"

# Pre-flight check
if ! command -v kraken2-build &> /dev/null; then
    echo -e "\n[$(date +'%Y-%m-%d %H:%M:%S')] ❌ ERROR: kraken2-build could not be found."
    exit 1
fi

# Step 1: Taxonomy (Using Local Files First)
if [ -f "$DBNAME/.taxonomy_success" ]; then
    log_progress "Step 1/4: Taxonomy already processed successfully. Skipping..."
else
    log_progress "Step 1/4: Preparing NCBI taxonomy..."
    
    # Ensure the taxonomy directory exists
    mkdir -p "$DBNAME/taxonomy"
    
    if [ -f "$LOCAL_TAXDUMP_DIR/nodes.dmp" ] && [ -f "$LOCAL_TAXDUMP_DIR/names.dmp" ]; then
        log_progress "Found existing nodes.dmp and names.dmp in $LOCAL_TAXDUMP_DIR. Copying locally..."
        cp "$LOCAL_TAXDUMP_DIR/nodes.dmp" "$DBNAME/taxonomy/"
        cp "$LOCAL_TAXDUMP_DIR/names.dmp" "$DBNAME/taxonomy/"
        touch "$DBNAME/.taxonomy_success"
        
    elif [ -f "$LOCAL_TAXDUMP_DIR/taxdump.tar.gz" ]; then
        log_progress "Found taxdump.tar.gz in $LOCAL_TAXDUMP_DIR. Extracting locally..."
        tar -xzf "$LOCAL_TAXDUMP_DIR/taxdump.tar.gz" -C "$DBNAME/taxonomy/" nodes.dmp names.dmp
        touch "$DBNAME/.taxonomy_success"
        
    else
        log_progress "No local taxonomy files found. Downloading NCBI taxonomy via FTP..."
        log_progress "⚠️ Using --skip-maps to bypass massive, unnecessary accession maps."
        kraken2-build --download-taxonomy --skip-maps --use-ftp --db "$DBNAME"
        touch "$DBNAME/.taxonomy_success"
    fi
fi

# Step 2: Fungi Library
if [ -f "$DBNAME/.library_success" ]; then
    log_progress "Step 2/4: Fungi library already downloaded successfully. Skipping..."
else
    log_progress "Step 2/4: Downloading the latest RefSeq fungi library..."
    kraken2-build --download-library fungi --use-ftp --db "$DBNAME"
    touch "$DBNAME/.library_success"
fi

# Step 3: Hash Table Build
if [ -f "$DBNAME/.build_success" ]; then
    log_progress "Step 3/4: Hash table already built successfully. Skipping..."
else
    log_progress "Step 3/4: Building the k-mer hash table..."
    kraken2-build --build --threads "$THREADS" --db "$DBNAME"
    touch "$DBNAME/.build_success"
fi

# Step 4: Cleanup
if [ -f "$DBNAME/.cleanup_success" ]; then
    log_progress "Step 4/4: Cleanup already performed. Skipping..."
else
    log_progress "Step 4/4: Cleaning up intermediate FASTA files to save disk space..."
    kraken2-build --clean --db "$DBNAME"
    touch "$DBNAME/.cleanup_success"
fi

log_progress "✅ SUCCESS: Kraken2 fungi database '$DBNAME' has been successfully built!"
