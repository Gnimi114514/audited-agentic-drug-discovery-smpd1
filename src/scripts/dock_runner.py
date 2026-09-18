"""Phase 4: Vina docking runner — one config per ligand, N workers, --cpu 1 each."""
import os, sys, glob, csv, time, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

VINA = 'bin/vina.exe'
PDBQT_DIR = 'docking/pdbqt'
OUT = 'docking/out'
WORK = 'docking/work'
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

CENTER = (-13.710, -34.100, -28.720)
SIZE = 24
CPU_PER = 1
WORKERS = min(20, os.cpu_count())

def run_vina(pdbqt_path):
    name = os.path.basename(pdbqt_path).replace('.pdbqt', '')
    outp = f'{OUT}/{name}.out.pdbqt'
    if os.path.exists(outp):
        try:
            for l in open(outp):
                if 'VINA RESULT' in l:
                    return name, float(l.split()[3]), 'cached'
        except Exception:
            pass
    cfg = (f'receptor = structures/5i85_recA_ZN_rigid.pdbqt\n'
           f'ligand = {pdbqt_path}\n'
           f'center_x = {CENTER[0]}\ncenter_y = {CENTER[1]}\ncenter_z = {CENTER[2]}\n'
           f'size_x = {SIZE}\nsize_y = {SIZE}\nsize_z = {SIZE}\n'
           f'exhaustiveness = 8\nseed = 42\nnum_modes = 5\ncpu = {CPU_PER}\n'
           f'out = {outp}\n')
    cfgf = f'{WORK}/{name}.cfg'
    open(cfgf, 'w').write(cfg)
    try:
        r = subprocess.run([VINA, '--config', cfgf], capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(outp):
            return name, None, f'rc={r.returncode}:{r.stderr[-80:]}'
        for l in open(outp):
            if 'VINA RESULT' in l:
                return name, float(l.split()[3]), 'ok'
        return name, None, 'no-result'
    except subprocess.TimeoutExpired:
        return name, None, 'timeout'

def dock(pattern='*.pdbqt', workers=WORKERS):
    files = sorted(glob.glob(f'{PDBQT_DIR}/{pattern}'))
    print(f'docking {len(files)} ligands, {workers} workers x {CPU_PER} cpu', flush=True)
    t0 = time.time()
    results, fails = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_vina, fp): fp for fp in files}
        for f in as_completed(futs):
            name, score, status = f.result()
            if score is None:
                fails.append((name, status))
            else:
                results.append((name, score, status))
            n = len(results) + len(fails)
            if n % 200 == 0:
                rate = n / (time.time() - t0)
                eta = (len(files) - n) / max(rate, 1e-6) / 60
                print(f'{n}/{len(files)} | {rate:.2f}/s | ETA {eta:.0f} min | last {name} {score}', flush=True)
    with open('docking/vina_scores.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['ligand', 'vina_best', 'status'])
        w.writerows(sorted(results, key=lambda x: x[1]))
    print(f'DONE: {len(results)} scored, {len(fails)} failed in {round(time.time()-t0)}s')
    if fails:
        print('failure sample:', fails[:5])
    return results

if __name__ == '__main__':
    pat = sys.argv[1] if len(sys.argv) > 1 else 'REF_*.pdbqt'
    dock(pat)
