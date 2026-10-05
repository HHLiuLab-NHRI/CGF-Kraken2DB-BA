#!/usr/bin/env python3
"""Recompute final BA-vs-healthy effect sizes, BH-FDR values, and direct 95% CIs.

Confirmed legacy database mapping:
  k2GenusSummary_R1/R2                  -> original/default Kraken2 fungal reference
  k2GenusSummary_R1_nFunDB/R2_nFunDB   -> CGF/PHF-enhanced reference
  k2GenusSummary_R1_deFunDB/R2_deFunDB -> locally rebuilt non-enhanced control

Rank-biserial 95% CIs use DeLong structural-component variance for the
equivalent AUC statistic, with r = 2*AUC - 1 and ties counted as 0.5.
The descriptive log2 fold change uses the historical pseudocount 0.1.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

PSEUDOCOUNT = 0.1
DATABASES = {
    "default": {
        "R1": "k2GenusSummary_R1/genusAverage.csv",
        "R2": "k2GenusSummary_R2/genusAverage.csv",
    },
    "enhanced": {
        "R1": "k2GenusSummary_R1_nFunDB/genusAverage.csv",
        "R2": "k2GenusSummary_R2_nFunDB/genusAverage.csv",
    },
    "nonenhanced": {
        "R1": "k2GenusSummary_R1_deFunDB/genusAverage.csv",
        "R2": "k2GenusSummary_R2_deFunDB/genusAverage.csv",
    },
}


def assign_group(sample_name):
    value = str(sample_name)
    if re.fullmatch(r"BA\d+", value):
        return "BA"
    if re.fullmatch(r"H\d+", value):
        return "H"
    return None


def load_matrix(matrix_path: Path, meta_path: Path) -> pd.DataFrame:
    matrix = pd.read_csv(matrix_path)
    meta = pd.read_csv(meta_path)
    if "Identifier" not in matrix.columns:
        raise ValueError(f"{matrix_path} must contain Identifier")
    if not {"Run", "Sample Name"}.issubset(meta.columns):
        raise ValueError(f"{meta_path} must contain Run and Sample Name")

    run_to_sample = dict(zip(meta["Run"].astype(str), meta["Sample Name"]))
    matrix["Run_ID"] = matrix["Identifier"].astype(str).str.split("_").str[0]
    matrix["Sample_Name"] = matrix["Run_ID"].map(run_to_sample)
    matrix["Group"] = matrix["Sample_Name"].map(assign_group)
    matrix = matrix[matrix["Group"].isin(["BA", "H"])].copy()

    counts = matrix["Group"].value_counts().to_dict()
    if counts.get("BA") != 50 or counts.get("H") != 40:
        raise ValueError(f"Expected BA=50 and H=40; observed {counts}")
    return matrix


def rank_biserial_delong_ci(ba, healthy):
    ba = np.asarray(ba, dtype=float)
    healthy = np.asarray(healthy, dtype=float)
    comparisons = (
        (ba[:, None] > healthy[None, :]).astype(float)
        + 0.5 * (ba[:, None] == healthy[None, :])
    )
    auc = float(comparisons.mean())
    v10 = comparisons.mean(axis=1)
    v01 = comparisons.mean(axis=0)
    r = 2.0 * auc - 1.0
    var_auc = np.var(v10, ddof=1) / len(v10) + np.var(v01, ddof=1) / len(v01)
    se_r = 2.0 * np.sqrt(max(float(var_auc), 0.0))
    z = stats.norm.ppf(0.975)
    return r, se_r, max(-1.0, r - z * se_r), min(1.0, r + z * se_r)


def analyze(df: pd.DataFrame) -> pd.DataFrame:
    n_ba = int((df["Group"] == "BA").sum())
    n_h = int((df["Group"] == "H").sum())
    excluded = {"Identifier", "Run_ID", "Sample_Name", "Group"}
    genera = [c for c in df.columns if c not in excluded]
    rows = []

    for genus in genera:
        ba = df.loc[df["Group"] == "BA", genus].to_numpy(float)
        healthy = df.loc[df["Group"] == "H", genus].to_numpy(float)
        mean_ba, mean_h = float(ba.mean()), float(healthy.mean())

        if ba.sum() == 0 and healthy.sum() == 0:
            u_stat, p_value = n_ba * n_h / 2.0, 1.0
            r, se_r, ci_low, ci_high = 0.0, 0.0, 0.0, 0.0
        else:
            u_stat, p_value = stats.mannwhitneyu(ba, healthy, alternative="two-sided")
            r, se_r, ci_low, ci_high = rank_biserial_delong_ci(ba, healthy)

        r_from_u = 2.0 * float(u_stat) / (n_ba * n_h) - 1.0
        if not np.isclose(r, r_from_u, atol=1e-12):
            raise RuntimeError(f"AUC/U effect mismatch for {genus}")

        rows.append({
            "Genus": genus,
            "Prevalence_BA": f"{(ba > 0).sum()}/{n_ba} ({100*(ba > 0).sum()/n_ba:.1f}%)",
            "Prevalence_H": f"{(healthy > 0).sum()}/{n_h} ({100*(healthy > 0).sum()/n_h:.1f}%)",
            "Mean_BA": round(mean_ba, 2),
            "Mean_H": round(mean_h, 2),
            "Log2_Fold_Change": round(np.log2((mean_ba + PSEUDOCOUNT)/(mean_h + PSEUDOCOUNT)), 2),
            "Rank_Biserial_Effect": round(r_from_u, 3),
            "Rank_Biserial_CI95_Lower": ci_low,
            "Rank_Biserial_CI95_Upper": ci_high,
            "Rank_Biserial_SE_DeLong": se_r,
            "p_value": float(p_value),
            "Enriched_In": "BA" if mean_ba > mean_h else "H" if mean_h > mean_ba else "None",
        })

    result = pd.DataFrame(rows)
    result["FDR_adj_p"] = multipletests(result["p_value"], method="fdr_bh")[1]
    return result.sort_values("FDR_adj_p").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser()
    default_root = Path(__file__).resolve().parent.parent
    parser.add_argument("--study-root", type=Path, default=default_root)
    parser.add_argument("--meta", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    root = args.study_root.resolve()
    meta = args.meta.resolve() if args.meta else root / "meta" / "meta.csv"
    out = args.output_dir.resolve() if args.output_dir else root / "statistics_direct_ci"
    out.mkdir(parents=True, exist_ok=True)

    for db_name, reads in DATABASES.items():
        for read_name, rel in reads.items():
            result = analyze(load_matrix(root / rel, meta))
            output = out / f"{db_name}_EffectSizes_DirectCI_{read_name}.csv"
            result.to_csv(output, index=False)
            print(f"{db_name:11s} {read_name}: {len(result)} genera; "
                  f"{int((result['FDR_adj_p'] < 0.01).sum())} at FDR<0.01 -> {output}")


if __name__ == "__main__":
    main()
