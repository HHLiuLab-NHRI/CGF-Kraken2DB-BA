#!/usr/bin/env python3
import os
import pandas as pd
import glob
import re

# Config
CLUSTER_FILE = "../CGFNovelResults/novel_species_clusters.tsv"
BUSCO_DIR = "../CGFNovelResults/busco_out"
OUT_REPS = "../CGFNovelResults/novel_representatives.tsv"

def parse_busco_summary(summary_path):
    """Extracts C (Complete) and F (Fragmented) scores."""
    if not os.path.exists(summary_path): return 0.0, 100.0
    with open(summary_path) as f:
        content = f.read()
        # Regex for: C:98.5%[S:98.0%,D:0.5%],F:0.5%,M:1.0%
        match = re.search(r'C:(\d+\.?\d*)%.*?F:(\d+\.?\d*)%', content)
        if match:
            return float(match.group(1)), float(match.group(2))
    return 0.0, 100.0

def main():
    # 1. Load Clusters
    df_clusters = pd.read_csv(CLUSTER_FILE, sep='\t')
    
    # 2. Score every genome
    scores = []
    for genome in df_clusters['genome_filename']:
        # BUSCO output dir usually matches the genome basename (minus extension)
        base = genome.replace(".fna.gz", "").replace(".fna", "")
        summary_path = os.path.join(BUSCO_DIR, base, f"short_summary.specific.fungi_odb10.{base}.txt")
        
        comp, frag = parse_busco_summary(summary_path)
        scores.append({'genome_filename': genome, 'busco_comp': comp, 'busco_frag': frag})
    
    df_scores = pd.DataFrame(scores)
    df_merged = pd.merge(df_clusters, df_scores, on='genome_filename')

    # 3. Select Best per Cluster
    # Logic: Sort by Completeness (Desc), then Fragmentation (Asc)
    best_reps = df_merged.sort_values(
        ['novel_species_id', 'busco_comp', 'busco_frag'], 
        ascending=[True, False, True]
    ).drop_duplicates('novel_species_id', keep='first')

    best_reps.to_csv(OUT_REPS, sep='\t', index=False)
    print(f"[INFO] Selected {len(best_reps)} representatives. Saved to {OUT_REPS}")

if __name__ == "__main__":
    main()
