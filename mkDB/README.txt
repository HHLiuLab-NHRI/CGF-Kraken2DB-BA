# Enhanced fungal database construction workflow
# Run the following sequentially from ./mkDB unless noted otherwise.
# Python dependencies are listed in ../requirements.txt.
# Major external tools include FastANI, BUSCO, Kraken2, and standard Unix utilities.

# -----------------------------------------------------------------------------
# Download PHF and CGF genomes
# -----------------------------------------------------------------------------
./11282025_00_getPHFaccessions.py
./11282025_01_downloadPHFaccessions.py
./11282025_02_getCGFaccessions.py
./11282025_03_downloadCGFaccessions.py

# -----------------------------------------------------------------------------
# Cluster PHF + CGF genomes (1,210 input genomes in the manuscript workflow)
# -----------------------------------------------------------------------------
../scripts_GCF+PHF/00_make_filelist.py
../scripts_GCF+PHF/01_split_files.py
../scripts_GCF+PHF/02_run_fastani_grid.sh
../scripts_GCF+PHF/03_fastani_to_graph.py
../scripts_GCF+PHF/04_cluster_components.py

# -----------------------------------------------------------------------------
# Download/reference NCBI fungal genomes
# -----------------------------------------------------------------------------
./12012025_00_download_fungi_summaries.sh
./12012025_01_extract_fungal_ftp_paths.py
./12012025_02_parallel_download_fungi_with_progress_and_testmode.py
./12012025_03_detect_double_gzip.py
./12012025_04_fix_double_gzip.py
./12022025_00_check_refseq_downloads.py
./12022025_01_check_cluster_genomes.py
./12022025_02_link_refFungi.sh

# -----------------------------------------------------------------------------
# Calibrate taxonomy of reference fungal genomes
# -----------------------------------------------------------------------------
../refCalibrationScripts/12032025_00_prep_taxdump.sh
../refCalibrationScripts/12032025_01_prep_refseq_metadata.py
../refCalibrationScripts/12032025_02_ref_make_filelist.py
../refCalibrationScripts/12032025_03_ref_split_files.py
../refCalibrationScripts/12032025_04_ref_run_fastani_grid.sh
../refCalibrationScripts/12032025_05_ref_fastani_to_graph.py
../refCalibrationScripts/12032025_06_ref_cluster_components.py
../refCalibrationScripts/12032025_07_ref_merge_ncbi_metadata.py

# -----------------------------------------------------------------------------
# Identify CGF/PHF genomes already represented in the reference set
# ANI >=95% is treated as represented at the species-cluster level.
# -----------------------------------------------------------------------------
../CGFvsRefScripts/12052025_00_prepare_cgf_filelist.py
../CGFvsRefScripts/12052025_01_split_cgf_filelist.py
../CGFvsRefScripts/12052025_02_run_fastani_chunks.sh
../CGFvsRefScripts/12052025_03_merge_fastani_results.py
../CGFvsRefScripts/12082025_04_assign_cgf_species.py

# -----------------------------------------------------------------------------
# Cluster/QC putatively novel genomes and insert representatives into taxonomy
# -----------------------------------------------------------------------------
../CGFNovelScripts/12082025_01_prep_novel_filelist.py
../CGFNovelScripts/12082025_02_split_novel_files.py
../CGFNovelScripts/12082025_03_run_novel_fastani.sh
../CGFNovelScripts/12082025_04_novel_fastani_to_graph.py
../CGFNovelScripts/12082025_05_cluster_novel.py
../CGFNovelScripts/12082025_06_link_genomes.sh
../CGFNovelScripts/12082025_07_run_busco_qc.sh
../CGFNovelScripts/12092025_08_select_representatives.py
../CGFNovelScripts/12092025_09_refine_and_filter.py
../CGFNovelScripts/12092025_10_assign_phylogenetic_parent.py
../CGFNovelScripts/12102025_11_prepare_kraken2_custom_db.py
../CGFNovelScripts/12102025_12_format_local_refseq.py
../CGFNovelScripts/12102025_13_build_custom_kraken2_db.sh

# The resulting Kraken2_DB is the CGF/PHF-ENHANCED database used by the
# manuscript analysis (legacy analysis suffix: nFunDB).

# -----------------------------------------------------------------------------
# Build the locally rebuilt NON-ENHANCED NCBI-derived control
# -----------------------------------------------------------------------------
./04152026_00_build_kraken_default_fungi.sh

# Historical note: the script filename above contains "default_fungi", but this
# rebuilt database is the manuscript's NON-ENHANCED control (legacy suffix:
# deFunDB). It is distinct from the older original/default Kraken2 fungal
# database used for the initial replication analysis.

# See ../REPRODUCIBILITY.md for database finalization evidence and environment
# metadata captured from the analysis workstation.
