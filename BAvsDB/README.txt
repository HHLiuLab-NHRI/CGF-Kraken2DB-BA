# Install Kraken2 default fungi database at $HOME/share/db/kraken2/fungi/
# Run sequentially
# Downloading
./12152025_01_dlSRA.sh
./12192025_00_random2MSRR.sh

# Using Kraken2 default database
./12192025_01_classifyForward_srr2M.sh
./12192025_02_classifyReverse_srr2M.sh
./12232025_00_extractGenus_R1.py
./12232025_01_extractGenus_R2.py
./12232025_02_averageGenus_R1.py
./12232025_03_averageGenus_R2.py
./12242025_00_analyzeGenus_BAvsH_FDR.01.py
./12242025_01_suppStat.py

# Using CGF-enhanced database
./04142026_00_classifyForward_srr2M_nFunDB.sh
./04142026_01_classifyReverse_srr2M_nFunDB.sh
./04142026_02_extractGenus_R1_nFunDB.py
./04142026_03_extractGenus_R2_nFunDB.py
./04142026_04_averageGenus_R1_nFunDB.py
./04142026_05_averageGenus_R2_nFunDB.py
./04142026_06_analyzeGenus_BAvsH_FDR_nFunDB.01.py
./04142026_07_suppStat.py

# Using locally built non-enhanced database
./04152026_00_classifyForward_srr2M_deFunDB.sh
./04152026_01_classifyReverse_srr2M_deFunDB.sh
./04152026_02_extractGenus_R1_deFunDB.py
./04152026_03_extractGenus_R2_deFunDB.py
./04152026_04_averageGenus_R1_deFunDB.py
./04152026_05_averageGenus_R2_deFunDB.py
./04152026_06_analyzeGenus_BAvsH_FDR_deFunDB.01.py
./04152026_07_suppStat.py

# Sankey diagrams
./05062026_00_find_top_penicillium.py
./05062026_01_pool_top5.sh
./05062026_02_run_sankey_kraken2.sh
./05062026_03_parse_sankey.py
./05062026_04_top10Penicillium.sh
