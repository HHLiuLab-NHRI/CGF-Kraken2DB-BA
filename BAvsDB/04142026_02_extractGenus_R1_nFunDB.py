#! /usr/bin/python3
# Extract Genus info for Forward (R1) reads - CORRECTED EXTENSION

iDir = '../kraken2Output_R1_nFunDB/'
oDir = '../k2Genus_R1_nFunDB/'

from glob import glob
from os import system

# 1. Identify subdirectories
sd = glob(iDir + '*')
# Only process directories
indices = [d.split('/')[-1] + '/' for d in sd if '.' not in d.split('/')[-1]]

# 2. Create corresponding output directories
for i in indices:
    system('mkdir -p ' + oDir + i)

print(f"Processing reports from {iDir}...")

# --- FIX: Changed glob to match *.report instead of *.k2.report ---
for iReport in glob(iDir + '*/*.report'):
    
    # Extract filename carefully. 
    # Input: SRR35008927_1.fastq.gz.report
    # Split by '.' -> ['SRR35008927_1', 'fastq', 'gz', 'report']
    # Element [0] -> 'SRR35008927_1'
    oName = iReport.split('/')[-1].split('.')[0]
    
    # Extract subdirectory (e.g., "1")
    subFolder = iReport.split('/')[-2]
    
    oCSV = oDir + subFolder + '/' + oName + '.csv'

    # Parse the Kraken2 report
    try:
        f = open(iReport, 'r')
        genus = {}
        while 1:
            l = f.readline().strip()
            if not len(l): break
            r = l.split('\t')
            # Filter: Count > 0 AND Rank == 'G' (Genus)
            if int(r[1]) > 0 and r[3] == 'G':
                genus[r[-1].strip()] = r[1]
        f.close()

        # Write the single-row CSV
        f = open(oCSV, 'w')
        f.write('Identifier,')
        keys = sorted(genus.keys())
        f.write(','.join(keys) + '\n')
        
        f.write(oName + ',')
        values = list(map(lambda k: genus[k], keys))
        f.write(','.join(values) + '\n')
        f.close()
    except Exception as e:
        print(f"Error processing {iReport}: {e}")

print("Extraction complete.")
