"""Bound-state MD v2 — pre-registered analysis protocol (post-audit repair).

Fixes vs the audited v1 (independent-audit/REPORT.md finding 2):
- dt=2 fs; production steps assert steps*dt == 3.0 ns exactly.
- All Å values convert from nm explicitly (x10).
- Backbone selection = protein residues only (excludes WAT/LIG/ZN/ions), N/CA/C/O.
- Zn-LIG distances use MINIMUM-IMAGE convention with live box vectors.
- Ligand heavy-atom RMSD uses whole-ligand COM minimum-image correction.
- Explicit minimized reference saved to md/bound_ref.pdb BEFORE dynamics.
- Analysis protocol pre-registered in md/bound_analysis_pre_registered.json before run.
"""
import json, os, time
import openmm as mm
from openmm import app, unit
import numpy as np
import parmed as pmd

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
MD_DIR = f'{WORK}/md'

DT_FS = 2.0
HEAT_STEPS = 50000           # 100 ps
PROD_STEPS = 1500000         # 3.0 ns exactly (1.5e6 steps x 2 fs)
NS_TARGET = PROD_STEPS * DT_FS / 1e6   # fs -> ns
assert abs(NS_TARGET - 3.0) < 1e-9

pre = {
    'dt_fs': DT_FS, 'heat_steps': HEAT_STEPS, 'production_steps': PROD_STEPS,
    'production_ns': NS_TARGET, 'ensemble': 'NVT 310K LangevinMiddle',
    'zn_model': 'Li-Merz 2014 12-6-4 set, 12-6 subset (C4 term omitted), verified eps=0.02662782',
    'metrics': [
        'ligand heavy-atom RMSD vs minimized reference after whole-ligand COM minimum-image correction (A)',
        'min Zn-ligand minimum-image distance per frame (A)',
        'protein backbone (N,CA,C,O; protein residues only) RMSD with Kabsch superposition (A)',
    ],
    'reference': 'md/bound_ref.pdb (energy-minimized starting structure, saved before dynamics)',
}
json.dump(pre, open(f'{MD_DIR}/bound_analysis_pre_registered.json', 'w'), indent=1)
print('pre-registered:', NS_TARGET, 'ns', flush=True)

pm = pmd.load_file(f'{MD_DIR}/complex.prmtop', xyz=f'{MD_DIR}/complex.inpcrd')
system = pm.createSystem(nonbondedMethod=app.PME, nonbondedCutoff=1.0*unit.nanometers,
                         constraints=app.HBonds)
top = pm.topology
lig_idx = [a.index for a in top.atoms() if a.residue.name == 'LIG' and a.element.symbol != 'H']
zn_idx = [a.index for a in top.atoms() if a.residue.name == 'ZN']
WATER_IONS = {'WAT', 'HOH', 'Na+', 'Cl-', 'K+', 'ZN'}
bb_idx = [a.index for a in top.atoms() if a.name in ('N', 'CA', 'C', 'O')
          and a.residue.name not in WATER_IONS | {'LIG'}]
print('particles:', system.getNumParticles(), '| LIG heavy:', len(lig_idx),
      '| ZN:', len(zn_idx), '| protein backbone:', len(bb_idx), flush=True)

platform = mm.Platform.getPlatformByName('CUDA')
platform.setPropertyDefaultValue('CudaPrecision', 'mixed')
integrator = mm.LangevinMiddleIntegrator(310*unit.kelvin, 1/unit.picosecond, DT_FS*unit.femtoseconds)
integrator.setConstraintTolerance(1e-5)
sim = app.Simulation(top, system, integrator, platform)
sim.context.setPositions(pm.positions)
sim.minimizeEnergy(maxIterations=0)

ref_state = sim.context.getState(getPositions=True, getEnergy=True)
ref_pos_nm = ref_state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
with open(f'{MD_DIR}/bound_ref.pdb', 'w') as f:
    app.PDBFile.writeFile(top, ref_state.getPositions(), f)
print('reference saved: md/bound_ref.pdb (E = %.1f kJ/mol)' %
      ref_state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole), flush=True)
assert np.isfinite(ref_pos_nm).all()

sim.context.setVelocitiesToTemperature(310*unit.kelvin, 1234)
sim.reporters.append(app.DCDReporter(f'{MD_DIR}/bound_v2.dcd', 2500))     # 5 ps
sim.reporters.append(app.CheckpointReporter(f'{MD_DIR}/bound_v2.chk', 10000))
sim.reporters.append(app.StateDataReporter(f'{MD_DIR}/bound_v2_log.csv', 2500,
    step=True, time=True, potentialEnergy=True, temperature=True, speed=True))

x0 = ref_pos_nm
def metrics():
    st = sim.context.getState(getPositions=True)
    x = st.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    box = st.getPeriodicBoxVectors(asNumpy=True)
    com_t = x[lig_idx].mean(axis=0)
    com_0 = x0[lig_idx].mean(axis=0)
    dcom = com_t - com_0
    L = np.array(box); Linv = np.linalg.inv(L)
    frac = dcom @ Linv; frac -= np.round(frac)
    shift = frac @ L
    lig_rmsd = float(np.sqrt((((x[lig_idx] - shift) - x0[lig_idx])**2).sum(axis=1).mean())) * 10
    dvec = x[lig_idx][None, :, :] - x[zn_idx][:, None, :]
    dmin = float(box_min_image(dvec, box).min()) * 10
    P, Q = x[bb_idx], x0[bb_idx]
    pm_, qm_ = P.mean(axis=0), Q.mean(axis=0)
    H = (P - pm_).T @ (Q - qm_)
    U, S, Vt = np.linalg.svd(H)
    d_ = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d_]) @ U.T
    bb = float(np.sqrt((((P - pm_) @ R.T - (Q - qm_))**2).sum(axis=1).mean())) * 10
    return lig_rmsd, dmin, bb

def box_min_image(dvec_nm, box):
    L = np.array(box)
    Linv = np.linalg.inv(L)
    frac = dvec_nm @ Linv
    frac -= np.round(frac)
    return np.linalg.norm(frac @ L, axis=-1)

t0 = time.time()
sim.step(HEAT_STEPS)
print('heat 100 ps: ligRMSD %.2f A | Zn-lig %.2f A | bbRMSD %.2f A | %.0f s'
      % (*metrics(), time.time()-t0), flush=True)
print('production %.1f ns ...' % NS_TARGET, flush=True)
CHUNK = int(round(1000.0 / DT_FS)) * 1000      # steps per 1 ns at dt=2 fs -> 500,000
for ns in (1.0, 2.0, 3.0):
    sim.step(CHUNK)
    print('%1.1f ns: ligRMSD %.2f A | Zn-lig %.2f A | bbRMSD %.2f A | %.0f s'
          % (ns, *metrics(), time.time()-t0), flush=True)
total_steps = HEAT_STEPS + 3 * CHUNK
print('BOUND MD v2 DONE: %d steps x %g fs = %.2f ns (production %.2f ns)' % (
    total_steps, DT_FS, total_steps*DT_FS/1e6, 3*CHUNK*DT_FS/1e6), flush=True)
