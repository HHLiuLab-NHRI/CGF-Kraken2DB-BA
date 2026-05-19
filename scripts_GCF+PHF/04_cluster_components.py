#!/usr/bin/env python3
import networkx as nx
import pandas as pd
import os

EDGES_FILE   = "../results/fastani/edges.tsv"       # from fixed 03_fastani_to_graph.py
FILELIST     = "../results/fastani/filelist.txt"    # all 1210 genomes
OUTFILE      = "../results/clusters/01_components.tsv"

def normalize(path: str) -> str:
    """
    Normalize a genome path to the same form used in edges.tsv.
    03_fastani_to_graph.py writes basenames (e.g. GCA_XXXX.fna),
    so we just take basename here as well.
    """
    return os.path.basename(path.strip())

# --- Load edges (normalized already by 03 script) ---
edges = pd.read_csv(
    EDGES_FILE,
    sep="\t",
    header=None,
    names=["A", "B", "ANI"]
)

G = nx.Graph()

# --- Add ALL genomes from filelist as nodes (to keep singletons) ---
with open(FILELIST) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        nid = normalize(line)
        G.add_node(nid)

# --- Add edges from ANI results ---
for _, row in edges.iterrows():
    G.add_edge(row["A"], row["B"])

components = list(nx.connected_components(G))

os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

with open(OUTFILE, "w") as w:
    for i, comp in enumerate(components, 1):
        w.write(f"Sp{i}\t" + ",".join(sorted(comp)) + "\n")

print("Clusters:", len(components))
print("Wrote:", OUTFILE)

