#!/usr/bin/env python3
import pandas as pd
import scipy.stats as stats
from statsmodels.stats.multitest import multipletests
import numpy as np
import os
import re

META_FILE = '../meta/meta.csv'
STAT_DIR = '../statistics/'
OUTPUT_TEXT_FILE = os.path.join(STAT_DIR, 'deFunDB_Metrics.txt')

# Create the statistics directory if it doesn't exist
os.makedirs(STAT_DIR, exist_ok=True)

# 0. Initialize and clear the output text file
with open(OUTPUT_TEXT_FILE, 'w') as f:
    f.write("============================================================\n")
    f.write("  DATA METRICS FOR REVIEWER RESPONSE\n")
    f.write("============================================================\n")

def log_and_print(message):
    """Prints to the console AND writes to the summary text file."""
    print(message)
    with open(OUTPUT_TEXT_FILE, 'a') as f:
        f.write(message + '\n')

def get_stats(input_file, read_label):
    log_and_print(f"\n{'='*60}\n ANALYZING {read_label} DATA \n{'='*60}")
    
    # 1. Load Data
    genus_df = pd.read_csv(input_file)
    meta_df = pd.read_csv(META_FILE)
    
    run_map = dict(zip(meta_df['Run'], meta_df['Sample Name']))
    genus_df['Run_ID'] = genus_df['Identifier'].apply(lambda x: str(x).split('_')[0])
    genus_df['Sample_Name'] = genus_df['Run_ID'].map(run_map)
    
    def assign_group(name):
        s = str(name)
        if re.match(r'^BA\d+$', s): return 'BA'
        if re.match(r'^H\d+$', s): return 'H'
        return None
        
    genus_df['Group'] = genus_df['Sample_Name'].apply(assign_group)
    analysis_df = genus_df.dropna(subset=['Group']).copy()
    
    # --- Sample Sizes ---
    n_ba = len(analysis_df[analysis_df['Group'] == 'BA'])
    n_h = len(analysis_df[analysis_df['Group'] == 'H'])
    log_and_print(f"SAMPLE SIZES: Total N = {n_ba + n_h} (BA: {n_ba}, Healthy Controls: {n_h})")
    
    # 2. Compute Stats
    numeric_cols = analysis_df.select_dtypes(include=['number']).columns.tolist()
    metadata_cols = ['Identifier', 'Run_ID', 'Sample_Name', 'Group']
    genera_cols = [c for c in numeric_cols if c not in metadata_cols]
    
    results = []
    
    for genus in genera_cols:
        ba = analysis_df[analysis_df['Group'] == 'BA'][genus]
        h = analysis_df[analysis_df['Group'] == 'H'][genus]
        
        # Prevalences (Samples with > 0 reads)
        prev_ba_count = (ba > 0).sum()
        prev_h_count = (h > 0).sum()
        
        mean_ba = ba.mean()
        mean_h = h.mean()
        
        # Log2 Fold Change (add pseudo-count of 0.1 to avoid log(0))
        l2fc = np.log2((mean_ba + 0.1) / (mean_h + 0.1))
        
        if ba.sum() == 0 and h.sum() == 0:
            p_val = 1.0
            r_biserial = 0.0
        else:
            try: 
                U, p_val = stats.mannwhitneyu(ba, h, alternative='two-sided')
                # Rank-Biserial Correlation (Cliff's Delta equivalent effect size)
                r_biserial = (2 * U) / (n_ba * n_h) - 1
            except: 
                p_val = 1.0
                r_biserial = 0.0
                
        enriched_in = 'BA' if mean_ba > mean_h else ('H' if mean_h > mean_ba else 'None')
        
        results.append({
            'Genus': genus,
            'Prevalence_BA': f"{prev_ba_count}/{n_ba} ({(prev_ba_count/n_ba)*100:.1f}%)",
            'Prevalence_H': f"{prev_h_count}/{n_h} ({(prev_h_count/n_h)*100:.1f}%)",
            'Mean_BA': round(mean_ba, 2),
            'Mean_H': round(mean_h, 2),
            'Log2_Fold_Change': round(l2fc, 2),
            'Rank_Biserial_Effect': round(r_biserial, 3),
            'p_value': p_val,
            'Enriched_In': enriched_in
        })
        
    stats_df = pd.DataFrame(results)
    
    # FDR Correction
    if not stats_df.empty:
        _, stats_df['FDR_adj_p'], _, _ = multipletests(stats_df['p_value'], method='fdr_bh')
    else:
        stats_df['FDR_adj_p'] = 1.0
        
    # --- Denominator and Skew ---
    total_tested = len(stats_df)
    higher_ba = len(stats_df[stats_df['Enriched_In'] == 'BA'])
    higher_h = len(stats_df[stats_df['Enriched_In'] == 'H'])
    
    sig_01 = stats_df[stats_df['FDR_adj_p'] < 0.01]
    sig_ba_01 = len(sig_01[sig_01['Enriched_In'] == 'BA'])
    sig_h_01 = len(sig_01[sig_01['Enriched_In'] == 'H'])
    
    log_and_print(f"\nDENOMINATOR & SKEW:")
    log_and_print(f"Total Genera Tested: {total_tested}")
    log_and_print(f"Higher mean in BA: {higher_ba} (Significant at FDR<0.01: {sig_ba_01})")
    log_and_print(f"Higher mean in H: {higher_h} (Significant at FDR<0.01: {sig_h_01})")
    
    # --- FDR Threshold ---
    sig_05 = stats_df[stats_df['FDR_adj_p'] < 0.05]
    log_and_print(f"\nFDR THRESHOLD:")
    log_and_print(f"Significant at FDR < 0.05: {len(sig_05)} genera")
    log_and_print(f"Significant at FDR < 0.01: {len(sig_01)} genera")
    
    # Save into the statistics directory
    stats_df = stats_df.sort_values('FDR_adj_p')
    out_file = os.path.join(STAT_DIR, f"deFunDB_EffectSizes_{read_label}.csv")
    stats_df.to_csv(out_file, index=False)
    log_and_print(f"\nWrote comprehensive effect size/prevalence table to -> {out_file}")

# Run for both R1 and R2
try: get_stats('../k2GenusSummary_R1_deFunDB/genusAverage.csv', 'R1')
except Exception as e: log_and_print(f"Could not process R1: {e}")

try: get_stats('../k2GenusSummary_R2_deFunDB/genusAverage.csv', 'R2')
except Exception as e: log_and_print(f"Could not process R2: {e}")
