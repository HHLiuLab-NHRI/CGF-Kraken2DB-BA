#! /usr/bin/python3
# Summarize duplicates for Reverse (R2) reads

iDir = '../k2Genus_R2/'
oDir = '../k2GenusSummary_R2/'

from glob import glob
from os import system
import pandas as pd

system('mkdir -p ' + oDir)

sd = glob(iDir + '*')
indices = list(map(lambda d: d.split('/')[-1] + '/', sd))

print(f"Aggregating counts from {len(indices)} replicates...")

for i in indices:
    df = pd.DataFrame()
    csv_files = glob(iDir + i + '*.csv')
    for c in csv_files:
        dfCSV = pd.read_csv(c)
        df = pd.concat([df, dfCSV], axis=0, ignore_index=True).fillna(0)
    df.to_csv(oDir + 'genus_' + i[:-1] + '.csv', index=False)

print("Calculating averages...")
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

output_file = oDir + 'genusAverage.csv'
df.to_csv(output_file, index=False)

print(f"Done. Final summary saved to: {output_file}")
