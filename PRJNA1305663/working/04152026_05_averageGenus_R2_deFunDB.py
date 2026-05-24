#! /usr/bin/python3
# Summarize duplicates for Forward (R1) reads

import os
import pandas as pd
from glob import glob

iDir = '../k2Genus_R2_deFunDB/'
oDir = '../k2GenusSummary_R2_deFunDB/'

# 1. Use os.makedirs instead of system calls for safety
os.makedirs(oDir, exist_ok=True)

# Get list of subdirectories (1, 2...) safely
sd = glob(os.path.join(iDir, '*/'))
indices = [os.path.basename(os.path.dirname(d)) for d in sd]

print(f"Aggregating counts from {len(indices)} replicates...")

# Step 1: Create a merged CSV for EACH replicate folder (genus_1.csv, genus_2.csv...)
for i in indices:
    csv_files = glob(os.path.join(iDir, str(i), '*.csv'))
    if not csv_files:
        continue
    
    # OPTIMIZATION 1: Read all CSVs into a list first, then concatenate once.
    # This prevents Pandas memory fragmentation and is significantly faster.
    df_list = [pd.read_csv(c) for c in csv_files]
    df = pd.concat(df_list, axis=0, ignore_index=True).fillna(0)
    
    # Save intermediate file (e.g., genus_1.csv)
    df.to_csv(os.path.join(oDir, f'genus_{i}.csv'), index=False)

# Step 2: Average across all replicates
print("Calculating averages...")

# Load the intermediate summary files (genus_1.csv, genus_2.csv, etc.)
summary_csvs = glob(os.path.join(oDir, 'genus_*.csv'))

if summary_csvs:
    # Read intermediate summaries efficiently
    summary_list = [pd.read_csv(c) for c in summary_csvs]
    df_total = pd.concat(summary_list, axis=0, ignore_index=True).fillna(0)

    # Group by Sample Name ('Identifier') and Sum
    df_grouped = df_total.groupby('Identifier', as_index=False).sum()

    # OPTIMIZATION 2: Fix the FutureWarnings regarding incompatible dtypes.
    # Instead of in-place assignment (which forces floats into int64 columns), 
    # we isolate the numeric columns, divide them, and concatenate them back with the identifiers.
    numeric_cols = df_grouped.columns.drop('Identifier')
    
    # Division automatically handles the float casting gracefully here
    df_averaged = df_grouped[numeric_cols] / len(summary_csvs)
    
    # Re-attach the Identifier column
    df_final = pd.concat([df_grouped[['Identifier']], df_averaged], axis=1)

    # Save final matrix
    output_file = os.path.join(oDir, 'genusAverage.csv')
    df_final.to_csv(output_file, index=False)

    print(f"Done. Final summary saved to: {output_file}")
else:
    print("Error: No summary files found to calculate averages.")
