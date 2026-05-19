#!/usr/bin/env python3
import os
import sys
import pandas as pd

REFSEQ_SUMMARY = "../meta/fungi_all/assembly_summary_fungi_refseq.txt"
TAXDUMP_DIR = "../refCalibrationResults/taxdump/"
OUTFILE = "../refCalibrationResults/refseq_metadata.tsv"

NODES = os.path.join(TAXDUMP_DIR, "nodes.dmp")
NAMES = os.path.join(TAXDUMP_DIR, "names.dmp")

RANKS = ["species", "genus", "family", "order", "class", "phylum", "kingdom"]


def load_names():
    names = {}
    with open(NAMES) as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            taxid = int(parts[0])
            name = parts[1]
            type_ = parts[3]
            if type_ == "scientific name":
                names[taxid] = name
    return names


def load_nodes():
    nodes = {}
    with open(NODES) as f:
        for line in f:
            parts = [p.strip() for p in line.split("|")]
            tid = int(parts[0])
            parent = int(parts[1])
            rank = parts[2]
            nodes[tid] = (parent, rank)
    return nodes


def trace_lineage(start_taxid, nodes):
    """
    Return dict {rank: taxid} for all ranks of interest.
    """
    out = {r: None for r in RANKS}
    cur = start_taxid
    visited = set()

    while cur != 1 and cur not in visited:
        visited.add(cur)
        parent, rank = nodes.get(cur, (1, None))

        if rank in out:
            out[rank] = cur

        if cur == parent:
            break
        cur = parent

    return out


def main():
    print("Loading taxdump...")
    names = load_names()
    nodes = load_nodes()

    print("Loading RefSeq summary...")
    df = pd.read_csv(
        REFSEQ_SUMMARY,
        sep="\t",
        comment="#",
        header=None,
        low_memory=False
    )

    # According to assembly_summary format:
    # col 0 = assembly_accession
    # col 5 = taxid
    # col 6 = species_taxid
    # col 7 = organism_name

    df_sum = pd.DataFrame()
    df_sum["assembly"] = df[0]
    df_sum["taxid"] = df[5].astype(int)
    df_sum["species_taxid"] = df[6].astype(int)
    df_sum["organism_name"] = df[7]

    # If species_taxid == 0, use taxid instead
    df_sum.loc[df_sum["species_taxid"] == 0, "species_taxid"] = df_sum["taxid"]

    print(f"Total genomes: {len(df_sum)}")

    records = []
    for _, row in df_sum.iterrows():
        sp_taxid = int(row["species_taxid"])
        lin = trace_lineage(sp_taxid, nodes)

        rec = {
            "assembly": row["assembly"],
            "organism_name": row["organism_name"],
            "species_taxid": sp_taxid,
            "species_name": names.get(lin["species"], ""),
        }
        # add higher ranks
        for r in RANKS:
            rec[f"{r}_taxid"] = lin[r]
            rec[f"{r}_name"] = names.get(lin[r], "")

        records.append(rec)

    out_df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)
    out_df.to_csv(OUTFILE, sep="\t", index=False)
    print(f"Saved: {OUTFILE}")


if __name__ == "__main__":
    main()

