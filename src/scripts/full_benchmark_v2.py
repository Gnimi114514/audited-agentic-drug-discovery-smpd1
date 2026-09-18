"""Full benchmark v2: 2 workers, incremental save, rate-limit-safe.

35 remaining tasks × 3 arms = 105 executions.
State saved after every execution. Resume from where it left off.
"""
import json, os, subprocess, time, hashlib, shutil, sys, threading
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
BENCH = WORK / 'runs' / 'benchmark-v1'
STATE_F = BENCH / 'full_v2_state.json'
RESULTS_F = BENCH / 'full_v2_results.json'
CODEX = shutil.which('codex') or shutil.which('codex.cmd') or 'codex'

manifest = json.load(open(WORK / 'paper' / 'workflow-study' / 'DATA_SPLIT_MANIFEST.json'))
all_tasks = manifest['tasks']
# Only T006+ (T001-T005 already done in pilot)
remaining = [t for t in all_tasks if t['task_id'] > 'T005']
print(f'Remaining tasks: {len(remaining)} (T006-T0{len(all_tasks):03d})', flush=True)

TASK_PROMPTS = {
    'structure-prep': "Given PDB 5I85 (human acid sphingomyelinase with Zn and phosphocholine), describe receptor preparation for docking. List chains, heteroatoms, protonation pH 7.4, missing atoms, active-site residues. Output JSON. Save to output.json.",
    'virtual-screen': "Given 5 SMILES: [CC(=O)Oc1ccccc1C(=O)O, N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1, O=C1NCN(c2ccccc2)C12CCN(C1Cc3ccccc3)CC2, O=C1Cc2cc(CCN3CCN(c4cccc5ccccc45)CC3)ccc2N1, c1ccc2ncccc2c1CN1CCN(C)CC1], rank by drug-likeness. Output JSON. Save to output.json.",
    'md-analysis': "Given 620-frame MD trajectory (5 ps/frame) of protein-ligand + 2 Zn, describe analysis for pocket residence, Zn-ligand distance, backbone stability. Output JSON. Save to output.json.",
    'route-planning': "Given CHEMBL7385 (N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1), identify retrosynthetic disconnections. Output JSON. Save to output.json.",
    'target-evidence': "For cognitive impairment in Alzheimer's disease, produce ranked shortlist of 3 targets with evidence. Output JSON. Save to output.json.",
}

ARM_WRAP = {
    'A': lambda p: p,
    'B': lambda p: "Multi-agent team task:\n\n" + p + "\n\nCoordinate with target-analyst, molecular-designer, and simulation-analyst perspectives.",
    'C': lambda p: "Audited multi-agent team task. An independent auditor will review for identity errors, unit errors, and overclaims.\n\n" + p + "\n\nSelf-check before producing final output.",
}

# Load previous results if any
results = []
done_keys = set()
if RESULTS_F.exists():
    try:
        results = json.load(open(RESULTS_F))
        done_keys = {f"{r['task_id']}_{r['arm']}" for r in results}
        print(f'Resuming: {len(done_keys)} already done', flush=True)
    except Exception:
        pass

state_lock = threading.Lock()

def save_state():
    with state_lock:
        json.dump({'completed': sorted(done_keys), 'n_results': len(results),
                   'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')},
                  open(STATE_F, 'w'), indent=1)

def run_one(task, arm):
    key = f"{task['task_id']}_{arm}"
    tid = task['task_id']
    family = task['family']
    prompt_template = TASK_PROMPTS.get(family)
    if not prompt_template:
        return None

    prompt = ARM_WRAP[arm](prompt_template)
    tdir = BENCH / f'arm-{arm}' / tid
    tdir.mkdir(parents=True, exist_ok=True)
    outp = tdir / 'output.json'

    t0 = time.time()
    try:
        r = subprocess.run([CODEX, 'exec', '--skip-git-repo-check',
                           '--dangerously-bypass-approvals-and-sandbox',
                           '-C', str(WORK), '-'],
                          input=prompt, capture_output=True, text=True,
                          timeout=600, encoding='utf-8', errors='replace',
                          cwd=str(WORK))
        elapsed = time.time() - t0
        artifact_ok = outp.exists() and outp.stat().st_size > 50
        content = outp.read_text(encoding='utf-8', errors='replace')[:500] if outp.exists() else None
        return {'task_id': tid, 'arm': arm, 'family': family, 'variant': task['variant'],
                'elapsed_s': round(elapsed, 1), 'artifact_ok': artifact_ok,
                'artifact_size': outp.stat().st_size if outp.exists() else 0,
                'content_preview': content, 'exit_code': r.returncode}
    except subprocess.TimeoutExpired:
        return {'task_id': tid, 'arm': arm, 'family': family, 'variant': task['variant'],
                'elapsed_s': round(time.time()-t0, 1), 'artifact_ok': False,
                'error': 'TIMEOUT'}
    except Exception as e:
        return {'task_id': tid, 'arm': arm, 'family': family, 'variant': task['variant'],
                'elapsed_s': round(time.time()-t0, 1), 'artifact_ok': False,
                'error': str(e)[:200]}

def main():
    t0 = time.time()
    all_work = [(t, arm) for arm in ['A', 'B', 'C'] for t in remaining
                if f"{t['task_id']}_{arm}" not in done_keys]
    print(f'Total executions needed: {len(all_work)}', flush=True)

    # Build all (task, arm) pairs for the 3 arms
    all_pairs = []
    for arm in ['A', 'B', 'C']:
        for t in remaining:
            key = f"{t['task_id']}_{arm}"
            if key not in done_keys:
                all_pairs.append((t, arm))

    print(f'Executions to run: {len(all_pairs)}', flush=True)
    semaphore = threading.Semaphore(2)  # max 2 concurrent

    def limited_run(task, arm):
        with semaphore:
            result = run_one(task, arm)
            with state_lock:
                if result:
                    results.append(result)
                    done_keys.add(f"{result['task_id']}_{result['arm']}")
                    # Incremental save every 5 results
                    if len(results) % 5 == 0:
                        json.dump(results, open(RESULTS_F, 'w'), indent=1, ensure_ascii=False)
                        save_state()
            time.sleep(30)  # 30s gap between starts to avoid rate limit

    from concurrent.futures import ThreadPoolExecutor, as_completed
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs = {pool.submit(limited_run, t, a): f"{t['task_id']}_{a}" for t, a in all_pairs}
        for i, f in enumerate(as_completed(futs)):
            try:
                f.result()
            except Exception as e:
                print(f'EXC: {e}', flush=True)
            if (i+1) % 10 == 0:
                elapsed = time.time() - t0
                print(f'{i+1}/{len(all_pairs)} done, {elapsed:.0f}s', flush=True)
            save_state()

    # Final save
    json.dump(results, open(RESULTS_F, 'w'), indent=1, ensure_ascii=False)
    save_state()
    print(f'\nALL DONE: {len(results)} results in {time.time()-t0:.0f}s', flush=True)

if __name__ == '__main__':
    main()
