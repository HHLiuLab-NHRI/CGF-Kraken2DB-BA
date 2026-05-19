#!/usr/bin/env python3
import os
import math
import glob

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
INPUT_LIST = "../CGFNovelResults/filelist_novel.txt"
CHUNK_DIR  = "../CGFNovelResults/chunks"
CHUNK_SIZE = 50  # 281 files -> ~6 chunks. 6x6=36 jobs. Very fast.

os.makedirs(CHUNK_DIR, exist_ok=True)

# Clean old chunks
for f in glob.glob(os.path.join(CHUNK_DIR, "*.list")):
    os.remove(f)

def main():
    if not os.path.exists(INPUT_LIST):
        print("[ERROR] Input list not found.")
        return

    with open(INPUT_LIST) as f:
        lines = [x.strip() for x in f if x.strip()]

    total = len(lines)
    num_chunks = math.ceil(total / CHUNK_SIZE)
    print(f"[INFO] Splitting {total} files into {num_chunks} chunks (size {CHUNK_SIZE}).")

    for i in range(num_chunks):
        chunk = lines[i*CHUNK_SIZE : (i+1)*CHUNK_SIZE]
        out_name = os.path.join(CHUNK_DIR, f"chunk_{i:03d}.list")
        with open(out_name, "w") as out:
            out.write("\n".join(chunk) + "\n")
            
    print(f"[DONE] Chunks written to {CHUNK_DIR}")

if __name__ == "__main__":
    main()
