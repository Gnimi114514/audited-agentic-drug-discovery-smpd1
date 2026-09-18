#!/bin/bash
# GAFF2 + AM1-BCC parameterization of the leader ligand (AmberTools antechamber)
set -e
cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery/md
export AMBERHOME=~/miniforge/envs/amber
export PATH=$AMBERHOME/bin:$PATH
antechamber -i leader_ligand.sdf -fi sdf -o leader.mol2 -fo mol2 -at gaff2 -c bcc -rn LIG -s 2 > antechamber.log 2>&1
parmchk2 -i leader.mol2 -f mol2 -o leader.frcmod >> antechamber.log 2>&1
echo "antechamber done"
ls -la leader.mol2 leader.frcmod
