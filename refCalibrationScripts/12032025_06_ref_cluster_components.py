#!/usr/bin/env python3
import os
import networkx as nx
import pandas as pd

EDGES_FILE = "../refCalibrationResults/fastani/edges_ref.tsv"
FILELIST   = "../refCalibrationResults/fastani/filelist_refseq.txt"
OUTFILE    = "../refCalibrationResults/clusters/ref_components.tsv"

def normalize(path: str) -> str:
    """
    Normalize a genome path to the basename used in edges_ref.tsv.
    """
    return os.path.basename(path.strip())

def main():
    # Load edges
    edges = pd.read_csv(
        EDGES_FILE,
        sep="\t",
        header=None,
        names=["A", "B", "ANI"]
    )

    G = nx.Graph()

    # Ensure all genomes (incl. ANI singletons) appear
    with open(FILELIST) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nid = normalize(line)
            G.add_node(nid)

    # Add edges
    for _, row in edges.iterrows():
        G.add_edge(row["A"], row["B"])

    components = list(nx.connected_components(G))

    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

    with open(OUTFILE, "w") as w:
        for i, comp in enumerate(components, 1):
            members = ",".join(sorted(comp))
            w.write(f"RefSp{i}\t{members}\n")

    print(f"[INFO] Clusters: {len(components)}")
    print(f"[INFO] Wrote: {OUTFILE}")

if __name__ == "__main__":
    main()

