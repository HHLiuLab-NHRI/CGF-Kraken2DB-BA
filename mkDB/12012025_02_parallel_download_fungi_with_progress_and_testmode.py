#!/usr/bin/env python3
import os
import time
import argparse
import subprocess
from multiprocessing import Pool, Manager
from tqdm import tqdm
import shutil
import zipfile

META_DIR = "../meta/fungi_all/"
TSV_FILE = os.path.join(META_DIR, "fungi_all_ftp_paths.tsv")   # We only use accession column

OUT_DIR = "../data/fungi_all/"
LOG_DIR = "../data/logs/fungi_all/"
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

NUM_WORKERS = 6
MAX_RETRIES = 3


def log(worker, msg):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} [W{worker}] {msg}"
    print(line)
    with open(os.path.join(LOG_DIR, f"worker_{worker}.log"), "a") as f:
        f.write(line + "\n")

def extract_fasta_from_zip(zip_path, final_output):
    """Extract genomic FASTA, compress it with pigz, and write final_output.gz"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            for fname in z.namelist():

                # Accept both fake ".fna.gz" entries and real ".fna"
                if fname.endswith("_genomic.fna") or fname.endswith("_genomic.fna.gz"):

                    # Extract to temp folder
                    extract_dir = "/tmp/fungi_extract"
                    z.extract(fname, extract_dir)

                    extracted_file = os.path.join(extract_dir, fname)

                    # Normalize to .fna
                    if extracted_file.endswith(".gz"):
                        # NCBI sometimes names as .fna.gz but contents are plain text
                        # Try gzip test
                        try:
                            subprocess.check_call(
                                f"gzip -t '{extracted_file}'", shell=True
                            )
                            # It is a real gzip file
                            shutil.move(extracted_file, final_output)
                            shutil.rmtree(extract_dir, ignore_errors=True)
                            return True
                        except:
                            # Not gzipped despite extension — rename to .fna
                            new_path = extracted_file[:-3]
                            os.rename(extracted_file, new_path)
                            extracted_file = new_path

                    # Now ensure we have plain .fna
                    if extracted_file.endswith(".fna"):
                        # Compress with pigz
                        subprocess.call(f"pigz -f '{extracted_file}'", shell=True)
                        gz_file = extracted_file + ".gz"

                        shutil.move(gz_file, final_output)
                        shutil.rmtree(extract_dir, ignore_errors=True)
                        return True

    except Exception as e:
        print("Zip extraction error:", e)

    return False

def download_one(job):
    acc, worker, progress = job

    # -----------------------------------------------------
    # Define file paths
    # -----------------------------------------------------
    final = os.path.join(OUT_DIR, f"{acc}.fna.gz")     # Expected final output
    partial = final + ".partial"                       # Temporary FASTA file
    zip_path = partial + ".zip"                        # Temporary ZIP download
    extract_tmp = "/tmp/fungi_extract"                 # Folder used by extraction
    # (Your extract_fasta_from_zip() function handles extraction internally)

    # -----------------------------------------------------
    # SKIP LOGIC (added)
    # -----------------------------------------------------

    # Case 1 — final output already exists
    if os.path.exists(final):
        log(worker, f"SKIP {acc} (already downloaded)")
        progress["done"] += 1
        return

    # Case 2 — leftover temporary ZIP → remove
    if os.path.exists(zip_path):
        log(worker, f"SKIP {acc} (removing stale {zip_path})")
        os.remove(zip_path)

    # Case 3 — leftover temporary FASTA → remove
    if os.path.exists(partial):
        log(worker, f"SKIP {acc} (removing stale {partial})")
        os.remove(partial)

    # -----------------------------------------------------
    # Begin download attempts
    # -----------------------------------------------------
    for attempt in range(1, MAX_RETRIES + 1):

        log(worker, f"{acc}: Attempt {attempt}/{MAX_RETRIES}")

        # ---------------------------------------------
        # 1) Download ZIP via NCBI datasets CLI
        # ---------------------------------------------
        cmd = (
            f"datasets download genome accession {acc} "
            f"--include genome "
            f"--filename '{zip_path}' >/dev/null 2>&1"
        )
        ret = subprocess.call(cmd, shell=True)

        if ret != 0 or not os.path.exists(zip_path):
            log(worker, f"{acc}: ERROR (datasets download failed)")
            continue

        # ---------------------------------------------
        # 2) Extract FASTA from ZIP
        # ---------------------------------------------
        ok = extract_fasta_from_zip(zip_path, partial)

        # Always remove ZIP after extraction attempt
        try:
            os.remove(zip_path)
        except FileNotFoundError:
            pass

        if not ok:
            log(worker, f"{acc}: ERROR no genomic FASTA in ZIP")
            continue

        # ---------------------------------------------
        # 3) Compress final .fna.gz
        # ---------------------------------------------
        # Your original logic:
        #   - partial may be plain .fna or already gzipped
        #   - compress if necessary, rename after success
        if os.path.exists(partial):
            if not final.endswith(".gz"):
                # Not expected for your pipeline, but retained for compatibility
                subprocess.call(f"pigz -f '{partial}'", shell=True)
                os.rename(partial + ".gz", final)
            else:
                # We expect plain FASTA → compress it
                subprocess.call(f"pigz -f '{partial}'", shell=True)
                # pigz outputs partial.gz
                gz = partial + ".gz"
                if os.path.exists(gz):
                    os.rename(gz, final)
                else:
                    # fallback: maybe extraction already produced .gz
                    if os.path.exists(partial):
                        os.rename(partial, final)

        # ---------------------------------------------
        # SUCCESS
        # ---------------------------------------------
        log(worker, f"SUCCESS {acc}")
        progress["done"] += 1
        return

    # -----------------------------------------------------
    # If all attempts fail
    # -----------------------------------------------------
    log(worker, f"FAILED {acc}")
    progress["done"] += 1

def main():
    parser = argparse.ArgumentParser(description="NCBI Datasets fungal downloader")
    parser.add_argument("--test", type=int, default=None,
                        help="Download only first N genomes")
    args = parser.parse_args()

    # Load accession table
    if not os.path.exists(TSV_FILE):
        print("ERROR: TSV not found:", TSV_FILE)
        return

    jobs_list = []
    with open(TSV_FILE) as f:
        header = f.readline()
        for line in f:
            acc = line.strip().split("\t")[0]   # Use only accession
            jobs_list.append(acc)

    # Apply test limit
    if args.test is not None:
        print(f"TEST MODE ENABLED: only first {args.test} genomes")
        jobs_list = jobs_list[:args.test]

    total = len(jobs_list)
    print(f"Loaded {total} accessions for download")

    manager = Manager()
    progress = manager.dict()
    progress["done"] = 0

    jobs = [(acc, i % NUM_WORKERS, progress) for i, acc in enumerate(jobs_list)]

    with tqdm(total=total, desc="Downloading genomes", unit="genome") as pbar:

        def update(_):
            pbar.n = progress["done"]
            pbar.refresh()

        with Pool(NUM_WORKERS) as pool:
            for j in jobs:
                pool.apply_async(download_one, (j,), callback=update)
            pool.close()
            pool.join()

    print("=== DONE ===")


if __name__ == "__main__":
    main()

