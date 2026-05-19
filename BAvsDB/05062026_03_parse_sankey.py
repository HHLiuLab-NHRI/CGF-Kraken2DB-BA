#! /usr/bin/python3

import os

def process_sankey_data(def_report, enh_report, def_out, enh_out, output_file):
    print(f"Processing data for {os.path.basename(output_file)}...")
    
    # 1. Map target clades from the Enhanced Report
    target_clades = {"Aspergillus": set(), "Penicillium": set()}
    current_target = None
    target_indent = -1

    try:
        with open(enh_report, 'r') as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 6: continue
                
                taxid, name_field = parts[4], parts[5]
                indent = len(name_field) - len(name_field.lstrip())
                name = name_field.strip()

                if name in ["Aspergillus", "Penicillium"]:
                    current_target = name
                    target_indent = indent
                    target_clades[current_target].add(taxid)
                elif current_target is not None:
                    if indent > target_indent:
                        target_clades[current_target].add(taxid)
                    else:
                        current_target = None
    except FileNotFoundError:
        print(f"  -> Error: Could not find {enh_report}")
        return

    # 2. Map readable names from the Default Report
    taxid_to_name = {'0': 'Unclassified (Default DB)'}
    try:
        with open(def_report, 'r') as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 6: continue
                taxid_to_name[parts[4]] = f"{parts[5].strip()} (Default DB)"
    except FileNotFoundError:
        print(f"  -> Error: Could not find {def_report}")
        return

    # 3. Trace the transitions
    print("  -> Cross-referencing 10 million reads... please wait.")
    transitions = {}
    try:
        with open(def_out, 'r') as f_def, open(enh_out, 'r') as f_enh:
            for line_def, line_enh in zip(f_def, f_enh):
                parts_def = line_def.split('\t')
                parts_enh = line_enh.split('\t')
                if len(parts_def) < 3 or len(parts_enh) < 3: continue
                
                tax_def = parts_def[2]
                tax_enh = parts_enh[2]
                
                target_genus = None
                if tax_enh in target_clades["Aspergillus"]: target_genus = "Aspergillus (Enhanced DB)"
                elif tax_enh in target_clades["Penicillium"]: target_genus = "Penicillium (Enhanced DB)"
                    
                if target_genus:
                    if tax_def not in transitions: transitions[tax_def] = {}
                    if target_genus not in transitions[tax_def]: transitions[tax_def][target_genus] = 0
                    transitions[tax_def][target_genus] += 1
    except FileNotFoundError as e:
        print(f"  -> Error reading output files: {e}")
        return

    # 4. Write SankeyMATIC syntax directly to the output file
    with open(output_file, 'w') as out_f:
        out_f.write(f"// SankeyMATIC data for {os.path.basename(output_file)}\n")
        for old_taxid, new_targets in transitions.items():
            source_name = taxid_to_name.get(old_taxid, f"TaxID {old_taxid} (Default DB)")
            for new_genus, count in new_targets.items():
                if count > 5: # Filter out 1-off random noise
                    out_f.write(f"{source_name} [{count}] {new_genus}\n")
    
    print(f"  -> Success! Results saved to {output_file}\n")


if __name__ == "__main__":
    # Common directory where everything is saved
    base_dir = "../sankey/"
    
    # Run for Read 1
    process_sankey_data(
        def_report=f"{base_dir}default_R1_report.txt",
        enh_report=f"{base_dir}enhanced_R1_report.txt",
        def_out=f"{base_dir}default_R1.txt",
        enh_out=f"{base_dir}enhanced_R1.txt",
        output_file=f"{base_dir}sankey_R1_final.txt"
    )

    # Run for Read 2
    process_sankey_data(
        def_report=f"{base_dir}default_R2_report.txt",
        enh_report=f"{base_dir}enhanced_R2_report.txt",
        def_out=f"{base_dir}default_R2.txt",
        enh_out=f"{base_dir}enhanced_R2.txt",
        output_file=f"{base_dir}sankey_R2_final.txt"
    )
