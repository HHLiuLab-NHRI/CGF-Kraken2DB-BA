#! /usr/bin/python3
# Summarize duplicates for Forward (R1) reads

iDir = '../k2Genus_R1/'
oDir = '../k2GenusSummary_R1/'

from glob import glob
from os import system
import pandas as pd

# Create output directory
system('mkdir -p ' + oDir)

# Get list of subdirectories (1/, 2/...)
sd = glob(iDir + '*')
indices = list(map(lambda d: d.split('/')[-1] + '/', sd))

print(f"Aggregating counts from {len(indices)} replicates...")

# Step 1: Create a merged CSV for EACH replicate folder (genus_1.csv, genus_2.csv...)
for i in indices:
    df = pd.DataFrame()
    csv_files = glob(iDir + i + '*.csv')
    
    # Concatenate all samples within this folder
    for c in csv_files:
        dfCSV = pd.read_csv(c)
        df = pd.concat([df, dfCSV], axis=0, ignore_index=True).fillna(0)
    
    # Save intermediate file (e.g., genus_1.csv)
    df.to_csv(oDir + 'genus_' + i[:-1] + '.csv', index=False)

# Step 2: Average across all replicates
print("Calculating averages...")

# Load the intermediate summary files (genus_1.csv, genus_2.csv, etc.)
summary_csvs = glob(oDir + 'genus_*.csv')
df = pd.DataFrame()

for c in summary_csvs:
    dfCSV = pd.read_csv(c)
    df = pd.concat([df, dfCSV], axis=0, ignore_index=True).fillna(0)

# Group by Sample Name ('Identifier') and sum
df = df.groupby('Identifier', as_index=False).sum(numeric_only=True)

# Average numeric genus columns using float dtype
numeric_cols = df.columns.drop('Identifier')
df = pd.concat(
    [
        df[['Identifier']],
        df[numeric_cols].astype('float64').div(len(summary_csvs))
    ],
    axis=1
)

# Save final matrix
output_file = oDir + 'genusAverage.csv'
df.to_csv(output_file, index=False)

print(f"Done. Final summary saved to: {output_file}")
