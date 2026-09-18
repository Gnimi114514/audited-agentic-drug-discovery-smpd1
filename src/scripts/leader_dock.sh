#!/bin/bash
# dock order-kept leader into MD snapshot 1ns receptor (crystal frame)
set -e
cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery
cat > md/leader_dock.cfg <<CFG
receptor = docking/md_snap/rec_1ns.pdbqt
ligand = md/leader_orderkept.pdbqt
center_x = -13.710
center_y = -34.100
center_z = -28.720
size_x = 24
size_y = 24
size_z = 24
exhaustiveness = 16
seed = 42
num_modes = 3
cpu = 4
out = md/leader_docked.out.pdbqt
CFG
./bin/vina.exe --config md/leader_dock.cfg 2>&1 | tail -8
