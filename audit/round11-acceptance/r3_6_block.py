# R3-6 replay: sign-preserving parse - one docking-score per reference, all required.
import re as _re2
_sa = open('structure-analysis.md', encoding='utf-8').read()
sec = _sa[_sa.find('Reference-inhibitor docking'):]
row_txt = sec.split('Empirical benchmark')[0]
keep = [l for l in row_txt.splitlines() if 'CHEMBL418376' in l and 'CHEMBL5284579' in l]
assert len(keep) == 1, f'R3-6 replay: expected the combined reference line, found {len(keep)}'
vals = []
for m3 in _re2.finditer(r'\*\*([−-]?\d+\.\d+)\*\*', keep[0]):
    vals.append(float(m3.group(1).replace('−', '-')))
assert len(vals) == 3, f'R3-6 replay: expected 3 bold docking scores, got {vals}'
detected_36 = not any(v <= -7.0 for v in vals)  # TRUE expected: none <= -7
print('R3-6 replay values parsed:', vals, flush=True)
rec('R3-6', 'numeric-consistency', 'structure-analysis.md reference-inhibitor table',
    'executed check: none of the cited table values <= -7.0', f'values={vals}',
    detected_36, 'sign-preserving parse of the cited row')

