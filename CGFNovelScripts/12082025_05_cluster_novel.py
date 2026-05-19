#!/usr/bin/env python3
import networkx as nx
import pandas as pd
import os
import sys

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
EDGE_FILE = "../CGFNovelResults/novel_graph_edges.tsv"
FILELIST  = "../CGFNovelResults/filelist_novel.txt"
OUT_CLUSTERS = "../CGFNovelResults/novel_species_clusters.tsv"

def main():
    print("[INFO] Building Graph...")
    G = nx.Graph()

    # 1. Add ALL novel nodes (even singletons)
    # We need the full list of 281 genomes to ensure singletons aren't lost
    with open(FILELIST) as f:
        all_genomes = [os.path.basename(x.strip()) for x in f if x.strip()]
    
    G.add_nodes_from(all_genomes)
    print(f"[INFO] Added {G.number_of_nodes()} nodes (genomes).")

    # 2. Add edges (ANI >= 95%)
    if os.path.exists(EDGE_FILE) and os.path.getsize(EDGE_FILE) > 0:
        df_edges = pd.read_csv(EDGE_FILE, sep='\t')
        for _, row in df_edges.iterrows():
            G.add_edge(row['node1'], row['node2'], weight=row['ani'])
    else:
        print("[INFO] No edges file found or empty. All genomes will be singletons.")

    print(f"[INFO] Added {G.number_of_edges()} edges.")

    # 3. Find Connected Components
    comps = list(nx.connected_components(G))
    print(f"[INFO] Identified {len(comps)} distinct novel species clusters.")

    # 4. Assign IDs and Save
    results = []
    for i, comp in enumerate(comps, start=1):
        cluster_id = f"NovelSp_{i:03d}"  # e.g., NovelSp_001
        
        # Pick a "Representative" (e.g., alphabetically first)
        members = sorted(list(comp))
        rep = members[0]
        
        for member in members:
            results.append({
                'novel_species_id': cluster_id,
                'genome_filename': member,
                'representative': rep,
                'cluster_size': len(members)
            })

    df_out = pd.DataFrame(results)
    df_out.to_csv(OUT_CLUSTERS, sep='\t', index=False)
    print(f"[DONE] Saved cluster definitions to {OUT_CLUSTERS}")
    
    # Summary
    print("\nSize Distribution:")
    print(df_out['cluster_size'].value_counts().sort_index())

if __name__ == "__main__":
    main()
