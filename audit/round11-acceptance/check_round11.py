import ast, hashlib, json, subprocess, sys, io, contextlib
from pathlib import Path
from datetime import datetime, timezone

out = Path(__file__).resolve().parent
root = out.parents[1]
def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()
checks = {'timestamp': datetime.now(timezone.utc).isoformat(), 'python': sys.executable}
manifest = json.loads((root/'audit_manifest.json').read_text())
entries = []
for level, rows in manifest['levels'].items():
    for row in rows:
        p = root/row['path']
        actual = digest(p) if p.is_file() else None
        size = p.stat().st_size if p.is_file() else None
        entries.append(dict(level=level, path=row['path'], expected_sha256=row['sha256'], actual_sha256=actual, bytes=size, passed=actual==row['sha256'] and size==row['bytes']))
checks['manifest'] = dict(count=len(entries), levels={k:len(v) for k,v in manifest['levels'].items()}, passed=len(entries)==77 and all(x['passed'] for x in entries), entries=entries)
checks['handoffs'] = []
checker = Path('C:/Users/Gnimi/.agents/skills/ai-drug-discovery-team/scripts/check_handoff.py')
for p in sorted((root/'runs/audit-20260913').glob('handoff-r11-*.json')):
    cmd = [sys.executable, '-B', str(checker), str(p), '--root', str(root), '--require', 'artifacts']
    r = subprocess.run(cmd, capture_output=True, text=True)
    checks['handoffs'].append(dict(path=str(p.relative_to(root)), command=cmd, exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr))
r = subprocess.run([sys.executable, '-B', str(out/'run_replay.py')], cwd=root, capture_output=True, text=True)
(out/'replay_stdout.txt').write_text(r.stdout, encoding='utf-8')
(out/'replay_stderr.txt').write_text(r.stderr, encoding='utf-8')
replay = json.loads((out/'real_findings_replay_executed.json').read_text())
checks['replay'] = dict(exit_code=r.returncode, **replay)
source = (root/'scripts/findings_replay_executed.py').read_text(encoding='utf-8')
block = source[source.index('# R3-6 replay:'):source.index('# R1-10 appended BEFORE counting')]
(out/'r3_6_block.py').write_text(block, encoding='utf-8')
original = (root/'structure-analysis.md').read_text(encoding='utf-8')
scores = ['**\u22126.96**', '**\u22126.34**', '**\u22126.01**']
variants = {'baseline': original, 'all_missing': original, 'all_below_threshold': original, 'one_missing': original.replace(scores[0], 'NA'), 'empty': ''}
for s in scores:
    assert original.count(s)==1
    variants['all_missing'] = variants['all_missing'].replace(s, 'NA')
    variants['all_below_threshold'] = variants['all_below_threshold'].replace(s, '**-8.00**')
checks['mutations'] = []
for name, content in variants.items():
    p = out/f'structure-analysis-{name}.md'
    p.write_text(content, encoding='utf-8')
    def redirected_open(path, *args, **kwargs):
        assert path == 'structure-analysis.md'
        return open(p, *args, **kwargs)
    ns = {'open': redirected_open, 'rec': lambda *args, **kwargs: None}
    error = None
    try:
        with contextlib.redirect_stdout(io.StringIO()): exec(compile(block, str(out/'r3_6_block.py'), 'exec'), ns)
    except AssertionError as e: error = str(e)
    accepted = error is None and ns.get('detected_36') is True
    checks['mutations'].append(dict(name=name, copy=str(p.relative_to(root)), values=ns.get('vals'), assertion=error, detected=ns.get('detected_36'), passed=accepted if name=='baseline' else not accepted))
hit = (root/'hit-report.md').read_text(encoding='utf-8')
checks['reports'] = {'withdrawn_paragraph_absent': 'Their docked scores here are' not in hit, 'withdrawn_assertion_absent': 'chemotypes still show that the pocket/protocol yields' not in hit, 'dangling_fragment_absent': 'campaign); flexible-loop' not in original, 'merged_ensemble_sentence_present': 'rotamer ensembles). Flexible-loop (SMD/MD) effects on the entry channel are unassessed.' in original}
byid = {r['id']:r for r in replay['replays']}
checks['claims'] = {
 'R10-1': 'PASS' if r.returncode==0 and replay['summary']['executed_replays']==13 and byid['R3-6']['observed']=='values=[-6.96, -6.34, -6.01]' and byid['R3-6']['detected'] and byid['R1-10']['observed'].startswith('1.757 A') and all(m['passed'] for m in checks['mutations']) else 'FAIL',
 'R10-2a': 'PASS' if checks['reports']['withdrawn_paragraph_absent'] and checks['reports']['withdrawn_assertion_absent'] else 'FAIL',
 'R10-2b': 'PASS' if checks['reports']['dangling_fragment_absent'] and checks['reports']['merged_ensemble_sentence_present'] else 'FAIL',
 'manifests': 'PASS' if checks['manifest']['passed'] and len(checks['handoffs'])==2 and all(x['exit_code']==0 for x in checks['handoffs']) else 'FAIL'}
checks['frozen_hashes_unchanged_after_execution'] = all(digest(root/x['path'])==x['actual_sha256'] for x in entries)
checks['overall'] = 'ACCEPT-WITH-MINOR-NOTES' if all(v=='PASS' for v in checks['claims'].values()) and checks['frozen_hashes_unchanged_after_execution'] else 'REJECT'
checks['G6_recommendation'] = 'CONDITIONAL: close R10-1/R10-2 acceptance blockers; retain inherited scientific limitations and incomplete validations.' if checks['overall']!='REJECT' else 'BLOCKED'
(out/'round11_checks.json').write_text(json.dumps(checks, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({k: checks[k] for k in ('claims','overall','G6_recommendation','frozen_hashes_unchanged_after_execution')}, indent=2))
