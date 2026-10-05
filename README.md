# CGF-Kraken2DB-BA

Reproducible workflow for evaluating how fungal reference coverage changes shotgun-metagenomic signals in biliary atresia (BA), including construction of a human-associated fungal Kraken2 reference and reanalysis of public BioProject **PRJNA1305663**.

This repository supports the manuscript **“Human-associated fungal genomes rescue false-negative mycobiome signals in biliary atresia.”**

## Study logic

The project began as an independent attempt to replicate previously reported BA-associated *Aspergillus/Penicillium* signals using the standard Kraken2 fungal reference. Default-reference profiling showed a broad BA-skewed fungal signal but did not recover the expected genera. This discrepancy motivated expansion of the fungal reference space with cultivated gut fungi (CGF) and publicly available human-associated fungi (PHF), followed by a rebuilt non-enhanced control and read-level reassignment analysis.

The repository therefore contains two linked workflows:

1. **Fungal database construction**: CGF/PHF acquisition, FastANI screening and clustering, BUSCO QC, representative selection, taxonomy placement, and Kraken2 database construction.
2. **BA metagenomic analysis**: public SRA download, five independent 2-million-read subsamples per sample/read direction, Kraken2 classification, genus-level summaries, BA-versus-healthy statistics, direct confidence intervals, and read-level reassignment/Sankey analysis.

## Database configurations used in the manuscript

The historical directory suffixes are retained in the original scripts, but the manuscript terminology is:

| Legacy analysis name | Manuscript terminology | Observed genera |
|---|---|---:|
| no suffix | original/default Kraken2 fungal reference | 65 |
| `nFunDB` | CGF/PHF-enhanced fungal reference | 295 |
| `deFunDB` | locally rebuilt non-enhanced NCBI-derived control | 69 |

`pfFunDB` is an exploratory/intermediate analysis and is not one of the three final manuscript configurations.

## Repository structure

- `mkDB/` — entry point for the database-construction workflow.
- `scripts_GCF+PHF/` — clustering of the 1,210 CGF/PHF input genomes.
- `refCalibrationScripts/` — calibration/clustering of reference fungal genomes and taxonomy metadata.
- `CGFvsRefScripts/` — FastANI comparison of CGF/PHF genomes against the reference set; ANI >=95% is treated as already represented.
- `CGFNovelScripts/` — clustering/QC of putatively novel genomes, representative selection, phylogenetic placement, custom taxonomy, and final enhanced Kraken2 database construction.
- `PRJNA1305663/` — BA cohort metadata and downstream metagenomic analysis.
- `REPRODUCIBILITY.md` — database finalization evidence, environment snapshot, and final statistical validation targets.
- `requirements.txt` — Python package requirements used across the scripts.

## Input data

### Human-associated fungal genomes

The original workflow uses the CGF/PHF resources described in the database-construction scripts. The current build instructions begin in `mkDB/README.txt`.

The CGF metadata input `Table S2.xlsx` can be obtained from the supplementary archive associated with the source publication:

https://ars.els-cdn.com/content/image/1-s2.0-S0092867424004690-mmc1.zip

Save `Table S2.xlsx` into `./meta/` before running the relevant CGF acquisition scripts.

### Biliary atresia cohort

Public shotgun-metagenomic data are from NCBI BioProject **PRJNA1305663** (SRA study **SRP609322**). The analysis uses 50 BA and 40 healthy-control samples; group labels are derived from the exported sample-name structure in `PRJNA1305663/meta/meta.csv`.

## Reproducing the enhanced fungal database

Follow the scripts listed in:

```text
mkDB/README.txt
```

The workflow includes:

- CGF/PHF genome acquisition;
- ANI-based clustering at 95%;
- comparison with the reference fungal set;
- BUSCO QC using `fungi_odb10` with conditional `microsporidia_odb10` rescue;
- representative selection;
- taxonomic placement of novel representatives;
- custom taxids beginning at 3,000,000,000;
- generation of Kraken2-compatible taxonomy/FASTA files;
- final `kraken2-build` database construction.

The rebuilt non-enhanced database is a control constructed from the NCBI-derived fungal reference without addition of the novel human-associated representatives. It should not be confused with the older original/default Kraken2 fungal database used for the initial replication attempt.

## Reproducing the BA analysis

Follow:

```text
PRJNA1305663/README.txt
```

The original workflow analyzes R1 and R2 independently and averages five random 2-million-read subsampling iterations per sample/read direction.

The final statistical tables use:

- Mann-Whitney U tests;
- Benjamini-Hochberg false-discovery-rate correction;
- descriptive log2 fold change calculated as `log2[(mean BA + 0.1)/(mean healthy + 0.1)]`;
- rank-biserial correlation, `r = 2U/(nBA*nH) - 1`;
- 95% confidence intervals calculated directly from the observed sample distributions using DeLong structural-component variance for the equivalent AUC statistic, with `r = 2*AUC - 1` and ties counted as 0.5.

After the genus-average matrices are generated, run:

```bash
cd PRJNA1305663/working
python3 direct_ci_rank_biserial.py
python3 validate_final_results.py
```

The validation script checks the six final database/read-direction analyses and the manuscript values for *Penicillium* and *Aspergillus*.

## Read-level reassignment / Sankey analysis

The Sankey workflow compares the **locally rebuilt non-enhanced control** with the **CGF/PHF-enhanced database** in pooled high-*Penicillium* samples. It is not a comparison against the older original/default Kraken2 database.

The updated workflow:

1. derives the top five *Penicillium* samples separately from the enhanced R1 and R2 matrices;
2. pools those selected samples;
3. classifies pooled reads against the non-enhanced and enhanced databases;
4. verifies paired Kraken2 outputs by read identifier before tracing reassignment;
5. generates SankeyMATIC input for reads recovered as *Aspergillus* or *Penicillium* by the enhanced database.

## Reproducibility snapshot

The best-supported database finalization dates, analysis chronology, current software-environment snapshot, and final statistical validation targets are recorded in `REPRODUCIBILITY.md`.

Database dates are filesystem evidence and should not be interpreted as stronger historical provenance than the available metadata support.

## Software

Major external tools used by the workflow include Kraken2, FastANI, BUSCO, SRA Toolkit, seqtk, and pigz. Python dependencies are listed in `requirements.txt`.

## License

Code in this repository is released under the **MIT License**. See `LICENSE`.

## Contact

Hong-Hsing Liu, MD, PhD  
National Health Research Institutes, Taiwan
