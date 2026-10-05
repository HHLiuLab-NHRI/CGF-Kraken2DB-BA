# Reproducibility snapshot

This repository includes the scripts used to construct and analyze the three fungal reference configurations in the manuscript. The notes below distinguish contemporaneous analysis outputs from conclusions established later during a retrospective audit of the archived build tree.

## Database mapping

| Manuscript configuration | Historical analysis suffix | Best-supported finalization date |
|---|---|---|
| Original/default Kraken2 fungal reference | no suffix | 2024-07-11 |
| CGF-enhanced fungal reference | `nFunDB` | 2026-04-10 |
| Locally rebuilt non-enhanced NCBI-derived control | `deFunDB` | 2026-04-15 |

The dates above are based on filesystem evidence from the database files and build markers captured from the analysis workstation. They should be interpreted as best-supported finalization dates rather than stronger provenance claims.

## Retrospective audit of the historical enhanced-database build

During preparation of the manuscript/repository reproducibility materials, the archived `prFungiDB` project tree, intermediate tables, BUSCO summaries, and final database-library contents were audited against the public scripts.

The audit established the following historical path:

1. The source accession sets contained **708 cultivated gut fungal (CGF) genomes** and **502 publicly available human-associated fungal (PHF) genomes**, with no overlap: **1,210 genomes total**.
2. The initial FastANI file list contained all **1,210 genomes (708 CGF + 502 PHF)**.
3. The later RefSeq novelty-screening query list contained **708 genomes, all CGF**. PHF genomes did not enter this screening stage.
4. The 708-genome assignment table contained:
   - 395 `Assigned`;
   - 2 `Conflict` (ANI >=95% to more than one reference species cluster);
   - 281 `Novel`;
   - 30 `Novel (No Hits)`.
   Thus **311 CGF genomes** proceeded as putatively novel candidates.
5. The 311 candidates formed **131 ANI clusters**, of which 63 had more than one member.
6. Final filtering retained **128 representatives**, all recorded as `Fungi` in the archived final validation table.
7. The RefSeq-derived baseline contained **665 representatives**.
8. The formatted enhanced database contained **665 RefSeq-derived + 128 CGF-derived = 793 source FASTA entries**.

Accordingly, the final enhanced database used for the BA analysis should be described as **CGF-enhanced** (or, more generally, human-associated-fungal enhanced), not as a database containing both CGF- and PHF-derived novel representatives. The earlier shorthand `CGF/PHF-enhanced` is retained only where needed to explain historical directory or project naming.

### BUSCO representative-handling audit

The archived representative-selection script (`CGFNovelScripts/12092025_08_select_representatives.py`) ranks genomes within each novel cluster by fungal BUSCO completeness (descending) and then fragmentation (ascending). The downstream refinement script (`CGFNovelScripts/12092025_09_refine_and_filter.py`), however, resolves the sequence path from the row's pre-existing `representative` field rather than from the BUSCO-ranked row's `genome_filename` field.

In the archived output, these fields differed in **34 of 131 clusters**. Therefore, in those 34 clusters, the sequence carried forward was the preassigned cluster representative rather than the genome associated with the highest BUSCO-based ranking stored on that selected row.

A direct retrospective check of the archived fungi_odb10 BUSCO summaries for the 34 sequences actually carried forward showed that **all 34 had fungal BUSCO completeness >=50%**; none failed the fungal completeness threshold used for final retention. No BUSCO summary was missing for these checks.

This distinction affects the description of representative selection and provenance, but it does not change which historical database was used for the reported BA analysis. The historical scripts are preserved rather than silently modified because substituting BUSCO-top-ranked sequences would define a different Kraken2 database and would require a full reanalysis.

The current software snapshot reports BUSCO 5.5.0, but this is not asserted to be the exact BUSCO version used during the historical build unless independently recovered from the archived BUSCO logs.

## Analysis chronology

The default-reference genus-average matrices were produced on 2025-12-23, the enhanced-reference matrices on 2026-04-14, and the rebuilt non-enhanced control matrices on 2026-04-15. This sequence is consistent with the study history: the default-reference replication attempt preceded the enhanced-reference analysis, followed by the rebuilt non-enhanced control.

## Software environment snapshot

The following versions were installed when reproducibility metadata were collected on 2026-10-05:

- Kraken2 / kraken2-build: 2.1.3
- FastANI: 1.33
- BUSCO: 5.5.0
- SRA Toolkit: 3.2.1
- pigz: 2.8
- Python: 3.12.3
- NumPy: 1.26.4
- pandas: 2.1.4
- SciPy: 1.11.4
- statsmodels: 0.14.1
- Biopython: 1.83

These are a current environment snapshot, not definitive evidence that every package had the same version at the time each database was constructed.

The taxonomy-placement script also requires `ete3`; its historical version was not recoverable from the environment snapshot and is therefore not asserted.

## Final statistical validation targets

`PRJNA1305663/working/direct_ci_rank_biserial.py` and `PRJNA1305663/working/validate_final_results.py` reproduce and verify the final manuscript statistics.

Expected numbers of tested genera and genera at FDR <0.01:

| Database | R1 tested / significant | R2 tested / significant |
|---|---:|---:|
| Default | 65 / 11 | 65 / 8 |
| Enhanced | 295 / 27 | 295 / 23 |
| Non-enhanced | 69 / 11 | 69 / 7 |

Key enhanced-reference results:

- Penicillium R1: FDR 0.0076; rank-biserial r 0.420; 95% CI 0.206 to 0.634.
- Penicillium R2: FDR 0.0082; rank-biserial r 0.423; 95% CI 0.208 to 0.637.
- Aspergillus R1: FDR 0.0455; rank-biserial r 0.333; 95% CI 0.104 to 0.562.
- Aspergillus R2: FDR 0.0485; rank-biserial r 0.321; 95% CI 0.090 to 0.552.

Confidence intervals use DeLong structural-component variance for the equivalent AUC statistic and transform via `r = 2*AUC - 1`, with ties assigned half credit.
