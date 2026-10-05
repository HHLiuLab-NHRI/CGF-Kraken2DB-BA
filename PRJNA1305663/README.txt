# PRJNA1305663 analysis workflow

# Run the following from ./working unless otherwise noted.
# Cohort metadata are in ./meta/meta.csv.
# R1 and R2 are analyzed independently.
# Five random 2-million-read subsampling iterations are averaged per sample/read direction.

# Download and subsample public SRA data
./12152025_01_dlSRA.sh
./12192025_00_random2MSRR.sh

# -----------------------------------------------------------------------------
# 1. Original/default Kraken2 fungal reference
#    Historical analysis directories have no suffix.
# -----------------------------------------------------------------------------
./12192025_01_classifyForward_srr2M.sh
./12192025_02_classifyReverse_srr2M.sh
./12232025_00_extractGenus_R1.py
./12232025_01_extractGenus_R2.py
./12232025_02_averageGenus_R1.py
./12232025_03_averageGenus_R2.py
./12242025_00_analyzeGenus_BAvsH_FDR.01.py
./12242025_01_suppStat.py

# -----------------------------------------------------------------------------
# 2. CGF/PHF-enhanced fungal reference
#    Legacy suffix: nFunDB
# -----------------------------------------------------------------------------
./04142026_00_classifyForward_srr2M_nFunDB.sh
./04142026_01_classifyReverse_srr2M_nFunDB.sh
./04142026_02_extractGenus_R1_nFunDB.py
./04142026_03_extractGenus_R2_nFunDB.py
./04142026_04_averageGenus_R1_nFunDB.py
./04142026_05_averageGenus_R2_nFunDB.py
./04142026_06_analyzeGenus_BAvsH_FDR_nFunDB.01.py
./04142026_07_suppStat.py

# -----------------------------------------------------------------------------
# 3. Locally rebuilt non-enhanced NCBI-derived fungal reference
#    Legacy suffix: deFunDB
#    This is a control rebuilt without the novel CGF/PHF representatives.
#    It is NOT the older original/default Kraken2 fungal reference above.
# -----------------------------------------------------------------------------
./04152026_00_classifyForward_srr2M_deFunDB.sh
./04152026_01_classifyReverse_srr2M_deFunDB.sh
./04152026_02_extractGenus_R1_deFunDB.py
./04152026_03_extractGenus_R2_deFunDB.py
./04152026_04_averageGenus_R1_deFunDB.py
./04152026_05_averageGenus_R2_deFunDB.py
./04152026_06_analyzeGenus_BAvsH_FDR_deFunDB.01.py
./04152026_07_suppStat.py

# -----------------------------------------------------------------------------
# Final manuscript effect sizes and 95% CIs
# -----------------------------------------------------------------------------
# Uses Mann-Whitney U, BH-FDR, rank-biserial r, and DeLong structural-component
# variance for the equivalent AUC statistic. Log2 fold change uses +0.1.
python3 direct_ci_rank_biserial.py
python3 validate_final_results.py

# -----------------------------------------------------------------------------
# Read-level reassignment / Sankey workflow
# -----------------------------------------------------------------------------
# This compares the locally rebuilt NON-ENHANCED control with the ENHANCED DB.
# Top-five Penicillium samples are derived independently for R1 and R2.
./05062026_00_find_top_penicillium.py
./05062026_01_pool_top5.sh
./05062026_02_run_sankey_kraken2.sh
./05062026_03_parse_sankey.py
./05062026_04_top10Penicillium.sh

# The Sankey parser verifies equal file length and matching read IDs before
# tracing assignments to Aspergillus/Penicillium in the enhanced database.

# Exploratory/legacy scripts such as paired, three-group, BA-vs-H+U, and pfFunDB
# analyses are retained for provenance but are not part of the final manuscript
# analysis path described above.
