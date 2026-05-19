#! /usr/bin/bash

mkdir -p ../data/refseq_fungi

awk '!/^#/ {print $1}' ../meta/fungi_all/assembly_summary_fungi_refseq.txt \
| while read acc; do
    ln ../data/fungi_all/${acc}.fna.gz ../data/refseq_fungi/ 2>/dev/null
done

