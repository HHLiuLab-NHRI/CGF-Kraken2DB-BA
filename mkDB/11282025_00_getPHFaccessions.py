#!/usr/bin/env python3
import pandas as pd
import os

# ------------------------------------------
# Configuration
# ------------------------------------------
input_xlsx = "../meta/Table S2.xlsx"       # Path to Table S2
output_txt = "../meta/phf_accessions.txt"  # Output accession list

# ------------------------------------------
# Load Panel B of Table S2
# ------------------------------------------
print(f"Loading: {input_xlsx}")
xls = pd.ExcelFile(input_xlsx)

if "Panel B" not in xls.sheet_names:
    raise ValueError("Error: 'Panel B' not found in Table S2.xlsx sheets.")

panelB = pd.read_excel(input_xlsx, sheet_name="Panel B")

# ------------------------------------------
# Extract Assembly accession column
# ------------------------------------------
if "Assembly accession" not in panelB.columns:
    raise ValueError("Error: 'Assembly accession' column missing in Panel B.")

accessions = (
    panelB["Assembly accession"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()  # remove duplicates, if any
)

print(f"Total accessions extracted: {len(accessions)}")

# ------------------------------------------
# Save to text file
# ------------------------------------------
os.makedirs(os.path.dirname(output_txt), exist_ok=True)

with open(output_txt, "w") as f:
    for acc in accessions:
        f.write(acc + "\n")

print(f"Saved accession list to: {output_txt}")
