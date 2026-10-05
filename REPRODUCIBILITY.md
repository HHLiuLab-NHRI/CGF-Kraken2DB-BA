# Reproducibility snapshot

This repository includes the scripts used to construct and analyze the three fungal reference configurations in the manuscript. The database-construction accounting below is based on the archived project outputs and final database-library contents.

## Database mapping

| Manuscript configuration | Historical analysis suffix | Best-supported finalization date |
|---|---|---|
| Original/default Kraken2 fungal reference | no suffix | 2024-07-11 |
| CGF-enhanced fungal reference | `nFunDB` | 2026-04-10 |
| Locally rebuilt non-enhanced NCBI-derived control | `deFunDB` | 2026-04-15 |

The dates above are based on filesystem evidence from the database files and build markers captured from the analysis workstation. They should be interpreted as best-supported finalization dates rather than stronger provenance claims.

## Enhanced-database construction accounting

The archived project outputs establish the following database-construction path:

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
6. Final quality control retained **128 representatives** and excluded 3.
7. The RefSeq-derived baseline contained **665 fungal genomes**.
8. The formatted enhanced database contained **665 RefSeq-derived + 128 CGF-derived = 793 source FASTA entries**.

Accordingly, the final enhanced database used for the BA analysis should be described as **CGF-enhanced** (or, more generally, human-associated-fungal enhanced), not as a database containing both CGF- and PHF-derived novel representatives.

## Representative selection and BUSCO quality control

ANI >=95% defined the putatively novel genome clusters. Within each ANI-defined cluster, one deterministic representative was selected as the **lexicographically first genome accession/filename** in that cluster. BUSCO did not determine representative identity; it was used to assess the quality of the selected representative.

The selected representative was retained when `fungi_odb10` BUSCO completeness was >=50%. Representatives below this threshold were evaluated with `microsporidia_odb10` and retained only if completeness was >=65%. Of the 131 ANI-cluster representatives, **128 passed final QC and 3 were excluded**. The archived final validation table records all 128 retained representatives as `Fungi`.

The current software snapshot reports BUSCO 5.5.0. This is a current-environment value and is not asserted to be the exact BUSCO executable version used during every historical database-construction step.

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
