"""Phase 4 (v2): ligand prep with RDKit 3D + pH 7.4 protonation rules -> Meeko PDBQT.

Protonation rules (documented in research-log): pragmatic pH-7.4 dominant states.
"""
import os, sys, json, time
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from rdkit import RDConfig
from multiprocessing import Pool
from meeko import MoleculePreparation, PDBQTWriterLegacy

RDLogger.DisableLog('rdApp.*')
PDBQT_DIR = 'docking/pdbqt'
os.makedirs(PDBQT_DIR, exist_ok=True)

# ---- pH 7.4 protonation (SMARTS -> replacement on ionizable groups) ----
PROT_RULES = [
    # (smarts to find, smarta to install) applied with single-match-per-group semantics
    Chem.MolFromSmarts('[CX4][NX3;H1,H2,H3;!$([N]~[=O,N,#N]);!$(N*C=O);!$(N~[a])]'),  # aliphatic amine N-H
    Chem.MolFromSmarts('[C,SX4](=[OX1])[OX2;H1]'),          # carboxylic/sulfonic acid -> anion
    Chem.MolFromSmarts('[NX3;H0;!$(N*a);!$(N*C=O)]([C])='), # placeholder (not used)
]
DEPROT_ACID = Chem.MolFromSmarts('[CX3,SX4](=[OX1])[OX2H1]')
PROT_AMINE = Chem.MolFromSmarts('[#6X4][#7X3;H1,H2;!$(N[!#6]);!$(N*C=*O);!$(Nc)]')  # sec/tert aliphatic amine with >=1 H
PROT_GUAN = Chem.MolFromSmarts('[NX3;H0,H1][NX2]=[NX3]')  # guanidine-like (handled by charge later, skip)

def protonate_ph74(mol):
    """Return copy with pragmatic pH 7.4 dominant protonation state."""
    m = Chem.RWMol(mol)
    # deprotonate carboxylic acids -> [O-]
    for match in m.GetSubstructMatches(DEPROT_ACID):
        o_idx = match[2]  # [OX2H1]
        atom = m.GetAtomWithIdx(o_idx)
        if atom.GetFormalCharge() == 0:
            atom.SetFormalCharge(-1)
            atom.SetNumExplicitHs(max(0, atom.GetNumExplicitHs() - 1))
            atom.SetNoImplicit(True)
    # protonate aliphatic amines with >=1 H -> [+1]
    for match in m.GetSubstructMatches(PROT_AMINE):
        n_idx = match[1]
        atom = m.GetAtomWithIdx(n_idx)
        if atom.GetFormalCharge() == 0 and atom.GetTotalNumHs() >= 1:
            atom.SetFormalCharge(+1)
    Chem.SanitizeMol(m)
    return m

def prep_one(args):
    smi, name = args
    try:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return name, None, 'unparseable'
        mol = protonate_ph74(mol)
        mol_h = Chem.AddHs(mol)
        params = AllChem.ETKDGv3()
        params.randomSeed = 0xf00d
        params.enforceChirality = True
        cid = AllChem.EmbedMolecule(mol_h, params)
        if cid < 0:
            params.useRandomCoords = True
            cid = AllChem.EmbedMolecule(mol_h, params)
            if cid < 0:
                return name, None, 'embed-failed'
        if AllChem.MMFFHasAllMoleculeParams(mol_h):
            AllChem.MMFFOptimizeMolecule(mol_h, mmffVariant='MMFF94s', maxIters=500)
        Chem.AssignStereochemistryFrom3D(mol_h)
        prep = MoleculePreparation()
        setups = prep.prepare(mol_h)
        if not setups:
            return name, None, 'meeko-failed'
        pdbqt, ok, err = PDBQTWriterLegacy.write_string(setups[0])
        if not ok:
            return name, None, f'pdbqt-failed:{err}'
        with open(f'{PDBQT_DIR}/{name}.pdbqt', 'w') as f:
            f.write(pdbqt)
        return name, smi, None
    except Exception as e:
        return name, None, f'exc:{str(e)[:80]}'

def prepare_file(smi_file, workers=20):
    jobs = []
    for l in open(smi_file):
        l = l.strip()
        if l:
            smi, name = (l.split() + ['?'])[:2]
            out = f'{PDBQT_DIR}/{name}.pdbqt'
            if not os.path.exists(out):
                jobs.append((smi, name))
    print(f'{smi_file}: {len(jobs)} to prepare (of total listed)')
    t0 = time.time()
    ok, fail = 0, []
    with Pool(workers) as pool:
        for name, smi, err in pool.imap_unordered(prep_one, jobs, chunksize=8):
            if err:
                fail.append((name, err))
            else:
                ok += 1
            if (ok + len(fail)) % 1000 == 0:
                print(f'  {ok+len(fail)}/{len(jobs)} in {time.time()-t0:.0f}s', flush=True)
    print(f'prepared {ok}, failed {len(fail)} in {time.time()-t0:.0f}s')
    if fail[:10]:
        print('sample failures:', fail[:10])
    json.dump(fail, open('data/prep_failures.json', 'w'), indent=1)

if __name__ == '__main__':
    prepare_file(sys.argv[1])
