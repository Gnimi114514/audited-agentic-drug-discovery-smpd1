#!/bin/bash
export JAVA_HOME=~/miniforge/envs/p2r
export PATH=$JAVA_HOME/bin:$PATH
cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery
/tmp/p2rank_2.5.1/prank predict -f md/snapshot_1ns_al.pdb -o results/p2rank_out 2>&1 | tail -5
echo '== predicted pockets =='
cat results/p2rank_out/*.tsv 2>/dev/null | head -8
