"""Big item 2: fragment-growth expansion on priority hits — mono-substituent scans
(F/Cl/OH/OMe/CN/CF3/Me at aromatic CH positions, valence-safe) + docking.
Improved analogs are re-docked into the 5JG8 ensemble receptor for consistency."""
import os, sys, json, time, subprocess
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from multiprocessing import Pool
from meeko import MoleculePreparation, PDBQTWriterLegacy
from concurrent.futures import ThreadPoolExecutor, as_completed

RDLogger.DisableLog('rdApp.*')
VINA = 'bin/vina.exe'
PDBQT_DIR = 'docking/pdbqt_exp'
OUT = 'docking/out_exp'
os.makedirs(PDBQT_DIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
CENTER = (-13.710, -34.100, -28.720)
SIZE = 24

FRAGS = ['F', 'Cl', 'O', 'OC', 'C#N', 'C(F)(F)F', 'C']  # OH, OMe, CN, CF3, Me

def scan_analogs(smi):
    """Return list of (tag, smiles) mono-substituent analogs, valence-safe."""
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return []
    out = []
    seen = {Chem.MolToSmiles(m)}
    for a in m.GetAtoms():
        if a.GetSymbol() != 'C' or not a.GetIsAromatic() or a.GetTotalNumHs() != 1:
            continue
        if a.IsInRing() and sum(1 for n in a.GetNeighbors() if n.GetIsAromatic() and n.GetSymbol() == 'N') >= 1 and False:
            pass
        for fi, frag in enumerate(FRAGS):
            em = Chem.RWMol(m)
            atom = em.GetAtomWithIdx(a.GetIdx())
            atom.SetNumExplicitHs(0)
            atom.SetNoImplicit(True)
            if frag == 'C':  # methyl
                c = em.AddAtom(Chem.Atom(6))
                em.AddBond(a.GetIdx(), c, Chem.BondType.SINGLE)
            elif frag == 'OC':  # methoxy
                o = em.AddAtom(Chem.Atom(8))
                c = em.AddAtom(Chem.Atom(6))
                em.AddBond(a.GetIdx(), o, Chem.BondType.SINGLE)
                em.AddBond(o, c, Chem.BondType.SINGLE)
            elif frag == 'C#N':  # nitrile
                c = em.AddAtom(Chem.Atom(6))
                n = em.AddAtom(Chem.Atom(7))
                em.AddBond(a.GetIdx(), c, Chem.BondType.SINGLE)
                em.AddBond(c, n, Chem.BondType.TRIPLE)
            elif frag == 'C(F)(F)F':  # CF3
                c = em.AddAtom(Chem.Atom(6))
                em.AddBond(a.GetIdx(), c, Chem.BondType.SINGLE)
                for _ in range(3):
                    f = em.AddAtom(Chem.Atom(9))
                    em.AddBond(c, f, Chem.BondType.SINGLE)
            elif frag == 'O':  # hydroxyl
                o = em.AddAtom(Chem.Atom(8))
                em.AddBond(a.GetIdx(), o, Chem.BondType.SINGLE)
            else:  # F or Cl: aromatic C-H -> C-X
                atom.SetAtomicNum(9 if frag == 'F' else 17)
            try:
                Chem.SanitizeMol(em)
                smi2 = Chem.MolToSmiles(em)
                if smi2 not in seen:
                    seen.add(smi2)
                    out.append((f"{frag}@C{a.GetIdx()}", smi2))
            except Exception:
                continue
    return out[:60]

def prep_one(args):
    name, smi = args
    try:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            return name, None
        mol = Chem.AddHs(mol)
        p = AllChem.ETKDGv3(); p.randomSeed = 0xf00d
        if AllChem.EmbedMolecule(mol, p) < 0:
            p.useRandomCoords = True
            if AllChem.EmbedMolecule(mol, p) < 0:
                return name, None
        if AllChem.MMFFHasAllMoleculeParams(mol):
            AllChem.MMFFOptimizeMolecule(mol, mmffVariant='MMFF94s', maxIters=500)
        st = MoleculePreparation().prepare(mol)
        if not st:
            return name, None
        s, ok, _ = PDBQTWriterLegacy.write_string(st[0])
        if ok:
            open(f'{PDBQT_DIR}/{name}.pdbqt', 'w').write(s)
            return name, smi
    except Exception:
        return name, None
    return name, None

def run_vina(pdbqt_path, receptor='structures/5i85_recA_ZN_rigid.pdbqt', outdir=OUT, center=CENTER):
    name = os.path.basename(pdbqt_path).replace('.pdbqt', '')
    outp = f'{outdir}/{name}.out.pdbqt'
    cfg = (f'receptor = {receptor}\nligand = {pdbqt_path}\n'
           f'center_x = {center[0]:.3f}\ncenter_y = {center[1]:.3f}\ncenter_z = {center[2]:.3f}\n'
           f'size_x = {SIZE}\nsize_y = {SIZE}\nsize_z = {SIZE}\n'
           f'exhaustiveness = 8\nseed = 42\nnum_modes = 5\ncpu = 1\nout = {outp}\n')
    cfgf = f'{outdir}/{name}.cfg'
    open(cfgf, 'w').write(cfg)
    try:
        r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=900)
        if r.returncode != 0 or not os.path.exists(outp):
            return name, None
        for l in open(outp):
            if 'VINA RESULT' in l:
                return name, float(l.split()[3])
    except Exception:
        return name, None
    return name, None

if __name__ == '__main__':
    hits = json.load(open('results/top10_for_analogs.json'))
    PRIORITY = ['CHEMBL7385', 'CHEMBL24974', 'CHEMBL48767', 'CHEMBL6729',
                'CHEMBL29571', 'CHEMBL37169']
    sel = [h for h in hits if h['name'] in PRIORITY]
    jobs, meta = [], {}
    for h in sel:
        for tag, smi in scan_analogs(h['smiles']):
            an = f"EXP_{h['name']}_{tag.replace('@','_').replace('#','T')}"
            meta[an] = {'parent': h['name'], 'parent_vina': h['vina_best'], 'tag': tag, 'smiles': smi}
            jobs.append((an, smi))
    print(len(jobs), 'expansion analogs')
    with Pool(20) as pool:
        res = list(pool.imap_unordered(prep_one, jobs, chunksize=4))
    ok = [(n, s) for n, s in res if s]
    print('prepared:', len(ok), '/', len(jobs))
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(run_vina, f'{PDBQT_DIR}/{n}.pdbqt'): n for n, _ in ok}
        for f in as_completed(futs):
            n, sc = f.result()
            if sc is not None:
                results.append((n, sc))
    print('docked:', len(results))
    out = []
    for n, sc in results:
        m = meta[n]
        out.append({**m, 'analog_name': n, 'analog_vina': round(sc, 2),
                    'delta': round(sc - m['parent_vina'], 2)})
    out.sort(key=lambda r: r['delta'])
    json.dump(out, open('results/expansion_results.json', 'w'), indent=1)
    print('\n== best 3 per parent ==')
    byp = {}
    for r in out:
        byp.setdefault(r['parent'], []).append(r)
    for p, lst in byp.items():
        print(p, f'(parent {lst[0]["parent_vina"]}):')
        for r in lst[:3]:
            print(f"   {r['tag']:16} {r['analog_vina']}  d={r['delta']}  {r['smiles'][:80]}")
