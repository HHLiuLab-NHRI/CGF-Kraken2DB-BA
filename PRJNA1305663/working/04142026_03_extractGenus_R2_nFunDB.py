#! /usr/bin/python3
# Extract Genus info for Reverse (R2) reads - CORRECTED EXTENSION

iDir = '../kraken2Output_R2_nFunDB/'
oDir = '../k2Genus_R2_nFunDB/'

from glob import glob
from os import system

sd = glob(iDir + '*')
indices = [d.split('/')[-1] + '/' for d in sd if '.' not in d.split('/')[-1]]

for i in indices:
    system('mkdir -p ' + oDir + i)

print(f"Processing reports from {iDir}...")

# --- FIX: Changed glob to match *.report ---
for iReport in glob(iDir + '*/*.report'):
    oName = iReport.split('/')[-1].split('.')[0]
    subFolder = iReport.split('/')[-2]
    oCSV = oDir + subFolder + '/' + oName + '.csv'

    try:
        f = open(iReport, 'r')
        genus = {}
        while 1:
            l = f.readline().strip()
            if not len(l): break
            r = l.split('\t')
            if int(r[1]) > 0 and r[3] == 'G':
                genus[r[-1].strip()] = r[1]
        f.close()

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
