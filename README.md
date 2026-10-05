# CGF-Kraken2DB-BA

Reproducible workflow for evaluating how fungal reference coverage changes shotgun-metagenomic signals in biliary atresia (BA), including construction of a cultivated-gut-fungi (CGF)-enhanced Kraken2 reference and reanalysis of public BioProject **PRJNA1305663**.

This repository supports the manuscript **“Human-associated fungal genomes rescue false-negative mycobiome signals in biliary atresia.”**

## Study logic

The project began as an independent attempt to replicate previously reported BA-associated *Aspergillus/Penicillium* signals using the standard Kraken2 fungal reference. Default-reference profiling showed a broad BA-skewed fungal signal but did not recover the expected genera. This discrepancy motivated expansion of the fungal reference space with human-associated fungal genomes, followed by a rebuilt non-enhanced control and read-level reassignment analysis.

The archived database-development project initially assembled two human-associated fungal resources: 708 cultivated gut fungal (CGF) genomes and 502 publicly available human-associated fungal (PHF) genomes (1,210 genomes total). These 1,210 genomes were examined in an initial ANI-based clustering stage. The database-expansion pipeline then screened the **708 CGF genomes** against the RefSeq fungal baseline. PHF genomes did not enter that RefSeq novelty-screening step and did not contribute representatives to the final enhanced database.

The repository therefore contains two linked workflows:

1. **Fungal database construction**: CGF/PHF acquisition and initial clustering, RefSeq baseline construction, CGF-versus-RefSeq screening, novel-CGF clustering, deterministic representative selection, BUSCO QC, taxonomy placement, and Kraken2 database construction.
2. **BA metagenomic analysis**: public SRA download, five independent 2-million-read subsamples per sample/read direction, Kraken2 classification, genus-level summaries, BA-versus-healthy statistics, direct confidence intervals, and read-level reassignment/Sankey analysis.

## Database configurations used in the manuscript

The historical directory suffixes are retained in the original scripts, but the final analysis mapping is:

| Legacy analysis name | Description | Observed genera |
|---|---|---:|
| no suffix | original/default Kraken2 fungal reference | 65 |
| `nFunDB` | CGF-enhanced fungal reference | 295 |
| `deFunDB` | locally rebuilt non-enhanced NCBI-derived control | 69 |

`pfFunDB` is an exploratory/intermediate analysis and is not one of the three final manuscript configurations.

## Repository structure

- `mkDB/` — entry point for the database-construction workflow.
- `scripts_GCF+PHF/` — initial ANI-based clustering of the 1,210-genome CGF+PHF catalog.
- `refCalibrationScripts/` — calibration/clustering of reference fungal genomes and taxonomy metadata.
- `CGFvsRefScripts/` — FastANI comparison of the 708 CGF genomes against the RefSeq-derived reference set; ANI >=95% is treated as represented at the species-cluster level.
- `CGFNovelScripts/` — clustering/QC of putatively novel CGF genomes, representative handling, phylogenetic placement, custom taxonomy, and final enhanced Kraken2 database construction.
- `PRJNA1305663/` — BA cohort metadata and downstream metagenomic analysis.
- `REPRODUCIBILITY.md` — database construction accounting, environment snapshot, and final statistical validation targets.
- `requirements.txt` — Python package requirements used across the scripts.

## Input data

### Human-associated fungal genomes

The workflow downloaded 708 CGF accessions and 502 PHF accessions. The combined 1,210-genome catalog was used for an initial clustering analysis. The final enhanced Kraken2 database, however, was constructed from the CGF branch of the workflow: 708 CGF genomes were screened against the RefSeq baseline, 311 lacked an ANI >=95% species-level match, and 128 quality-controlled representatives were ultimately added to the database.

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

- acquisition of 708 CGF and 502 PHF genomes;
- initial ANI-based clustering of the combined 1,210-genome catalog;
- construction/calibration of the RefSeq fungal baseline;
- **CGF-only** screening against that baseline at ANI >=95%;
- clustering of the 311 putatively novel CGF genomes into 131 ANI clusters;
- deterministic representative selection as the lexicographically first accession/filename within each ANI cluster;
- BUSCO quality control of the selected representatives;
- final retention of 128 representatives;
- taxonomic placement of retained representatives;
- custom taxids beginning at 3,000,000,000;
- generation of Kraken2-compatible taxonomy/FASTA files;
- final `kraken2-build` database construction.

For representative QC, `fungi_odb10` BUSCO completeness >=50% is retained. Representatives below this threshold are evaluated with `microsporidia_odb10` and retained only if completeness is >=65%. Of 131 ANI-cluster representatives, 128 passed final QC and 3 were excluded.

The resulting enhanced database contains **665 RefSeq fungal genomes plus 128 CGF-derived representatives = 793 source entries**.

The rebuilt non-enhanced database is a control constructed from the NCBI-derived fungal reference without addition of the 128 CGF-derived representatives. It should not be confused with the older original/default Kraken2 fungal database used for the initial replication attempt.

## Reproducing the BA analysis

Follow:

```text
PRJNA1305663/README.txt
```

The original workflow analyzes R1 and R2 independently and averages five random 2-million-read subsampling iterations per sample/read direction.

The final statistical tables use:

- Mann-Whitney U tests with Benjamini-Hochberg false-discovery-rate correction;
- descriptive log2 fold change calculated as `log2[(mean BA + 0.1)/(mean healthy + 0.1)]`;
- rank-biserial correlation with direct 95% confidence intervals.

After the genus-average matrices are generated, run:

```bash
cd PRJNA1305663/working
python3 direct_ci_rank_biserial.py
python3 validate_final_results.py
```

These scripts reproduce the confidence intervals and validate the six final database/read-direction analyses against the reported results.

## Read-level reassignment / Sankey analysis

The Sankey workflow compares the **locally rebuilt non-enhanced control** with the **CGF-enhanced database** in pooled high-*Penicillium* samples. It is not a comparison against the older original/default Kraken2 database.

The updated workflow:

1. derives the top five *Penicillium* samples separately from the enhanced R1 and R2 matrices;
2. pools those selected samples;
3. classifies pooled reads against the non-enhanced and enhanced databases;
4. verifies paired Kraken2 outputs by read identifier before tracing reassignment;
5. generates SankeyMATIC input for reads recovered as *Aspergillus* or *Penicillium* by the enhanced database.

## Reproducibility snapshot

The best-supported database finalization dates, database construction accounting, analysis chronology, current software-environment snapshot, and final statistical validation targets are recorded in `REPRODUCIBILITY.md`.

Database dates are filesystem evidence and should not be interpreted as stronger historical provenance than the available metadata support.

## Software

Major external tools used by the workflow include Kraken2, FastANI, BUSCO, SRA Toolkit, seqtk, and pigz. Python dependencies are listed in `requirements.txt`.

## License

Code in this repository is released under the **MIT License**. See `LICENSE`.

## Contact

Hong-Hsing Liu, MD, PhD  
National Health Research Institutes, Taiwan
