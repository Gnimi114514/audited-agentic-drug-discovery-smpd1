"""MD v4 — frozen-pocket protocol (no custom forces).

- PDBFixer-fixed protein, TIP3P, 0.15 M, PME.
- Catalytic-pocket heavy atoms + 2 Zn dummy particles have mass 0 (frozen at crystal
  positions); everything else runs free NVT at 310 K. Metal coordination chemistry is
  not simulated — dummies are geometric placeholders preserving the catalytic site.
- Heat 100 ps + production 5 ns at 1 fs, DCD frames every 5 ps, final PDB snapshot.
"""
import os, time
import openmm as mm
from openmm import app, unit
import numpy as np

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
MD_DIR = f'{WORK}/md'
POCKET_IDS = {206, 208, 278, 282, 318, 319, 425, 457, 458, 459, 488}

pdb = app.PDBFile(f'{MD_DIR}/asm_fixed.pdb')
ff = app.ForceField('amber14/protein.ff14SB.xml', 'amber14/tip3p.xml')
modeller = app.Modeller(pdb.topology, pdb.positions)
modeller.addSolvent(ff, model='tip3p', padding=1.0*unit.nanometers, ionicStrength=0.15*unit.molar)
system = ff.createSystem(modeller.topology, nonbondedMethod=app.PME,
                         nonbondedCutoff=1.0*unit.nanometers, constraints=None)  # massless frozen atoms cannot carry constraints
print('solvated:', system.getNumParticles(), 'particles', flush=True)
with open(f'{MD_DIR}/solvated.pdb', 'w') as f:
    app.PDBFile.writeFile(modeller.topology, modeller.positions, f)

# --- frozen atoms: map crystal residue ids -> fixed residue order ---
crystal_ids = []
seen = set()
for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb'):
    if l.startswith('ATOM'):
        rid = int(l[22:26])
        if rid not in seen:
            seen.add(rid); crystal_ids.append(rid)
id2ordinal = {rid: i for i, rid in enumerate(crystal_ids)}
pocket_ordinals = {id2ordinal[i] for i in POCKET_IDS}
fixed_residues = list(modeller.topology.residues())
res_ordinal_map = {id(r): i for i, r in enumerate(fixed_residues)}
frozen = 0
for a in modeller.topology.atoms():
    if a.element.symbol != 'H' and res_ordinal_map[id(a.residue)] in pocket_ordinals:
        system.setParticleMass(a.index, 0.0); frozen += 1
print('frozen pocket heavy atoms:', frozen, flush=True)

# --- Zn dummies: append 2 frozen particles at crystal positions ---
zn_lines = [l for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb').read().splitlines()
            if l.startswith('HETATM') and l[17:20].strip() == 'ZN']
zn_nm = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in zn_lines]) * 0.1
for _ in range(2):
    system.addParticle(0.0)
    for f2 in system.getForces():
        if f2.getName() == 'NonbondedForce':
            f2.addParticle(0.0, 1e-8, 0.0)
positions = np.array(modeller.positions.value_in_unit(unit.nanometer))
positions = np.vstack([positions, zn_nm])
print('Zn dummies appended (mass 0, frozen)', flush=True)

platform = mm.Platform.getPlatformByName('CUDA')
platform.setPropertyDefaultValue('CudaPrecision', 'mixed')
integrator = mm.LangevinMiddleIntegrator(310*unit.kelvin, 1/unit.picosecond, 1*unit.femtoseconds)
integrator.setConstraintTolerance(1e-5)
sim = app.Simulation(modeller.topology, system, integrator, platform)
sim.context.setPositions([unit.Quantity(p, unit.nanometer) for p in positions])
sim.minimizeEnergy(maxIterations=0)
e = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
print('post-min E: %.1f kJ/mol' % e, flush=True)
x = sim.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
assert np.isfinite(x).all()
sim.context.setVelocitiesToTemperature(310*unit.kelvin, 1234)

class SlicedDCDReporter(object):
    """DCD reporter that drops the appended dummy-Zn particles from frames."""
    def __init__(self, file, topology, n_real, reportInterval, dt_ps):
        self._dcd = app.DCDFile(file, topology, dt_ps, 0, reportInterval)
        self._n = n_real; self._interval = reportInterval
    def describeNextReport(self, simulation):
        steps = self._interval - simulation.currentStep % self._interval
        return (steps, True, False, True, False, None)
    def report(self, simulation, state):
        pos = state.getPositions(asNumpy=True)[:self._n]
        self._dcd.writeModel(pos, periodicBoxVectors=state.getPeriodicBoxVectors())

dcd_handle = open(f'{MD_DIR}/prod.dcd', 'wb')
sim.reporters.append(SlicedDCDReporter(dcd_handle, modeller.topology,
                       modeller.topology.getNumAtoms(), 5000, 0.005))  # 5 ps/frame
sim.reporters.append(app.CheckpointReporter(f'{MD_DIR}/chk.chk', 10000))
sim.reporters.append(app.StateDataReporter(f'{MD_DIR}/log.csv', 2500,
    step=True, time=True, potentialEnergy=True, temperature=True, speed=True))

t0 = time.time()
print('heating 100 ps...', flush=True)
sim.step(100000)
print('heat done %.0fs' % (time.time()-t0), flush=True)
print('production 5 ns...', flush=True)
for ns in (1.0, 2.0, 3.0, 4.0, 5.0):
    sim.step(int(ns * 1e6))   # ns -> steps at 1 fs (1 ns = 1e6 steps)
    x = sim.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    print(f'{ns} ns: finite={np.isfinite(x).all()}, elapsed {time.time()-t0:.0f}s', flush=True)
with open(f'{MD_DIR}/final.pdb', 'w') as f:
    app.PDBFile.writeFile(sim.topology, sim.context.getState(getPositions=True).getPositions(asNumpy=True)[:modeller.topology.getNumAtoms()], f)
print('MD DONE', flush=True)
