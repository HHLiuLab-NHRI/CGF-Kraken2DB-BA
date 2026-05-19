#!/usr/bin/env python3
import os
import time

META_DIR = "../meta/fungi_all/"
REFSEQ_FILE  = os.path.join(META_DIR, "assembly_summary_fungi_refseq.txt")
GENBANK_FILE = os.path.join(META_DIR, "assembly_summary_fungi_genbank.txt")
OUT_TSV = os.path.join(META_DIR, "fungi_all_ftp_paths.tsv")

def log(msg):
    print(time.strftime("[%Y-%m-%d %H:%M:%S]"), msg)


def parse_fungi_summary(path):
    """
    Parses fungal assembly summary files with auto-detected column indices.
    Returns dict: accession → ftp_path
    """
    fungal = {}
    header = None
    accession_idx = None
    ftp_idx = None

    if not os.path.exists(path):
        log(f"ERROR: Cannot find file: {path}")
        return fungal

    log(f"Reading: {path}")

    with open(path) as f:
        for line in f:

            # Skip the leading explanatory comment line beginning with "##"
            if line.startswith("##"):
                continue

            # Detect header line
            if line.startswith("#assembly_accession"):
                header = line[1:].strip().split("\t")

                try:
                    accession_idx = header.index("assembly_accession")
                    ftp_idx       = header.index("ftp_path")
                except ValueError:
                    log("ERROR: Could not locate required columns in:")
                    log(header)
                    return {}

                continue

            # Skip any remaining comment lines
            if line.startswith("#"):
                continue

            # No header found yet → cannot parse
            if header is None:
                continue

            parts = line.rstrip("\n").split("\t")
            if len(parts) <= ftp_idx:
                continue

            acc = parts[accession_idx].strip()
            ftp = parts[ftp_idx].strip()

            if ftp != "na" and ftp != "":
                fungal[acc] = ftp

    return fungal


def build_fasta_url(ftp_root, acc):
    """
    Convert ftp root to a direct HTTPS FASTA URL.
    """
    https_root = ftp_root.replace("ftp://", "https://")
    return f"{https_root}/{acc}_genomic.fna.gz"


def main():
    log("=== Extracting fungal FTP paths from summary files ===")

    fungi = {}

    fungi.update(parse_fungi_summary(REFSEQ_FILE))
    fungi.update(parse_fungi_summary(GENBANK_FILE))

    log(f"Total fungal assemblies collected: {len(fungi)}")

    log(f"Writing output TSV: {OUT_TSV}")
    with open(OUT_TSV, "w") as out:
        out.write("accession\tftp_root\tfasta_url\n")
        for acc, ftp in sorted(fungi.items()):
            fasta = build_fasta_url(ftp, acc)
            out.write(f"{acc}\t{ftp}\t{fasta}\n")

    log("=== DONE ===")


if __name__ == "__main__":
    main()

