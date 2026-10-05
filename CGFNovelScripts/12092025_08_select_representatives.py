#!/usr/bin/env python3
import os
import re
import pandas as pd

# Config
CLUSTER_FILE = "../CGFNovelResults/novel_species_clusters.tsv"
BUSCO_DIR = "../CGFNovelResults/busco_out"
OUT_REPS = "../CGFNovelResults/novel_representatives.tsv"


def parse_busco_summary(summary_path):
    """Extract fungal BUSCO complete (C) and fragmented (F) percentages."""
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"BUSCO summary not found: {summary_path}")

    with open(summary_path) as f:
        content = f.read()

    # Example: C:98.5%[S:98.0%,D:0.5%],F:0.5%,M:1.0%
    match = re.search(r'C:(\d+\.?\d*)%.*?F:(\d+\.?\d*)%', content)
    if not match:
        raise ValueError(f"Could not parse BUSCO C/F scores from: {summary_path}")

    return float(match.group(1)), float(match.group(2))


def busco_summary_path(genome):
    base = genome.replace(".fna.gz", "").replace(".fna", "")
    return os.path.join(
        BUSCO_DIR,
        base,
        f"short_summary.specific.fungi_odb10.{base}.txt",
    )


def main():
    df = pd.read_csv(CLUSTER_FILE, sep='\t')

    required = {'novel_species_id', 'genome_filename'}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {CLUSTER_FILE}: {sorted(missing)}")

    rows = []

    # Each ANI-defined cluster receives one deterministic representative:
    # the lexicographically first genome accession/filename in that cluster.
    # BUSCO is used only to assess the quality of that chosen representative;
    # BUSCO scores do not determine representative identity.
    for cluster_id, group in df.groupby('novel_species_id', sort=True):
        members = sorted(group['genome_filename'].astype(str).tolist())
        representative = members[0]

        comp, frag = parse_busco_summary(busco_summary_path(representative))

        rows.append({
            'novel_species_id': cluster_id,
            'genome_filename': representative,
            'representative': representative,
            'cluster_size': len(members),
            'busco_comp': comp,
            'busco_frag': frag,
        })

    reps = pd.DataFrame(rows)
    reps.to_csv(OUT_REPS, sep='\t', index=False)

    print(f"[INFO] ANI clusters: {len(reps)}")
    print("[INFO] Representative rule: lexicographically first genome accession per ANI cluster")
    print("[INFO] BUSCO role: quality control of the selected representative")
    print(f"[INFO] Saved representatives and BUSCO QC scores to {OUT_REPS}")


if __name__ == "__main__":
    main()
