#!/usr/bin/env python3
import os
import csv

COMPONENTS_FILE = "../refCalibrationResults/clusters/ref_components.tsv"
SUMMARY_FILE    = "../meta/fungi_all/assembly_summary_fungi_refseq.txt"
OUT_MEMBERS     = "../refCalibrationResults/clusters/ref_components_members_with_ncbi.tsv"

def load_ncbi_summary(path):
    """
    Parse assembly_summary_fungi_refseq.txt into a dict:
    accession -> metadata dict
    """
    meta = {}

    with open(path) as f:
        reader = csv.reader(f, delimiter="\t")
        header = None
        for line in f:
            if line.startswith("#"):
                header = line.lstrip("#").strip().split("\t")
                continue
            parts = line.rstrip("\n").split("\t")
            if not parts or parts[0] == "":
                continue
            if header is None:
                # No header line found; assume standard assembly_summary order
                # (assembly_accession is column 0, taxid 5, species_taxid 6, organism_name 7, infraspecific_name 8, ftp_path 19)
                assembly_accession = parts[0]
                taxid              = parts[5] if len(parts) > 5 else ""
                species_taxid      = parts[6] if len(parts) > 6 else ""
                organism_name      = parts[7] if len(parts) > 7 else ""
                infraspecific_name = parts[8] if len(parts) > 8 else ""
                ftp_path           = parts[19] if len(parts) > 19 else ""
            else:
                cols = {h: (parts[i] if i < len(parts) else "") for i, h in enumerate(header)}
                assembly_accession = cols.get("assembly_accession", "")
                taxid              = cols.get("taxid", "")
                species_taxid      = cols.get("species_taxid", "")
                organism_name      = cols.get("organism_name", "")
                infraspecific_name = cols.get("infraspecific_name", "")
                ftp_path           = cols.get("ftp_path", "")

            if not assembly_accession:
                continue

            meta[assembly_accession] = {
                "taxid": taxid,
                "species_taxid": species_taxid,
                "organism_name": organism_name,
                "infraspecific_name": infraspecific_name,
                "ftp_path": ftp_path,
            }

    print(f"[INFO] Loaded metadata for {len(meta)} assemblies from {path}")
    return meta

def basename_to_accession(basename: str) -> str:
    """
    Convert basename like GCF_012345678.1.fna.gz → GCF_012345678.1
    or GCA_... similarly.
    """
    for ext in (".fna.gz", ".fna", ".fa.gz", ".fa"):
        if basename.endswith(ext):
            return basename[:-len(ext)]
    return basename

def main():
    meta = load_ncbi_summary(SUMMARY_FILE)

    os.makedirs(os.path.dirname(OUT_MEMBERS), exist_ok=True)

    with open(COMPONENTS_FILE) as f_in, open(OUT_MEMBERS, "w") as f_out:
        header = [
            "cluster_id",
            "member_basename",
            "assembly_accession",
            "taxid",
            "species_taxid",
            "organism_name",
            "infraspecific_name",
            "ftp_path",
        ]
        f_out.write("\t".join(header) + "\n")

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            clust_id, members_str = line.split("\t", 1)
            members = [m for m in members_str.split(",") if m]

            for m in members:
                acc = basename_to_accession(m)
                info = meta.get(acc, {})
                row = [
                    clust_id,
                    m,
                    acc,
                    info.get("taxid", ""),
                    info.get("species_taxid", ""),
                    info.get("organism_name", ""),
                    info.get("infraspecific_name", ""),
                    info.get("ftp_path", ""),
                ]
                f_out.write("\t".join(row) + "\n")

    print(f"[INFO] Wrote member+metadata table → {OUT_MEMBERS}")

if __name__ == "__main__":
    main()

