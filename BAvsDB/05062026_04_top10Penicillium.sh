#! /bin/bash
echo 'Top 10 from Read 1' 
awk -F'\t' '$4 == "S" && $6 ~ /Penicillium/ {print $2, $6}' ../sankey/enhanced_R1_report.txt | sort -nr | head -n 10
echo 'Top 10 from Read 2'
awk -F'\t' '$4 == "S" && $6 ~ /Penicillium/ {print $2, $6}' ../sankey/enhanced_R2_report.txt | sort -nr | head -n 10
