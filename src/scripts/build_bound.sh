#!/bin/bash
# Build bound-state system: MD-relaxed protein + ZN x2 (crystal pos, Li-Merz 12-6-4) + docked leader ligand (GAFF2)
set -e
cd /mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery
python3 - <<'PYEOF'
lines = []
for l in open('md/snapshot_1ns_al.pdb'):
    # strip protein hydrogens (leap rebuilds them; avoids HIS-template clashes), keep heavy atoms
    if l.startswith('ATOM') and l[12:16].strip()[:1] != 'H':
        lines.append(l.rstrip())
lines.append('TER')
zn = [l.rstrip() for l in open('structures/5i85_recA_ZN.pdb')
      if l.startswith('HETATM') and l[17:20].strip() == 'ZN']
lig = [l.rstrip() for l in open('md/leader_docked.pdb') if l.startswith(('HETATM', 'ATOM'))]
with open('md/bound_combined.pdb', 'w') as f:
    for l in lines + zn + lig:
        f.write(l + '\n')
    f.write('END\n')
print('combined: %d protein + %d ZN + %d LIG atoms' % (len(lines), len(zn), len(lig)))
PYEOF

cat > md/tleap_bound.in <<'TLEAP'
source leaprc.protein.ff14SB
source leaprc.gaff2
source leaprc.water.tip3p
loadamberparams md/leader.frcmod
loadamberparams ~/miniforge/envs/amber/dat/leap/parm/frcmod.ions234lm_1264_tip3p
LIG = loadmol2 md/leader_pose.mol2
SYS = loadpdb md/bound_combined.pdb
check SYS
solvateBox SYS TIP3PBOX 10.0
addIonsRand SYS Cl- 0
saveAmberParm SYS md/complex.prmtop md/complex.inpcrd
quit
TLEAP

~/miniforge/envs/amber/bin/tleap -f md/tleap_bound.in > md/tleap_bound.log 2>&1
tail -12 md/tleap_bound.log
ls -la md/complex.prmtop md/complex.inpcrd
# PRE-REGISTERED BUILD CHECK: Zn self-LJ eps must equal the 2014 12-6-4 value (0.02662782)
~/miniforge/envs/md/bin/python - <<'PYCHECK'
import parmed as pmd
pm = pmd.load_file("md/complex.prmtop")
zn = [a for r in pm.residues if r.name == "ZN" for a in r.atoms][0]
t = pm.LJ_types[zn.type]
i = j = t
if i < j: i, j = j, i
k = i*(i-1)//2 + j - 1
A = pm.parm_data["LENNARD_JONES_ACOEF"][k]
B = pm.parm_data["LENNARD_JONES_BCOEF"][k]
eps = B*B/(4*A)
rmin_half = (A/B)**(1/6) * 2**(-1/6) * 2   # sigma-style guard, report both conventions
print("BUILD CHECK: Zn eps = %.8f kcal/mol (target 0.02662782), q = %.1f" % (eps, zn.charge))
assert abs(eps - 0.02662782) < 1e-6, "Zn params are NOT the 2014 12-6-4 set!"
print("BUILD CHECK PASSED: 12-6-4 parameters active")
PYCHECK
