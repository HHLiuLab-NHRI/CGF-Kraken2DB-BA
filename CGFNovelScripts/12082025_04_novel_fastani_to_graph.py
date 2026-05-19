#!/usr/bin/env python3
import os
import glob
import pandas as pd

FASTANI_DIR = "../CGFNovelResults/fastani_out"
OUT_GRAPH   = "../CGFNovelResults/novel_graph_edges.tsv"
ANI_CUTOFF  = 95.0

def main():
    print(f"[INFO] Merging files from {FASTANI_DIR}...")
    files = glob.glob(os.path.join(FASTANI_DIR, "*.tsv"))
    
    if not files:
        print("[ERROR] No FastANI output files found.")
        return

    # Use a set to store unique edges to save memory/avoid dupes
    # Format: tuple(sorted((genomeA, genomeB))) -> max_ani
    # Actually, we can just stream-write significant hits to disk
    
    count = 0
    with open(OUT_GRAPH, "w") as out:
        out.write("node1\tnode2\tani\n")
        
        for f in files:
            try:
                # FastANI columns: query, ref, ani, map_frag, tot_frag
                # Read chunks to handle potential weirdness, though usually small
                df = pd.read_csv(f, sep='\t', header=None, names=['q','r','ani','m','t'], engine='python')
                
                # Filter strict ANI
                df = df[df['ani'] >= ANI_CUTOFF]
                
                for _, row in df.iterrows():
                    q = os.path.basename(row['q'])
                    r = os.path.basename(row['r'])
                    
                    # Avoid self-loops in graph
                    if q == r: 
                        continue
                        
                    out.write(f"{q}\t{r}\t{row['ani']}\n")
                    count += 1
            except Exception as e:
                print(f"[WARN] Error reading {f}: {e}")

    print(f"[DONE] Wrote {count} edges to {OUT_GRAPH}")

if __name__ == "__main__":
    main()
