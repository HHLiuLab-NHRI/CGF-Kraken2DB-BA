#! /usr/bin/bash
while read SRR; do
    echo "Downloading $SRR"
    fasterq-dump "$SRR" \
        --outdir ../sra \
        --split-files \
        --threads 16 \
        --temp ../sra/tmp_$SRR \
        --skip-technical \
        --progress
done < ../meta/srr_list.txt

