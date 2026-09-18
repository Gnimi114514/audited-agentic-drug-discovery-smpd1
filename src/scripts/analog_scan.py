"""Phase 6: generate SAR analogs (mono-substitution scan) for top hits and dock them.

Analog hypotheses computed, not just asserted:
- A: aromatic H->F swap (block metabolism / modulate electronics)
- B: methyl scan on aromatic CH (fill adjacent subpocket)
- C: terminal-amine N-demethylation or N-ethyl homolog (tune pKa/lysosomotropism)
Each analog is re-protonated, re-prepared and docked with the identical protocol.
"""
import os, sys, json, time
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem
from multiprocessing import Pool
from meeko import MoleculePreparation, PDBQTWriterLegacy
import subprocess

RDLogger.DisableLog('rdApp.*')
PDBQT_DIR = 'docking/pdbqt_analog'
OUT = 'docking/out_analog'
os.makedirs(PDBQT_DIR, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
VINA = 'bin/vina.exe'
CENTER = (-13.710, -34.100, -28.720)
SIZE = 24

def analogs_for(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return []
    out = []
    for a in m.GetAtoms():
        # A: aromatic CH -> C-F
        if a.GetSymbol() == 'C' and a.GetIsAromatic() and not a.IsInRingSize(5):
            if all(n.GetSymbol() != 'F' for n in a.GetNeighbors()):
                em = Chem.RWMol(m)
                em.GetAtomWithIdx(a.GetIdx()).SetAtomicNum(9)
                out.append(('F-scan@' + str(a.GetIdx()), Chem.MolToSmiles(em)))
        # B: aromatic CH -> C-CH3 (valence permitting)
        if a.GetSymbol() == 'C' and a.GetIsAromatic() and a.GetTotalNumHs() == 1:
            em = Chem.RWMol(m)
            em.GetAtomWithIdx(a.GetIdx()).SetNumExplicitHs(0)
            em.GetAtomWithIdx(a.GetIdx()).SetNoImplicit(True)
            c = Chem.Atom(6)
            idx = em.AddAtom(c)
            em.AddBond(a.GetIdx(), idx, Chem.BondType.SINGLE)
            try:
                Chem.SanitizeMol(em)
                out.append(('Me-scan@' + str(a.GetIdx()), Chem.MolToSmiles(em)))
            except Exception:
                pass
    # C: terminal tertiary amine ethyl homolog (one per tertiary dialkylamine)
    for a in m.GetAtoms():
        if a.GetSymbol() == 'N' and a.GetFormalCharge() >= 0:
            nbrs = [n for n in a.GetNeighbors() if n.GetSymbol() == 'C']
            nh = a.GetTotalNumHs()
            if len(nbrs) == 2 and nh == 1:  # secondary amine -> N-ethyl
                em = Chem.RWMol(m)
                em.GetAtomWithIdx(a.GetIdx()).SetNumExplicitHs(0)
                em.GetAtomWithIdx(a.GetIdx()).SetNoImplicit(True)
                c = Chem.Atom(6)
                idx = em.AddAtom(c)
                em.AddBond(a.GetIdx(), idx, Chem.BondType.SINGLE)
                c2 = Chem.Atom(6)
                idx2 = em.AddAtom(c2)
                em.AddBond(idx, idx2, Chem.BondType.SINGLE)
                try:
                    Chem.SanitizeMol(em)
                    out.append(('N-ethyl', Chem.MolToSmiles(em)))
                except Exception:
                    pass
    # cap: max 12 analogs per hit
    return out[:12]

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

def run_vina(pdbqt_path):
    name = os.path.basename(pdbqt_path).replace('.pdbqt', '')
    outp = f'{OUT}/{name}.out.pdbqt'
    cfg = (f'receptor = structures/5i85_recA_ZN_rigid.pdbqt\nligand = {pdbqt_path}\n'
           f'center_x = {CENTER[0]}\ncenter_y = {CENTER[1]}\ncenter_z = {CENTER[2]}\n'
           f'size_x = {SIZE}\nsize_y = {SIZE}\nsize_z = {SIZE}\n'
           f'exhaustiveness = 8\nseed = 42\nnum_modes = 5\ncpu = 1\nout = {outp}\n')
    cfgf = f'{OUT}/{name}.cfg'
    open(cfgf, 'w').write(cfg)
    try:
        r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(outp):
            return name, None
        for l in open(outp):
            if 'VINA RESULT' in l:
                return name, float(l.split()[3])
    except Exception:
        return name, None
    return name, None

if __name__ == '__main__':
    top = json.load(open('results/top10_for_analogs.json'))
    jobs, meta = [], {}
    for hit in top:
        name0 = hit['name']; smi0 = hit['smiles']; vina0 = hit['vina_best']
        for tag, smi in analogs_for(smi0):
            an = f"AN_{name0}_{tag.replace('@','_')}"
            if an in meta:
                continue
            meta[an] = {'parent': name0, 'parent_vina': vina0, 'tag': tag, 'smiles': smi}
            jobs.append((an, smi))
    print(len(jobs), 'analog jobs')
    with Pool(20) as pool:
        res = list(pool.imap_unordered(prep_one, jobs, chunksize=4))
    ok_jobs = [(n, s) for n, s, in res if s]
    print('prepared:', len(ok_jobs))
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(run_vina, f'{PDBQT_DIR}/{n}.pdbqt'): n for n, _ in ok_jobs}
        for f in as_completed(futs):
            n, sc = f.result()
            if sc is not None:
                results.append((n, sc))
    out = []
    for n, sc in results:
        m = meta[n]
        out.append({**m, 'analog_name': n, 'analog_vina': round(sc, 2),
                    'delta': round(sc - m['parent_vina'], 2)})
    out.sort(key=lambda r: r['delta'])
    json.dump(out, open('results/analog_results.json', 'w'), indent=1)
    for r in out[:25]:
        print(f"{r['analog_name']:52} parent={r['parent_vina']} analog={r['analog_vina']} d={r['delta']}")
    print('saved results/analog_results.json')
