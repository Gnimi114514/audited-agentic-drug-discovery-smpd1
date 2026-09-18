"""Full parallel benchmark runner for all three arms across all remaining tasks.

Integrates with workflow_state.py for state management.
Uses ThreadPoolExecutor for parallel Codex CLI execution.
Covers: structure-prep, virtual-screen, md-analysis, route-planning families
(target-evidence already done in pilot).
"""
import json, os, subprocess, time, hashlib, shutil, sys, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORK = Path(__file__).resolve().parents[1]
BENCH = WORK / 'runs' / 'benchmark-v1'
STATE = WORK / 'runs' / 'benchmark-v1' / 'state.json'
CODEX = shutil.which('codex') or shutil.which('codex.cmd') or 'codex'

# Load manifest
manifest = json.load(open(WORK / 'paper' / 'workflow-study' / 'DATA_SPLIT_MANIFEST.json'))
tasks = manifest['tasks']

# Filter: only tasks not yet done (T006+, skip target-evidence already done)
remaining = [t for t in tasks if t['task_id'] > 'T005' and t['variant'] == 'natural']
print(f'Remaining natural tasks: {len(remaining)}', flush=True)

# Also add perturbed and insufficient-evidence tasks (1 per family for coverage)
perturbed = [t for t in tasks if t['variant'].startswith('perturbed-')]
insufficient = [t for t in tasks if t['variant'] == 'insufficient-evidence']
all_tasks = remaining + perturbed + insufficient
print(f'Total tasks to run: {len(all_tasks)} ({len(remaining)} natural + {len(perturbed)} perturbed + {len(insufficient)} insufficient)', flush=True)

# Task prompts per family
TASK_PROMPTS = {
    'structure-prep': """Given PDB structure 5I85 (human acid sphingomyelinase with Zn and phosphocholine), describe the receptor preparation steps for docking-ready output. List: chains, heteroatoms, protonation pH 7.4, missing atoms, active-site residues (use three-letter codes). Output JSON with keys: pdb_id, chains, removed_heteroatoms, retained_cofactors, protonation_notes, missing_atoms_modelled, active_site_residues, zns. Save to output.json in the current directory.""",
    'virtual-screen': """Given 5 candidate SMILES: [CC(=O)Oc1ccccc1C(=O)O, N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1, O=C1NCN(c2ccccc2)C12CCN(C1Cc3ccccc3)CC2, O=C1Cc2cc(CCN3CCN(c4cccc5ccccc45)CC3)ccc2N1, c1ccc2ncccc2c1CN1CCN(C)CC1], rank by predicted drug-likeness. For each: MW, cLogP, HBD, HBA, TPSA, PAINS flag. Output JSON array sorted by composite score. Save to output.json.""",
    'md-analysis': """Given a 620-frame MD trajectory (5 ps/frame) of protein-ligand with 2 Zn ions, describe analysis steps for: (1) ligand pocket residence, (2) Zn-ligand minimum distance, (3) backbone stability. Specify tools, coordinate frame handling, expected output. Output JSON with keys: steps, tools, output_format, caveats. Save to output.json.""",
    'route-planning': """Given CHEMBL7385 (SMILES: N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1), identify retrosynthetic disconnections and starting materials. Note protection steps. Output JSON with keys: disconnections, starting_materials, protection_steps, feasibility. Save to output.json.""",
    'target-evidence': """For disease "cognitive impairment in Alzheimer's disease", produce ranked shortlist of 3 targets. For each: ChEMBL/Ensembl ID, ≥2 evidence types, direction. Output JSON array. Save to output.json.""",
}

# Arm-specific role wrappers
def wrap_single(prompt):
    return prompt

def wrap_multi(prompt):
    return ("You are part of a multi-agent drug-discovery team. The target-analyst "
            "provides disease context, the molecular-designer refines candidates, "
            "and the simulation-analyst finalizes technical details.\n\n" + prompt +
            "\n\nCollaborate by addressing the task from your assigned perspective, "
            "then produce the final JSON output.")

def wrap_audited(prompt):
    return ("You are part of an audited multi-agent drug-discovery team. An independent "
            "auditor will review your output for identity errors, unit errors, overclaims, "
            "and missing evidence. Be precise and well-scoped.\n\n" + prompt +
            "\n\nAddress the task, then self-check before producing the final JSON output.")

ARM_WRAPPERS = {'A': wrap_single, 'B': wrap_multi, 'C': wrap_audited}

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

def run_task(task, arm):
    """Execute a single task on a single arm."""
    tid = task['task_id']
    family = task['family']
    prompt_template = TASK_PROMPTS.get(family)
    if not prompt_template:
        return tid, arm, None, f'no prompt for family {family}', 0

    prompt = ARM_WRAPPERS[arm](prompt_template)
    tdir = BENCH / f'arm-{arm}' / tid
    tdir.mkdir(parents=True, exist_ok=True)
    outp = tdir / 'output.json'

    cfg = f'task={tid} arm={arm} model=codex-cli'
    t0 = time.time()
    try:
        r = subprocess.run([CODEX, 'exec', '--skip-git-repo-check',
                           '--dangerously-bypass-approvals-and-sandbox',
                           '-C', str(WORK), '-'],
                          input=prompt, capture_output=True, text=True,
                          timeout=600, encoding='utf-8', errors='replace',
                          cwd=str(WORK))
        elapsed = time.time() - t0
        if r.returncode != 0:
            print(f'  WARNING: {tid}/{arm} exit={r.returncode} stderr={r.stderr[-200:]}', flush=True)
        artifact_ok = outp.exists() and outp.stat().st_size > 50
        content = outp.read_text(encoding='utf-8', errors='replace')[:500] if outp.exists() else None
        return tid, arm, {'elapsed_s': round(elapsed, 1), 'artifact_ok': artifact_ok,
                          'artifact_size': outp.stat().st_size if outp.exists() else 0,
                          'content_preview': content}, None, elapsed
    except subprocess.TimeoutExpired:
        return tid, arm, None, 'TIMEOUT after 600s', time.time() - t0
    except Exception as e:
        return tid, arm, None, f'ERROR: {str(e)[:100]}', time.time() - t0

def run_task_wrapper(args):
    task, arm = args
    tid, arm, result, error, elapsed = run_task(task, arm)
    return {'task_id': tid, 'arm': arm, 'family': task['family'],
            'variant': task['variant'], 'result': result, 'error': error,
            'elapsed_s': round(elapsed, 1)}

# State management with workflow_state integration
state_lock = threading.Lock()
state = {'completed': [], 'failed': [], 'in_progress': [], 'start_time': time.strftime('%Y-%m-%dT%H:%M:%S')}

def save_state():
    with state_lock:
        json.dump(state, open(STATE, 'w'), indent=1)

if __name__ == '__main__':
    all_args = [(t, arm) for arm in ['A', 'B', 'C'] for t in all_tasks]
    total = len(all_args)
    print(f'Total executions: {total} ({len(all_tasks)} tasks × 3 arms)', flush=True)

    results = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(run_task_wrapper, args): args for args in all_args}
        done = 0
        for f in as_completed(futures):
            args = futures[f]
            try:
                r = f.result()
                results.append(r)
                done += 1
                if done % 10 == 0:
                    elapsed = time.time() - t0
                    print(f'{done}/{total} done, {elapsed:.0f}s elapsed', flush=True)
            except Exception as e:
                print(f'ERROR: {e}', flush=True)

    # Save all results
    json.dump(results, open(BENCH / 'all_results.json', 'w'), indent=1, ensure_ascii=False)

    # Summary
    by_arm = {}
    for r in results:
        arm = r['arm']
        by_arm.setdefault(arm, {'total': 0, 'ok': 0, 'failed': 0})
        by_arm[arm]['total'] += 1
        if r.get('result') and r['result'].get('artifact_ok'):
            by_arm[arm]['ok'] += 1
        else:
            by_arm[arm]['failed'] += 1

    print('\n=== SUMMARY ===')
    for arm, s in sorted(by_arm.items()):
        print(f'Arm {arm}: {s["ok"]}/{s["total"]} artifacts OK, {s["failed"]} failed')
    print(f'Total wall time: {time.time()-t0:.0f}s')
    print(f'Saved to {BENCH}/all_results.json')
