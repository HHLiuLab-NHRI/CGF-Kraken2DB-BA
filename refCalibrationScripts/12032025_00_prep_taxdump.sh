#! /usr/bin/bash

mkdir -p ../refCalibrationResults/taxdump
cd ../refCalibrationResults/taxdump
wget -c https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -xvzf taxdump.tar.gz nodes.dmp names.dmp
