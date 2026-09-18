"""Phase 4: prepare ligands — obabel 3D/protonation (parallel chunks) -> Meeko PDBQT per molecule."""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

OB = r'C:/ProgramData/anaconda3/envs/ob/Library/bin/obabel.exe'
WORK = 'docking/work'
PDBQT_DIR = 'docking/pdbqt'
os.makedirs(WORK, exist_ok=True)
os.makedirs(PDBQT_DIR, exist_ok=True)

def chunk_list(x, n):
    k, m = divmod(len(x), n)
    return [x[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]

def obabel_chunk(idx, lines):
    smi_in = f'{WORK}/sdf_chunk{idx}.smi'
    sdf_out = f'{WORK}/sdf_chunk{idx}.sdf'
    with open(smi_in, 'w') as f:
        f.writelines(lines)
    r = subprocess.run([OB, smi_in, '-O', sdf_out, '--gen3d', '-p', '7.4'],
                       capture_output=True, text=True)
    ok = os.path.exists(sdf_out)
    n = open(sdf_out).read().count('$$$$') if ok else 0
    return idx, r.returncode, n

def meeko_chunk(idx):
    """Convert SDF chunk to per-molecule PDBQT via Meeko; returns count."""
    from rdkit import Chem, RDLogger
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    RDLogger.DisableLog('rdApp.*')
    sdf = f'{WORK}/sdf_chunk{idx}.sdf'
    if not os.path.exists(sdf) or os.path.getsize(sdf) < 10 or '$$$$' not in open(sdf).read():
        return idx, 0
    prep = MoleculePreparation()
    n = 0
    supp = Chem.SDMolSupplier(sdf, removeHs=False)
    for mol in supp:
        if mol is None or mol.GetNumAtoms() == 0:
            continue
        name = (mol.GetProp('_Name') or f'mol_idx{idx}_{n}').strip().replace(' ', '_')
        setups = prep.prepare(mol)
        for st in setups:
            pdbqt, ok, err = PDBQTWriterLegacy.write_string(st)
            if ok:
                with open(f'{PDBQT_DIR}/{name}.pdbqt', 'w') as f:
                    f.write(pdbqt)
                n += 1
            break
    return idx, n

def prepare_all(smi_files, tag, workers=None):
    lines = []
    for sf in smi_files:
        for l in open(sf):
            l = l.strip()
            if l:
                smi, name = (l.split() + ['?'])[:2]
                lines.append(f'{smi}\t{name}\n')
    workers = workers or max(1, os.cpu_count() - 4)
    chunks = chunk_list(lines, workers)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(obabel_chunk, i, c) for i, c in enumerate(chunks)]
        n3d = 0
        for f in as_completed(futs):
            idx, rc, n = f.result()
            n3d += n
            if rc != 0:
                print(f'obabel chunk {idx} rc={rc}')
    print(f'{tag}: 3D embed done {n3d}/{len(lines)} in {time.time()-t0:.0f}s')
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=min(8, workers)) as ex:
        futs = [ex.submit(meeko_chunk, i) for i in range(len(chunks))]
        npdb = 0
        for f in as_completed(futs):
            idx, n = f.result()
            npdb += n
    print(f'{tag}: meeko PDBQT done {npdb} in {time.time()-t0:.0f}s')
    return npdb

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'refs':
        n = prepare_all(['data/dock_refs.smi'], 'refs')
        print('refs prepared:', n)
    elif mode == 'prep':
        n = prepare_all(['data/dock_set.smi'], 'main')
        print('main set prepared:', n)
