#!/usr/bin/env python3

import os
import pandas as pd


def find_top_samples(input_csv, output_csv, target="Penicillium", top_n=5):
    print(f"Processing: {input_csv}")
    df = pd.read_csv(input_csv)

    target_cols = [col for col in df.columns if target.lower() in col.lower()]
    if len(target_cols) != 1:
        raise ValueError(
            f"Expected exactly one '{target}' column in {input_csv}; found {target_cols}"
        )
    target_col = target_cols[0]

    top_samples = (
        df[["Identifier", target_col]]
        .sort_values(by=target_col, ascending=False)
        .head(top_n)
    )

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    top_samples.to_csv(output_csv, index=False)

    print(f"  -> Top {top_n} {target} samples:")
    for _, row in top_samples.iterrows():
        print(f"     {row['Identifier']}: {row[target_col]}")
    print(f"  -> Saved to: {output_csv}\n")


if __name__ == "__main__":
    find_top_samples(
        "../k2GenusSummary_R1_nFunDB/genusAverage.csv",
        "../sankey/top5_penicillium_R1.csv",
    )
    find_top_samples(
        "../k2GenusSummary_R2_nFunDB/genusAverage.csv",
        "../sankey/top5_penicillium_R2.csv",
    )
