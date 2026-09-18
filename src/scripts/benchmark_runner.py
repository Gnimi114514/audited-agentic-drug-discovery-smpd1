"""Benchmark runner: dispatch tasks to three arms (A/B/C) and collect results.

Uses Codex CLI for real agent execution. Each arm gets a different configuration:
- Arm A (single agent): one codex exec call per task, no role separation
- Arm B (multi-agent): three sequential codex exec calls (target analyst → designer → simulation analyst)
- Arm C (audited multi-agent): same as B plus a fourth codex exec call (independent auditor)

All arms receive the same task description and have the same tools available.
Fresh context per execution (no shared memory between tasks).
"""
import json, os, subprocess, time, hashlib, shutil
CODEX = shutil.which('codex') or shutil.which('codex.cmd') or 'codex'
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
BENCH = WORK / 'runs' / 'benchmark-v1'
BENCH.mkdir(parents=True, exist_ok=True)

# Load task manifest
manifest = json.load(open(WORK / 'paper' / 'workflow-study' / 'DATA_SPLIT_MANIFEST.json'))
tasks = manifest['tasks']

# Select pilot subset: 1 task per family, natural variant only (5 tasks)
pilot = [t for t in tasks if t['variant'] == 'natural'][:5]

TASK_PROMPTS = {
    'target-evidence': """Given the disease "cognitive impairment in Alzheimer's disease", produce a ranked shortlist of exactly 3 therapeutic target genes. For each: provide the ChEMBL or Ensembl target ID, at least 2 independent evidence types (genetics, literature, animal model, etc.), and a direction-of-modulation hypothesis. Output as JSON array of objects with keys: gene, target_id, evidence_types (array), direction. Save to {output_file}.""",
    'structure-prep': """Given PDB structure 5I85 (human acid sphingomyelinase), describe the receptor preparation steps needed to make it docking-ready. List: (1) chains to keep, (2) heteroatoms to remove/retain, (3) protonation considerations at pH 7.4, (4) missing residues/atoms to model, (5) active-site residue list. Output as a structured JSON with keys: pdb_id, chains, removed_heteroatoms, retained_cofactors, protonation_notes, missing_atoms_modelled, active_site_residues. Save to {output_file}.""",
    'virtual-screen': """Given a set of 5 candidate SMILES strings [CC(=O)Oc1ccccc1C(=O)O, N#Cc1ccccc1N1CCN(C(=O)c2ccccc2[nH]2)CC1, O=C1NCN(c2ccccc2)C12CCN(C1Cc3ccccc3)CC2, O=C1Cc2cc(CCN3CCN(c4cccc5ccccc45)CC3)ccc2N1, c1ccc2ncccc2c1CN1CCN(C)CC1], rank them by predicted drug-likeness. For each: compute MW, cLogP, HBD, HBA, TPSA; flag PAINS alerts if any. Output as JSON array sorted by composite score (higher = more drug-like). Save to {output_file}.""",
    'md-analysis': """Given a molecular dynamics trajectory of a protein-ligand complex (hypothetical: 620 frames, 5 ps per frame), describe the key analysis steps to determine: (1) whether the ligand remains in the binding pocket, (2) the minimum ligand-Zn distance over time, (3) protein backbone stability. Specify the software/tools you would use, the coordinate frame considerations, and the expected output format. Output as JSON with keys: steps (array), tools, output_format, caveats. Save to {output_file}.""",
    'route-planning': """Given the target molecule CHEMBL7385 (SMILES: N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1), identify the key retrosynthetic disconnections and suggest starting materials. Note any protection/deprotection steps needed. Output as JSON with keys: disconnections (array of {bonds_broken, fragments, reaction_class}), starting_materials (array), protection_steps, feasibility_assessment. Save to {output_file}.""",
}

def run_codex(prompt, timeout=600):
    """Execute a single Codex CLI call and return (exit_code, output_text)."""
    cmd = [CODEX, 'exec', '--skip-git-repo-check', '--dangerously-bypass-approvals-and-sandbox',
           '-C', str(WORK), '-']
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                          timeout=timeout, encoding='utf-8', errors='replace', cwd=str(WORK))
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except subprocess.TimeoutExpired:
        return -1, 'TIMEOUT'
    except Exception as e:
        return -2, str(e)

def run_arm(task, arm, attempt_dir):
    """Execute a single task on a single arm."""
    family = task['family']
    base_prompt = TASK_PROMPTS[family].format(output_file=str(attempt_dir / 'output.json'))

    t0 = time.time()
    outputs = []

    if arm == 'A':
        # Single agent: one call
        code, out = run_codex(base_prompt, timeout=600)
        outputs.append({'role': 'executor', 'exit_code': code, 'output_len': len(out)})
        artifact = attempt_dir / 'output.json'

    elif arm == 'B':
        # Multi-agent: 3 sequential role calls
        roles = [
            ('target-analyst', f'You are a target/disease analyst. Task: {base_prompt}'),
            ('molecular-designer', 'You are a molecular designer. Review the previous analysis and refine the output. Task: ' + base_prompt),
            ('simulation-analyst', 'You are a simulation/computational analyst. Finalize the technical details and save the result. Task: ' + base_prompt),
        ]
        prev = ''
        for role, p in roles:
            full = p + ('\n\nPrevious agent output:\n' + prev if prev else '')
            code, out = run_codex(full, timeout=600)
            outputs.append({'role': role, 'exit_code': code, 'output_len': len(out)})
            prev = out[-2000:] if len(out) > 2000 else out
        artifact = attempt_dir / 'output.json'

    elif arm == 'C':
        # Audited multi-agent: same as B plus auditor
        roles = [
            ('target-analyst', f'You are a target/disease analyst. Task: {base_prompt}'),
            ('molecular-designer', 'You are a molecular designer. Task: ' + base_prompt),
            ('simulation-analyst', 'You are a simulation analyst. Task: ' + base_prompt),
            ('independent-auditor', 'You are an independent auditor. Review the previous work for identity errors, unit errors, overclaims, or missing evidence. If corrections are needed, apply them and save the corrected output. Task: ' + base_prompt),
        ]
        prev = ''
        for role, p in roles:
            full = p + ('\n\nPrevious agent output:\n' + prev[-2000:] if prev else '')
            code, out = run_codex(full, timeout=600)
            outputs.append({'role': role, 'exit_code': code, 'output_len': len(out)})
            prev = out[-2000:] if len(out) > 2000 else out
        artifact = attempt_dir / 'output.json'
    else:
        raise ValueError(f'Unknown arm: {arm}')

    elapsed = time.time() - t0
    return {
        'arm': arm, 'task_id': task['task_id'], 'family': family,
        'elapsed_s': round(elapsed, 1), 'agent_calls': len(outputs),
        'outputs': outputs, 'artifact_exists': artifact.exists(),
        'artifact_content': artifact.read_text(encoding='utf-8', errors='replace')[:2000] if artifact.exists() else None,
    }

if __name__ == '__main__':
    arm_name = __import__('sys').argv[1] if len(__import__('sys').argv) > 1 else 'A'
    n_tasks = int(__import__('sys').argv[2]) if len(__import__('sys').argv) > 2 else 5

    arm_dir = BENCH / f'arm-{arm_name}'
    arm_dir.mkdir(parents=True, exist_ok=True)

    print(f'Running arm {arm_name} on {n_tasks} tasks...', flush=True)
    all_results = []
    for i, task in enumerate(pilot[:n_tasks]):
        tid = task['task_id']
        tdir = arm_dir / tid
        tdir.mkdir(parents=True, exist_ok=True)
        print(f'  [{i+1}/{n_tasks}] {tid} ({task["family"]})...', flush=True)
        result = run_arm(task, arm_name, tdir)
        result['task_family'] = task['family']
        all_results.append(result)
        print(f'    done in {result["elapsed_s"]}s, artifact={result["artifact_exists"]}', flush=True)

    json.dump(all_results, open(arm_dir / 'results.json', 'w'), indent=1, ensure_ascii=False)
    print(f'Arm {arm_name} complete: {n_tasks} tasks, results in {arm_dir}/results.json')
