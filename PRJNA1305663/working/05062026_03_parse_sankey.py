#!/usr/bin/env python3

from collections import Counter
from itertools import zip_longest
from pathlib import Path

TARGETS = ("Aspergillus", "Penicillium")


def collect_target_taxids(report_path):
    target_clades = {target: set() for target in TARGETS}
    current_target = None
    target_indent = -1

    with open(report_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            taxid, name_field = parts[4], parts[5]
            indent = len(name_field) - len(name_field.lstrip())
            name = name_field.strip()

            if name in TARGETS:
                current_target = name
                target_indent = indent
                target_clades[current_target].add(taxid)
            elif current_target is not None:
                if indent > target_indent:
                    target_clades[current_target].add(taxid)
                else:
                    current_target = None

    return target_clades


def taxid_name_map(report_path):
    names = {"0": "Unclassified (Non-enhanced DB)"}
    with open(report_path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 6:
                names[parts[4]] = f"{parts[5].strip()} (Non-enhanced DB)"
    return names


def process_sankey_data(nonenh_report, enhanced_report, nonenh_out, enhanced_out, output_file):
    print(f"Processing {output_file}...")
    target_clades = collect_target_taxids(enhanced_report)
    names = taxid_name_map(nonenh_report)
    transitions = Counter()
    aligned_reads = 0

    with open(nonenh_out) as old_handle, open(enhanced_out) as new_handle:
        for line_number, (old_line, new_line) in enumerate(
            zip_longest(old_handle, new_handle), start=1
        ):
            if old_line is None or new_line is None:
                raise RuntimeError(
                    "Kraken2 output lengths differ; read-by-read reassignment cannot be aligned safely."
                )

            old = old_line.rstrip("\n").split("\t")
            new = new_line.rstrip("\n").split("\t")
            if len(old) < 3 or len(new) < 3:
                raise RuntimeError(f"Malformed Kraken2 output at line {line_number}")
            if old[1] != new[1]:
                raise RuntimeError(
                    f"Read-ID mismatch at line {line_number}: {old[1]!r} != {new[1]!r}"
                )

            aligned_reads += 1
            old_taxid, new_taxid = old[2], new[2]
            target = None
            if new_taxid in target_clades["Aspergillus"]:
                target = "Aspergillus (Enhanced DB)"
            elif new_taxid in target_clades["Penicillium"]:
                target = "Penicillium (Enhanced DB)"

            if target is not None:
                transitions[(old_taxid, target)] += 1

    with open(output_file, "w") as out:
        out.write(f"// {aligned_reads} aligned reads checked\n")
        out.write(f"// SankeyMATIC data for {Path(output_file).name}\n")
        for (old_taxid, target), count in transitions.most_common():
            if count > 5:
                source = names.get(old_taxid, f"TaxID {old_taxid} (Non-enhanced DB)")
                out.write(f"{source} [{count}] {target}\n")

    print(f"  -> checked {aligned_reads} aligned reads")
    print(f"  -> saved {output_file}\n")


if __name__ == "__main__":
    base = Path("../sankey")
    for read in ("R1", "R2"):
        process_sankey_data(
            base / f"nonenhanced_{read}_report.txt",
            base / f"enhanced_{read}_report.txt",
            base / f"nonenhanced_{read}.txt",
            base / f"enhanced_{read}.txt",
            base / f"sankey_{read}_final.txt",
        )
