#!/usr/bin/env python3

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats
from statsmodels.stats.multitest import multipletests
import os
import re

# ==========================================
# 1. Configuration
# ==========================================
META_FILE = '../meta/meta.csv'

TASKS = [
    {
        'label': 'R1',
        'input_file': '../k2GenusSummary_R1/genusAverage.csv',
        'output_dir': '../Geni_Analyses_TwoGroup_BA_H_FDR.01/R1'
    },
    {
        'label': 'R2',
        'input_file': '../k2GenusSummary_R2/genusAverage.csv',
        'output_dir': '../Geni_Analyses_TwoGroup_BA_H_FDR.01/R2'
    }
]

# Significance Cutoff (Applied to FDR Adjusted P-value)
FDR_CUTOFF = 0.01
GROUP_COLORS = {'BA': 'red', 'H': 'green'}
HUE_ORDER = ['BA', 'H']
BOX_PROPS = {'alpha': 0.5, 'edgecolor': 'black'}

# ==========================================
# 2. Shared Functions
# ==========================================

def load_and_prep_data(input_file):
    """Loads data, maps sample names, assigns BA/H groups only."""
    try:
        genus_df = pd.read_csv(input_file)
        meta_df = pd.read_csv(META_FILE)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return None

    if 'Run' not in meta_df.columns or 'Sample Name' not in meta_df.columns:
        print("Error: Meta file missing columns.")
        return None
        
    run_map = dict(zip(meta_df['Run'], meta_df['Sample Name']))
    
    def get_run_id(ident):
        return str(ident).split('_')[0]

    genus_df['Run_ID'] = genus_df['Identifier'].apply(get_run_id)
    genus_df['Sample_Name'] = genus_df['Run_ID'].map(run_map)

    # Two-Group Assignment (BA and H only)
    def assign_group(name):
        if pd.isna(name): return None
        s = str(name)
        if re.match(r'^BA\d+$', s): return 'BA'
        if re.match(r'^H\d+$', s): return 'H'
        return None

    genus_df['Group'] = genus_df['Sample_Name'].apply(assign_group)
    analysis_df = genus_df.dropna(subset=['Group']).copy()
    
    return analysis_df

def compute_statistics(analysis_df):
    """Runs Mann-Whitney U test and applies FDR Correction."""
    results = []
    numeric_cols = analysis_df.select_dtypes(include=['number']).columns.tolist()
    metadata_cols = ['Identifier', 'Run_ID', 'Sample_Name', 'Group']
    genera_cols = [c for c in numeric_cols if c not in metadata_cols]

    for genus in genera_cols:
        ba = analysis_df[analysis_df['Group'] == 'BA'][genus]
        h = analysis_df[analysis_df['Group'] == 'H'][genus]
        
        mean_ba = ba.mean()
        mean_h = h.mean()
        
        if ba.sum() == 0 and h.sum() == 0:
            p_val = 1.0
        else:
            try: _, p_val = stats.mannwhitneyu(ba, h, alternative='two-sided')
            except: p_val = 1.0
        
        enriched_in = 'BA' if mean_ba > mean_h else 'H'

        results.append({
            'Genus': genus,
            'p_value': p_val,
            'Mean_BA': mean_ba,
            'Mean_H': mean_h,
            'Enriched_In': enriched_in
        })
    
    stats_df = pd.DataFrame(results)
    
    # --- FDR CORRECTION ---
    # Apply Benjamini-Hochberg
    if not stats_df.empty:
        _, stats_df['p_adj'], _, _ = multipletests(stats_df['p_value'], method='fdr_bh')
    else:
        stats_df['p_adj'] = 1.0
        
    # Sort by Adjusted P-value
    stats_df = stats_df.sort_values('p_adj')
    
    return stats_df

def generate_box_plot(df, genus_list, title, filename, output_dir):
    """Generates Box + Jitter plots for BA vs H (Alphabetical X)."""
    if not genus_list:
        print(f"  No genera found for: {title}")
        return

    print(f"  Generating plot: {title} ({len(genus_list)} genera)...")
    
    # Alphabetical Sort
    valid_genera = sorted([g for g in genus_list if g in df.columns])
    
    plot_data = df.melt(id_vars=['Group'], value_vars=valid_genera, 
                        var_name='Genus', value_name='Abundance')
    
    width = max(8, len(valid_genera) * 1.5)
    
    # --- Standard Scale ---
    plt.figure(figsize=(width, 8))
    sns.boxplot(x='Genus', y='Abundance', hue='Group', data=plot_data,
                palette=GROUP_COLORS, showfliers=False, boxprops=BOX_PROPS,
                order=valid_genera, hue_order=HUE_ORDER)
    
    sns.stripplot(x='Genus', y='Abundance', hue='Group', data=plot_data,
                  dodge=True, jitter=True, color='black', alpha=0.6, size=4,
                  order=valid_genera, hue_order=HUE_ORDER)
    
    plt.title(f'{title}\n(Significant, FDR < {FDR_CUTOFF})', fontsize=15)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel('Abundance')
    plt.legend(title='Group')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{filename}.png'), dpi=300)
    plt.close()

    # --- Log Scale ---
    plt.figure(figsize=(width, 8))
    plot_data['Abundance_Log'] = plot_data['Abundance'] + 0.1
    sns.boxplot(x='Genus', y='Abundance_Log', hue='Group', data=plot_data,
                palette=GROUP_COLORS, showfliers=False, boxprops=BOX_PROPS,
                order=valid_genera, hue_order=HUE_ORDER)
    
    sns.stripplot(x='Genus', y='Abundance_Log', hue='Group', data=plot_data,
                  dodge=True, jitter=True, color='black', alpha=0.6, size=4,
                  order=valid_genera, hue_order=HUE_ORDER)
    
    plt.yscale('log')
    plt.title(f'{title} (Log Scale)', fontsize=15)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel('Abundance (Log)')
    plt.legend(title='Group')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{filename}_log.png'), dpi=300)
    plt.close()

# ==========================================
# 3. Main Execution
# ==========================================
if __name__ == "__main__":
    
    stored_data = {}
    
    # --- Step 1: Individual R1/R2 Analysis ---
    for task in TASKS:
        label = task['label']
        print(f"\nProcessing BA vs H Analysis for {label}...")
        
        os.makedirs(task['output_dir'], exist_ok=True)
        
        # Load
        df = load_and_prep_data(task['input_file'])
        if df is None or df.empty:
            print(f"Skipping {label} due to data error.")
            continue
            
        print(f"  Samples: {df['Group'].value_counts().to_dict()}")

        # Stats (With FDR)
        stats_df = compute_statistics(df)
        stats_path = os.path.join(task['output_dir'], f'{label}_BA_vs_H_statistics_FDR.csv')
        stats_df.to_csv(stats_path, index=False)
        print(f"  Statistics saved to {stats_path}")
        
        stored_data[label] = {'df': df, 'stats': stats_df, 'output_dir': task['output_dir']}
        
        # Plot A: All Significant (FDR < 0.05)
        sig_all = stats_df[stats_df['p_adj'] < FDR_CUTOFF]['Genus'].tolist()
        generate_box_plot(df, sig_all, 
                          f"{label}: Significant Diff (BA vs H)", 
                          f"{label}_boxplot_significant_BA_H", 
                          task['output_dir'])
                          
        # Plot B: BA Enriched Only (FDR < 0.05)
        sig_ba = stats_df[
            (stats_df['p_adj'] < FDR_CUTOFF) & 
            (stats_df['Enriched_In'] == 'BA')
        ]['Genus'].tolist()
        generate_box_plot(df, sig_ba, 
                          f"{label}: BA Enriched (BA > H)", 
                          f"{label}_boxplot_significant_BA_enriched", 
                          task['output_dir'])

    # --- Step 2: Intersection Analysis (R1 ∩ R2) ---
    if 'R1' in stored_data and 'R2' in stored_data:
        print("\n" + "="*40)
        print("Calculating BA vs H Intersection (Significant in BOTH)")
        print("="*40)
        
        s1 = stored_data['R1']['stats']
        s2 = stored_data['R2']['stats']
        
        # Intersection: Any Significance (FDR < 0.05)
        set1_all = set(s1[s1['p_adj'] < FDR_CUTOFF]['Genus'])
        set2_all = set(s2[s2['p_adj'] < FDR_CUTOFF]['Genus'])
        intersect_all = list(set1_all.intersection(set2_all))
        
        # Intersection: BA Enriched in Both (FDR < 0.05)
        set1_ba = set(s1[(s1['p_adj'] < FDR_CUTOFF) & (s1['Enriched_In'] == 'BA')]['Genus'])
        set2_ba = set(s2[(s2['p_adj'] < FDR_CUTOFF) & (s2['Enriched_In'] == 'BA')]['Genus'])
        intersect_ba = list(set1_ba.intersection(set2_ba))
        
        print(f"Genera significant in BOTH: {len(intersect_all)}")
        print(f"Genera BA-Enriched in BOTH: {len(intersect_ba)}")
        
        # Save Intersection CSV
        int_df = pd.DataFrame({'Genus': intersect_all})
        int_df['BA_Enriched_In_Both'] = int_df['Genus'].isin(intersect_ba)
        
        # Add FDR P-values
        rank_map_1 = s1.set_index('Genus')['p_adj'].to_dict()
        rank_map_2 = s2.set_index('Genus')['p_adj'].to_dict()
        int_df['p_adj_R1'] = int_df['Genus'].map(rank_map_1)
        int_df['p_adj_R2'] = int_df['Genus'].map(rank_map_2)
        int_df = int_df.sort_values('p_adj_R1')
        
        # Save to parent folder
        out_csv = os.path.join(stored_data['R1']['output_dir'], '..', 'BA_vs_H_Intersection_List_FDR.csv')
        int_df.to_csv(out_csv, index=False)
        print(f"Intersection list saved to: {out_csv}")
        
        # Plot Intersection (Using R1 Data)
        generate_box_plot(stored_data['R1']['df'], intersect_all, 
                          "Intersection (BA vs H) - R1 Data", 
                          "R1_intersect_BA_H_all", 
                          stored_data['R1']['output_dir'])
                          
        generate_box_plot(stored_data['R1']['df'], intersect_ba, 
                          "Intersection (BA Enriched) - R1 Data", 
                          "R1_intersect_BA_enriched", 
                          stored_data['R1']['output_dir'])

        # Plot Intersection (Using R2 Data)
        generate_box_plot(stored_data['R2']['df'], intersect_all, 
                          "Intersection (BA vs H) - R2 Data", 
                          "R2_intersect_BA_H_all", 
                          stored_data['R2']['output_dir'])
                          
        generate_box_plot(stored_data['R2']['df'], intersect_ba, 
                          "Intersection (BA Enriched) - R2 Data", 
                          "R2_intersect_BA_enriched", 
                          stored_data['R2']['output_dir'])

    print("\nBA vs H Analysis (FDR Corrected) Complete.")
