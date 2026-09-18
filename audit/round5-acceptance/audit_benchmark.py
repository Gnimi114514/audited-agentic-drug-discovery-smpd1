import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
rerun_dir = OUT / 'benchmark-rerun'
rerun_dir.mkdir(exist_ok=True)
seed_path = ROOT / 'scripts/seeded_benchmark.py'
replay_path = ROOT / 'scripts/findings_replay.py'
seed_source = seed_path.read_text(encoding='utf-8')
replay_source = replay_path.read_text(encoding='utf-8')
namespace = {}
stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    exec(compile(seed_source.replace("WORK = 'runs/benchmark-seeded'", 'WORK = ' + repr(rerun_dir.as_posix())), str(seed_path), 'exec'), namespace)
    exec(compile(replay_source.replace("'runs/benchmark-seeded/real_findings_replay.json'", repr((rerun_dir / 'real_findings_replay.json').as_posix())), str(replay_path), 'exec'), {})
(OUT / 'benchmark-rerun.log').write_text(stdout.getvalue(), encoding='utf-8')
seed = json.loads((ROOT / 'runs/benchmark-seeded/benchmark_results.json').read_text())
replay = json.loads((ROOT / 'runs/benchmark-seeded/real_findings_replay.json').read_text())
seed_run = json.loads((rerun_dir / 'benchmark_results.json').read_text())
replay_run = json.loads((rerun_dir / 'real_findings_replay.json').read_text())
seeded = [x for x in seed['cases'] if 'control' not in x['site']]
controls = [x for x in seed['cases'] if 'control' in x['site']]
replayable = [x for x in replay['findings'] if x['replayable']]
context = [x for x in replay['findings'] if not x['replayable']]
checks = {
    'stored_seeded_results_arithmetic': {'pass': len(seeded) == 5 and len({x['class'] for x in seeded}) == 5 and all(x['detected'] for x in seeded) and len(controls) == 5 and not any(x['detected'] for x in controls), 'seeded': len(seeded), 'controls': len(controls), 'summary': seed['summary']},
    'seeded_rerun': {'pass': seed_run['cases'] == seed['cases'] and seed_run['summary'] == seed['summary'], 'excluded_comparison_fields': ['generated']},
    'stored_replay_results_arithmetic': {'pass': len(replayable) == 13 and all(x['replay'] == 'detected' for x in replayable) and len(context) == 5 and [x['id'] for x in context] == replay['summary']['context_or_live_only'], 'replayable_count': len(replayable), 'context_live_only': [x['id'] for x in context]},
    'replay_script_reproduces_stored_result': {'pass': replay_run == replay, 'difference': {'summary.detection_rate_deterministic': {'stored': replay['summary']['detection_rate_deterministic'], 'rerun': replay_run['summary']['detection_rate_deterministic']}}},
    'actual_artifact_replay_implemented': {'pass': False, 'evidence': 'scripts/findings_replay.py:19-85 hardcodes detected statuses. Its only open() call is line 109, writing output. No artifact read, detector invocation, or erroneous-state reconstruction is implemented. Lines 91-96 count hardcoded detected statuses for both denominator and numerator.'},
    'seeded_design_matches_implementation': {'pass': False, 'evidence': 'scripts/seeded_benchmark.py:6-9 claims 15 injection sites and 15 controls; executed implementation has 5 and 5. E1-E4 are in-memory constants rather than copied project artifacts; only E5 reads/writes a canary.'},
    'historical_wrong_parameter_set_challenge': {'detected': not namespace['check_E3'](0.00330286, 2.0), 'expected_if_claimed_2014': True, 'evidence': 'scripts/seeded_benchmark.py:62-68 accepts either 2013 or 2014 epsilon. Seed uses neither-set epsilon 0.01234567, so 5/5 does not demonstrate detection of historical R1-3 wrong-set error.'},
}
out = {
    'scope': 'Mandatory item 5, benchmark existence, internal arithmetic, producing-script reproducibility and actual replay provenance',
    'verdict': 'FAIL_SUBSTANTIVE_REPLAY_CLAIM; stored numeric requirements pass',
    'checks': checks,
    'mandatory_repairs': [
        'Implement actual artifact-backed checks for the claimed 13 replayable findings (with frozen erroneous inputs, detector execution, observations and per-case result); derive denominator from replayable cases, not detected cases. Until executed, label this file a manually curated coverage inventory and withdraw claims that deterministic replays were run.',
        'Make findings_replay.py regenerate the corrected 13/13 and 5 context/live-only summary and regenerate benchmark artifacts and dependent manifests.',
        'Correct seeded benchmark documentation to the executed 5-case/5-control design or execute the stated 15-site design; describe simplified fixtures and parameter-set limitations accurately.'
    ],
    'limits': ['No broader sensitivity estimate follows from these five hand-constructed checks.', 'This audit reruns the supplied producing scripts with output paths redirected only; it does not turn their hardcoded replay labels into independently executed checks.'],
    'input_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in [seed_path, replay_path, ROOT / 'runs/benchmark-seeded/benchmark_results.json', ROOT / 'runs/benchmark-seeded/real_findings_replay.json']},
    'write_scope': 'All rerun and audit writes were confined to independent-audit/round5-acceptance.'
}
(OUT / 'benchmark_checks.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
