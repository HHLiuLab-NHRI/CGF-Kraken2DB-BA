#! /usr/bin/python3

import pandas as pd
import os

def find_top_samples(input_csv, output_csv, target="Penicillium", top_n=5):
    print(f"Processing: {input_csv}")
    
    # Load the CSV
    df = pd.read_csv(input_csv)
    
    # Identify the column containing the target genus
    target_cols = [col for col in df.columns if target.lower() in col.lower()]
    
    if not target_cols:
        print(f"  -> Error: '{target}' column not found in this file.\n")
        return
        
    target_col = target_cols[0]
    
    # Sort by the target column descending and grab the top N
    top_samples = df[['Identifier', target_col]].sort_values(by=target_col, ascending=False).head(top_n)
    
    # Ensure the target directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Save the output
    top_samples.to_csv(output_csv, index=False)
    
    print(f"  -> Top 3 {target} samples:")
    for index, row in top_samples.iterrows():
        print(f"     {row['Identifier']}: {row[target_col]}")
    print(f"  -> Saved to: {output_csv}\n")

if __name__ == "__main__":
    # Define your input paths
    r1_csv = "../k2GenusSummary_R1_nFunDB/genusAverage.csv"
    r2_csv = "../k2GenusSummary_R2_nFunDB/genusAverage.csv"
    
    # Define your output paths
    r1_out = "../sankey/top5_penicillium_R1.csv"
    r2_out = "../sankey/top5_penicillium_R2.csv"
    
    # Run the function for both Read 1 and Read 2
    find_top_samples(r1_csv, r1_out)
    find_top_samples(r2_csv, r2_out)
