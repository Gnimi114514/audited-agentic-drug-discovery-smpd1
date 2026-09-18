"""Phase 4: prepare ligand PDBQTs (obabel 3D + pH 7.4) in parallel chunks, then dock with Vina."""
import os, subprocess, sys, csv, math, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

OB = r'C:/ProgramData/anaconda3/envs/ob/Library/bin/obabel.exe'
VINA = 'bin/vina.exe'
WORK = 'docking/work'
OUT = 'docking/out'
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

CENTER = (-13.710, -34.100, -28.720)
SIZE = 24  # widened box to cover hydrophobic tail channel (see research-log Phase 3)

def chunk_list(x, n):
    k, m = divmod(len(x), n)
    return [x[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]

def prep_chunk(idx, lines):
    smi_in = f'{WORK}/chunk{idx}.smi'
    sdf_out = f'{WORK}/chunk{idx}.pdbqt'
    with open(smi_in, 'w') as f:
        f.writelines(lines)
    r = subprocess.run([OB, smi_in, '-O', sdf_out, '--gen3d', '-p', '7.4'],
                       capture_output=True, text=True)
    n = open(sdf_out).read().count('ROOT') if os.path.exists(sdf_out) else 0
    return idx, r.returncode, n

def prepare_all(smi_files, tag):
    """Prepare all .smi files into per-molecule pdbqt; returns list of pdbqt paths."""
    lines = []
    names = []
    for sf in smi_files:
        for l in open(sf):
            l = l.strip()
            if l:
                smi, name = (l.split() + ['?'])[:2]
                lines.append(f'{smi}\t{name}\n')
                names.append(name)
    chunks = chunk_list(lines, max(1, os.cpu_count() - 4))
    with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
        futs = [ex.submit(prep_chunk, i, c) for i, c in enumerate(chunks)]
        for f in as_completed(futs):
            idx, rc, n = f.result()
            if rc != 0:
                print(f'chunk {idx} failed rc={rc}')
    # split each chunk pdbqt into individual files via vina_split? obabel wrote multi-MODEL? 
    # obabel writes concatenated ROOT/ENDROOT blocks per molecule; use vina_split
    merged = f'{WORK}/merged_{tag}.pdbqt'
    with open(merged, 'w') as out:
        for i in range(len(chunks)):
            p = f'{WORK}/chunk{i}.pdbqt'
            if os.path.exists(p):
                out.write(open(p).read())
                out.write('\n')
    return merged, names

def split_ligands(merged_pdbqt, tag):
    """Split multi-ligand pdbqt into individual files using vina_split."""
    subprocess.run([VINA, '--split', merged_pdbqt], capture_output=True, text=True)
    base = merged_pdbqt.replace('.pdbqt', '_ligand')
    files = [f'{base}.{i}.pdbqt' for i in range(len(names))]  # vina_split numbering unknown; glob instead
    import glob
    files = sorted(glob.glob(base + '.*.pdbqt'))
    return files

def run_vina(pdbqt_path):
    name = os.path.basename(pdbqt_path).replace('.pdbqt', '')
    outp = f'{OUT}/{name}.out.pdbqt'
    if os.path.exists(outp):
        return name, None, True
    cfg = (f'receptor = structures/5i85_recA_ZN_rigid.pdbqt\n'
           f'ligand = {pdbqt_path}\n'
           f'center_x = {CENTER[0]}\ncenter_y = {CENTER[1]}\ncenter_z = {CENTER[2]}\n'
           f'size_x = {SIZE}\nsize_y = {SIZE}\nsize_z = {SIZE}\n'
           f'exhaustiveness = 8\nseed = 42\nnum_modes = 5\nout = {outp}\n')
    cfgf = f'{WORK}/{name}.cfg'
    open(cfgf, 'w').write(cfg)
    r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not os.path.exists(outp):
        return name, None, False
    score = None
    for l in open(outp):
        if l.startswith('MODEL'):
            continue
    # best affinity = first REMARK VINA RESULT
    for l in open(outp):
        if 'VINA RESULT' in l:
            score = float(l.split()[3])
            break
    return name, score, True

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'refs'
    if mode == 'refs':
        merged, names = prepare_all(['data/dock_refs.smi'], 'refs')
        files = split_ligands(merged, 'refs')
        print('ref ligands prepared:', files)
        for fp in files:
            name, score, ok = run_vina(fp)
            print(name, score, 'ok' if ok else 'FAILED')
    elif mode == 'prep':
        merged, names = prepare_all(['data/dock_set.smi'], 'main')
        files = split_ligands(merged, 'main')
        print('prepared', len(files), 'ligands')
        with open('data/prep_names.txt', 'w') as f:
            f.write('\n'.join(names))
    elif mode == 'dock':
        import glob, time
        files = sorted(glob.glob(f'{WORK}/merged_main_ligand.*.pdbqt'))
        print('docking', len(files), 'ligands on', min(20, os.cpu_count()), 'workers')
        t0 = time.time(); done = 0
        results = []
        with ThreadPoolExecutor(max_workers=20) as ex:
            futs = {ex.submit(run_vina, fp): fp for fp in files}
            for f in as_completed(futs):
                name, score, ok = f.result()
                done += 1
                if score is not None:
                    results.append((name, score))
                if done % 200 == 0:
                    print(f'{done}/{len(files)} done, {time.time()-t0:.0f}s, last={score}', flush=True)
        with open('docking/vina_scores.csv', 'w', newline='') as fh:
            w = csv.writer(fh); w.writerow(['ligand', 'vina_best'])
            w.writerows(sorted(results, key=lambda x: x[1]))
        print(f'DONE {len(results)} docked in {round(time.time()-t0)}s')
