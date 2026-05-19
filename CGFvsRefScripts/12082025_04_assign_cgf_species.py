#!/usr/bin/env python3
import pandas as pd
import os
import sys

"""
Script to assign CGF genomes to Reference Species based on FastANI results.
Logic:
  1. Load the MASTER list of queries (to ensure genomes with 0 hits are not lost).
  2. Filter FastANI hits with ANI >= 95%.
  3. Map reference genomes to their Species Cluster IDs.
  4. Assign species if matches are unambiguous.
  5. Flag 'Conflict' if matching multiple clusters > 95%.
  6. Flag 'Novel' if no matches > 95% (or no hits at all).
"""

# ---------------------------------------------------------
# Configuration / Paths
# ---------------------------------------------------------
REF_CLUSTERS_FILE = "../refCalibrationResults/clusters/ref_components_members_with_ncbi.tsv"
FASTANI_FILE      = "../CGFvsRefResults/CGFvsRefSeq_merged.tsv"
OUT_FILE          = "../CGFvsRefResults/CGF_species_assignment.tsv"
SUMMARY_FILE      = "../CGFvsRefResults/CGF_assignment_summary.txt"

# NEW: Path to the original file list to ensure we track all inputs
CGF_FILELIST      = "../CGFvsRefResults/filelist_cgf.txt"

ANI_THRESHOLD = 95.0

def main():
    # -------------------------------------------------------
    # 1. Load Reference Definitions
    # -------------------------------------------------------
    print(f"[INFO] Loading reference definitions from: {REF_CLUSTERS_FILE}")
    try:
        df_ref = pd.read_csv(REF_CLUSTERS_FILE, sep='\t')
    except FileNotFoundError:
        print(f"[ERROR] File not found: {REF_CLUSTERS_FILE}")
        sys.exit(1)

    # Create mapping dictionaries
    df_ref['member_basename'] = df_ref['member_basename'].str.strip()
    ref_file_to_cluster = df_ref.set_index('member_basename')['cluster_id'].to_dict()
    cluster_to_name = df_ref.groupby('cluster_id')['organism_name'].first().to_dict()

    # -------------------------------------------------------
    # 2. Load the Master Query List (The Fix for Silent Loss)
    # -------------------------------------------------------
    print(f"[INFO] Loading original CGF file list from: {CGF_FILELIST}")
    try:
        with open(CGF_FILELIST, 'r') as f:
            # We only need the basename (e.g., GCA_123.fna.gz) to match the FastANI output
            master_queries = [os.path.basename(line.strip()) for line in f if line.strip()]
        print(f"[INFO] Total query genomes to process: {len(master_queries)}")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {CGF_FILELIST}")
        print("       Please ensure 12052025_00_prepare_cgf_filelist.py was run.")
        sys.exit(1)

    # -------------------------------------------------------
    # 3. Load FastANI Results
    # -------------------------------------------------------
    print(f"[INFO] Loading FastANI results from: {FASTANI_FILE}")
    try:
        df_ani = pd.read_csv(FASTANI_FILE, sep='\t')
    except FileNotFoundError:
        print(f"[ERROR] File not found: {FASTANI_FILE}")
        sys.exit(1)

    # Clean up columns to get basenames
    df_ani['query_basename'] = df_ani['query'].apply(os.path.basename)
    df_ani['ref_basename'] = df_ani['reference'].apply(os.path.basename)

    # Filter for valid hits based on ANI threshold (>= 95%)
    df_hits = df_ani[df_ani['ani'] >= ANI_THRESHOLD].copy()
    
    # Map the reference genome in the hit to its cluster
    df_hits['ref_cluster'] = df_hits['ref_basename'].map(ref_file_to_cluster)

    # -------------------------------------------------------
    # 4. Process Assignments
    # -------------------------------------------------------
    print("[INFO] Processing assignments...")
    results = []
    
    # Iterate over the MASTER LIST, not the FastANI results list
    for query in master_queries:
        
        # Check if we have high-quality hits for this query
        my_hits = df_hits[df_hits['query_basename'] == query]
        
        # -------------------------------------------------------
        # CASE 1: NO HITS >= 95% (NOVEL or NO MATCH)
        # -------------------------------------------------------
        if len(my_hits) == 0:
            # Check if it exists in the raw FastANI output at all (i.e. low ANI hits)
            all_my_hits = df_ani[df_ani['query_basename'] == query]
            
            if not all_my_hits.empty:
                # It has hits, but they are all < 95%
                best_hit = all_my_hits.sort_values('ani', ascending=False).iloc[0]
                max_ani = best_hit['ani']
                best_ref = os.path.basename(best_hit['reference'])
                best_cluster = ref_file_to_cluster.get(best_ref, "Unknown_Ref")
                status_label = 'Novel'
            else:
                # It is TOTALLY MISSING from FastANI output (0 hits / < 10% coverage)
                # This catches the "Silent Loss" genomes
                max_ani = 0.0
                best_cluster = "None"
                status_label = 'Novel (No Hits)'

            results.append({
                'query_genome': query,
                'assigned_species_id': "Novel_Species",
                'assigned_species_name': "Unassigned",
                'status': status_label,
                'matched_clusters': "",
                'max_ani': max_ani,
                'best_match_cluster': best_cluster
            })
            continue

        # -------------------------------------------------------
        # CASE 2: HITS FOUND >= 95% -> CHECK FOR CONFLICTS
        # -------------------------------------------------------
        # Check which unique clusters were matched
        matched_clusters = my_hits['ref_cluster'].dropna().unique()
        matched_clusters = sorted(matched_clusters)
        max_ani = my_hits['ani'].max()
        
        if len(matched_clusters) == 0:
            # Reference genome exists in FastANI but not in our Cluster Definition file
            results.append({
                'query_genome': query,
                'assigned_species_id': "Error",
                'assigned_species_name': "Ref_Not_Found_In_DB",
                'status': 'Error',
                'matched_clusters': "",
                'max_ani': max_ani,
                'best_match_cluster': "Unknown"
            })
            
        elif len(matched_clusters) == 1:
            # Unambiguous assignment
            cluster_id = matched_clusters[0]
            name = cluster_to_name.get(cluster_id, "Unknown Name")
            
            results.append({
                'query_genome': query,
                'assigned_species_id': cluster_id,
                'assigned_species_name': name,
                'status': 'Assigned',
                'matched_clusters': cluster_id,
                'max_ani': max_ani,
                'best_match_cluster': cluster_id
            })
            
        else:
            # Conflict: Matches multiple distinct reference clusters > 95%
            cluster_str = ";".join(matched_clusters)
            results.append({
                'query_genome': query,
                'assigned_species_id': "Ambiguous",
                'assigned_species_name': "Ambiguous",
                'status': 'Conflict',
                'matched_clusters': cluster_str,
                'max_ani': max_ani,
                'best_match_cluster': cluster_str
            })

    # -------------------------------------------------------
    # 5. Save Results
    # -------------------------------------------------------
    df_results = pd.DataFrame(results)
    
    # Reorder columns
    cols = ['query_genome', 'assigned_species_id', 'assigned_species_name', 
            'status', 'max_ani', 'matched_clusters', 'best_match_cluster']
    df_results = df_results[cols]

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    df_results.to_csv(OUT_FILE, sep='\t', index=False)
    
    print("-" * 40)
    print(f"[DONE] Results saved to: {OUT_FILE}")
    
    # -----------------------------------------------------
    # 6. Save Summary
    # -----------------------------------------------------
    summary_counts = df_results['status'].value_counts().rename('Count')
    summary_df = summary_counts.to_frame()
    
    # Add a Total row to verify no data loss
    total_count = summary_df['Count'].sum()
    
    summary_output = "Summary of Assignments:\n"
    summary_output += summary_df.to_string() + "\n"
    summary_output += "-" * 20 + "\n"
    summary_output += f"Total Processed: {total_count}\n"
    
    # Save the summary to file
    with open(SUMMARY_FILE, 'w') as f:
        f.write(summary_output)
        
    print(f"[DONE] Assignment summary saved to: {SUMMARY_FILE}")
    print("-" * 40)
    print(summary_output)
    print("-" * 40)

if __name__ == "__main__":
    main()
