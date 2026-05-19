#!/usr/bin/env python3
import pandas as pd
import os
import sys
import time
from ete3 import NCBITaxa
from Bio import Entrez

# ================= CONFIGURATION =================
# INPUTS
NOVEL_LIST = "../CGFNovelResults/final_validated_representatives.tsv"
FASTANI_FILE = "../CGFvsRefResults/CGFvsRefSeq_merged.tsv"
OUTPUT_FILE = "../CGFNovelResults/novel_taxonomy_assignments.tsv"

# EMAIL REQUIRED FOR NCBI LOOKUP
# (NCBI requires an email to use their API. Replace with yours or keep this dummy one)
Entrez.email = "your_email@example.com" 

# THRESHOLDS
THR_GENUS_ANI = 80.0
THR_FAMILY_ANI = 70.0
MIN_COVERAGE = 0.25
# =================================================

def fetch_taxid_from_ncbi(accession_id):
    """
    Uses Bio.Entrez to look up the TaxID for a given Assembly Accession.
    """
    try:
        # Search the Assembly DB for the accession
        handle = Entrez.esearch(db="assembly", term=accession_id, retmode="xml")
        record = Entrez.read(handle)
        handle.close()
        
        if not record['IdList']:
            return None
            
        id_list = record['IdList'][0]
        
        # Fetch details to get TaxID
        handle = Entrez.esummary(db="assembly", id=id_list, report="full")
        summary = Entrez.read(handle)
        handle.close()
        
        # Extract Taxid
        return int(summary['DocumentSummarySet']['DocumentSummary'][0]['Taxid'])
        
    except Exception as e:
        print(f"   [API Error] Could not fetch TaxID for {accession_id}: {e}")
        return None

def get_parent_taxid(ref_taxid, ani_score, coverage, ncbi):
    """
    Decides Parent TaxID based on ANI AND Coverage.
    """
    try:
        lineage = ncbi.get_lineage(ref_taxid)
        ranks = ncbi.get_rank(lineage) 
        rank_map = {v: k for k, v in ranks.items()}
        
        # LOGIC: High ANI + Good Coverage = Genus Match
        if ani_score >= THR_GENUS_ANI and coverage >= MIN_COVERAGE:
            if 'genus' in rank_map: return rank_map['genus'], 'genus'
            elif 'family' in rank_map: return rank_map['family'], 'family'

        # LOGIC: High ANI but Low Coverage OR Moderate ANI = Family Match
        elif ani_score >= THR_FAMILY_ANI:
            if 'family' in rank_map: return rank_map['family'], 'family'
            elif 'order' in rank_map: return rank_map['order'], 'order'
                
        # LOGIC: Distant Match
        else:
            if 'order' in rank_map: return rank_map['order'], 'order'
            elif 'class' in rank_map: return rank_map['class'], 'class'
                
        return 4751, 'kingdom'
    except:
        return 4751, 'kingdom'

def clean_name(filename):
    base = os.path.basename(str(filename))
    for ext in ['.gz', '.fna', '.fasta', '.fa']:
        if base.endswith(ext):
            base = base[:-len(ext)]
    return base

def main():
    print("--- Phase 2: Phylogenomic Placement (FastANI + Entrez Lookup) ---")
    
    # 1. Load NCBI Taxonomy Tree (local)
    print("Loading local taxonomy tree...")
    ncbi = NCBITaxa()

    # 2. Load Novel List
    print(f"Loading Novel List: {NOVEL_LIST}")
    try:
        novel_df = pd.read_csv(NOVEL_LIST, sep='\t')
        novel_map = {}
        for idx, row in novel_df.iterrows():
            clean = clean_name(row['representative'])
            novel_map[clean] = row['novel_species_id']
    except Exception as e:
        print(f"Error loading novel list: {e}")
        sys.exit(1)

    # 3. Load FastANI
    print(f"Loading FastANI Results: {FASTANI_FILE}")
    try:
        # Robust load (check headers)
        header_check = pd.read_csv(FASTANI_FILE, sep='\t', nrows=5)
        cols_lower = [c.lower() for c in header_check.columns]
        
        if 'ani' in cols_lower and 'query' in cols_lower:
            ani_df = pd.read_csv(FASTANI_FILE, sep='\t')
            # Normalize headers
            rename_map = {'query': 'Query', 'reference': 'Ref', 'ani': 'ANI', 
                          'fragments_mapped': 'FragMap', 'fragments_total': 'TotalFrag'}
            ani_df.rename(columns=str.lower, inplace=True)
            ani_df.rename(columns=rename_map, inplace=True)
        else:
            ani_df = pd.read_csv(FASTANI_FILE, sep='\t', names=['Query', 'Ref', 'ANI', 'FragMap', 'TotalFrag'])
            
    except Exception as e:
        print(f"Error loading FastANI file: {e}")
        sys.exit(1)

    # 4. Clean and Filter
    # Ensure numeric
    ani_df['ANI'] = pd.to_numeric(ani_df['ANI'], errors='coerce')
    ani_df['FragMap'] = pd.to_numeric(ani_df['FragMap'], errors='coerce')
    ani_df['TotalFrag'] = pd.to_numeric(ani_df['TotalFrag'], errors='coerce')
    ani_df.dropna(subset=['ANI'], inplace=True)

    # Coverage
    if 'TotalFrag' in ani_df.columns:
        ani_df['Coverage'] = ani_df.apply(lambda x: x['FragMap'] / x['TotalFrag'] if x['TotalFrag'] > 0 else 0, axis=1)
    else:
        ani_df['Coverage'] = 1.0

    ani_df['Query_Clean'] = ani_df['Query'].apply(clean_name)
    ani_df['Ref_Clean'] = ani_df['Ref'].apply(clean_name)

    # Filter for novel
    target_ani = ani_df[ani_df['Query_Clean'].isin(novel_map.keys())].copy()
    
    # Sort and pick Best Hits
    target_ani['Score_Metric'] = target_ani['ANI'] * target_ani['Coverage']
    best_hits = target_ani.sort_values('Score_Metric', ascending=False).drop_duplicates('Query_Clean')
    
    print(f"Found {len(best_hits)} best hits. Resolving TaxIDs via NCBI Entrez...")
    print("   (This takes ~1 second per genome. Please wait...)")

    results = []
    
    # Cache to avoid re-fetching same reference
    ref_taxid_cache = {}

    for i, (_, row) in enumerate(best_hits.iterrows()):
        query_clean = row['Query_Clean']
        ref_clean = row['Ref_Clean']
        ani = row['ANI']
        cov = row['Coverage']
        cluster_id = novel_map.get(query_clean, "Unknown")
        
        # Extract Accession (GCF_...)
        parts = ref_clean.split('_')
        if len(parts) >= 2 and parts[0] in ['GCA', 'GCF']:
            acc = f"{parts[0]}_{parts[1].split('.')[0]}" 
        else:
            acc = ref_clean

        # --- THE FIX: WEB LOOKUP ---
        if acc in ref_taxid_cache:
            taxid = ref_taxid_cache[acc]
        else:
            print(f"   [{i+1}/{len(best_hits)}] Looking up {acc}...", end="\r")
            taxid = fetch_taxid_from_ncbi(acc)
            if taxid:
                ref_taxid_cache[acc] = taxid
            else:
                ref_taxid_cache[acc] = None # Mark as failed
            time.sleep(0.35) # Be nice to NCBI API

        # Resolve Lineage
        parent_id = 4751
        rank = "kingdom (fallback)"
        parent_name = "Fungi"

        if taxid:
            try:
                parent_id, rank = get_parent_taxid(taxid, ani, cov, ncbi)
                name_dict = ncbi.get_taxid_translator([parent_id])
                if name_dict: parent_name = name_dict[parent_id]
            except:
                pass

        results.append({
            'Novel_Cluster': cluster_id,
            'Query_Genome': query_clean,
            'Best_Ref': ref_clean,
            'Ref_Accession': acc,
            'ANI': ani,
            'Coverage': round(cov, 3),
            'Parent_TaxID': parent_id,
            'Parent_Rank': rank,
            'Parent_Name': parent_name
        })

    # 5. Save
    hits_df = pd.DataFrame(results)
    
    # Merge with full list
    final_output = []
    for clean_rep, cluster_id in novel_map.items():
        if not hits_df.empty:
            hit = hits_df[hits_df['Novel_Cluster'] == cluster_id]
        else:
            hit = pd.DataFrame()
            
        if not hit.empty:
            final_output.append(hit.iloc[0].to_dict())
        else:
            final_output.append({
                'Novel_Cluster': cluster_id,
                'Query_Genome': clean_rep,
                'Best_Ref': "None",
                'ANI': 0.0,
                'Coverage': 0.0,
                'Parent_TaxID': 4751,
                'Parent_Rank': 'kingdom',
                'Parent_Name': 'Fungi'
            })

    out_df = pd.DataFrame(final_output)
    out_df.to_csv(OUTPUT_FILE, sep='\t', index=False)
    print(f"\n\nTaxonomy assignment complete. Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
