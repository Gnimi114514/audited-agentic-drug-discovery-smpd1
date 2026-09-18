"""Turn an accepted diagnostic handoff into explicit next-stage constraints."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site-result', type=Path, required=True)
    p.add_argument('--mode', choices=('failure-analysis', 'design-readiness'), required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raw = args.site_result.read_bytes()
    result = json.loads(raw)
    value, threshold = result['ccd_graph_rmsd_A'], result['threshold_A']
    if any(type(x) not in (int, float) or not math.isfinite(x) or x < 0 for x in (value, threshold)):
        raise ValueError('invalid diagnostic metric')
    expected = 'PASS' if value <= threshold else 'FAIL'
    if result['scientific_outcome'] != expected:
        raise ValueError('diagnostic outcome contradicts its numerical criterion')
    if args.mode == 'failure-analysis' and expected != 'FAIL':
        raise ValueError('failure-analysis requires a failed diagnostic')
    output = {'input_sha256': hashlib.sha256(raw).hexdigest(), 'mode': args.mode,
              'diagnostic_outcome': expected, 'rmsd_A': value, 'threshold_A': threshold,
              'full_G2_accepted': False, 'candidate_generation_authorized': False}
    if args.mode == 'failure-analysis':
        output.update(scientific_outcome='PASS',
                      scope='negative-result interpretation completed; no biological or site validation PASS',
                      conclusions=['The recorded first pose exceeds the specified strict-template threshold.',
                                   'This diagnostic does not identify the cause or prove absence of binding.'],
                      next_evidence=['Establish assay-relevant protonation and receptor/metal assumptions.',
                                     'Review CCD-template applicability before testing alternative states.',
                                     'Keep candidate potency ranking uncalibrated until appropriate controls are validated.'])
    else:
        output.update(scientific_outcome='BLOCKED',
                      scope='design readiness requires full site acceptance; a single diagnostic is insufficient',
                      reason='No independently accepted complete G2 handoff is supplied by this diagnostic contract.')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'site-input.json').write_bytes(raw)
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (args.output / 'result.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps({'mode': args.mode, 'outcome': output['scientific_outcome']}))


if __name__ == '__main__':
    main()
