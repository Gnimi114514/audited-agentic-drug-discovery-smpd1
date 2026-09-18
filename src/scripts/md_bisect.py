"""Bisect the NaN: run short heating tests with staged complexity."""
import os, sys, time
import openmm as mm
from openmm import app, unit
import numpy as np

WORK = '/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery'
MD_DIR = f'{WORK}/md'
MODE = sys.argv[1]  # base | dummies | restraints

pdb = app.PDBFile(f'{MD_DIR}/asm_fixed.pdb')
ff = app.ForceField('amber14/protein.ff14SB.xml', 'amber14/tip3p.xml')
modeller = app.Modeller(pdb.topology, pdb.positions)
modeller.addSolvent(ff, model='tip3p', padding=1.0*unit.nanometers, ionicStrength=0.15*unit.molar)
system = ff.createSystem(modeller.topology, nonbondedMethod=app.PME,
                         nonbondedCutoff=1.0*unit.nanometers, constraints=app.HBonds)
positions = np.array(modeller.positions.value_in_unit(unit.nanometer))
print(MODE, 'particles:', system.getNumParticles(), flush=True)

if MODE in ('dummies', 'restraints'):
    zn_lines = [l for l in open(f'{WORK}/structures/5i85_recA_ZN.pdb').read().splitlines()
                if l.startswith('HETATM') and l[17:20].strip() == 'ZN']
    zn_nm = np.array([[float(l[30:38]), float(l[38:46]), float(l[46:54])] for l in zn_lines]) * 0.1
    n = system.getNumParticles()
    system.addParticle(65.38); system.addParticle(65.38)
    for f2 in system.getForces():
        if f2.getName() == 'NonbondedForce':
            f2.addParticle(0.0, 1e-8, 0.0); f2.addParticle(0.0, 1e-8, 0.0)
    positions = np.vstack([positions, zn_nm])
    # center-of-mass correction: translate dummies into the (possibly recentered) frame by
    # aligning to the closest C-alpha anchor pair of ASP206/HIS457 region if present
if MODE == 'restraints':
    rest = mm.CustomExternalForce('k_i*((x-x0)^2+(y-y0)^2+(z-z0)^2)')
    rest.addGlobalParameter('dummy', 0.0)
    for p in ('k_i', 'x0', 'y0', 'z0'):
        rest.addPerParticleParameter(p)
    ca = 0
    for a in modeller.topology.atoms():
        if a.name == 'CA':
            rest.addParticle(a.index, [100.0, *positions[a.index]]); ca += 1
    for j, z in enumerate(zn_nm):
        rest.addParticle(n + j, [200000.0, *z])
    system.addForce(rest)
    print('restraints: CA=%d Zn=2' % ca, flush=True)

platform = mm.Platform.getPlatformByName('CUDA')
platform.setPropertyDefaultValue('CudaPrecision', 'mixed')
integrator = mm.LangevinMiddleIntegrator(310*unit.kelvin, 1/unit.picosecond, 1*unit.femtoseconds)
integrator.setConstraintTolerance(1e-5)
sim = app.Simulation(modeller.topology, system, integrator, platform)
sim.context.setPositions([unit.Quantity(p, unit.nanometer) for p in positions])
sim.minimizeEnergy(maxIterations=0)
e = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
print('post-min E: %.1f' % e, flush=True)
x = sim.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
assert np.isfinite(x).all()
sim.context.setVelocitiesToTemperature(310*unit.kelvin, 1234)
t0 = time.time()
sim.step(50000)   # 50 ps at 1 fs
x = sim.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
print('50 ps OK, finite=%s, T-time %.0fs' % (np.isfinite(x).all(), time.time()-t0), flush=True)
