"""Execute the producer R3-6 block against in-memory artifact variants; no source edits."""
from pathlib import Path
import json, io, re
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
src = (root/'scripts/findings_replay_executed.py').read_text(encoding='utf8')
block = src.split('# R3-6:', 1)[1].split('# R1-10 appended', 1)[0]
block = block.split('\n', 1)[1]
original = (root/'structure-analysis.md').read_text(encoding='utf8')
variants = {'current_artifact': original,
            'reference_score_changed_to_minus_7_96': original.replace('−6.96', '−7.96'),
            'empty_artifact': ''}
checks=[]
for name, content in variants.items():
    records=[]
    def rec(*args): records.append(args)
    def read_artifact(path, **kwargs):
        assert path == 'structure-analysis.md'
        return io.StringIO(content)
    env={'open':read_artifact, 'rec':rec}
    exec(compile(block, 'producer_R3_6_block', 'exec'), env)
    checks.append({'variant':name,'parsed_values':env['vals'],'observed':records[0][4],'detected':records[0][5]})
(out/'replay_mutation_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
print(json.dumps(checks,indent=2))
