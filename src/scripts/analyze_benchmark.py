"""Analyze full benchmark v2 results and generate BENCHMARK_REPORT.md content."""
import json, os, sys
import numpy as np

RESULTS_F = 'runs/benchmark-v1/full_v2_results.json'
REPORT_F = 'paper/workflow-study/BENCHMARK_REPORT.md'

if not os.path.exists(RESULTS_F) or os.path.getsize(RESULTS_F) < 10:
    print('No results yet. Benchmark still running or not started.')
    sys.exit(0)

results = json.load(open(RESULTS_F))
print(f'Total results: {len(results)}', flush=True)

# Per-arm summary
arms = {}
for r in results:
    arm = r['arm']
    arms.setdefault(arm, []).append(r)

summary = {}
for arm, data in sorted(arms.items()):
    ok = [r for r in data if r.get('artifact_ok')]
    times = [r['elapsed_s'] for r in ok]
    total_time = sum(times)
    summary[arm] = {
        'total': len(data),
        'artifacts_ok': len(ok),
        'success_rate': f'{len(ok)/len(data)*100:.1f}%' if data else 'N/A',
        'mean_time_s': round(np.mean(times), 1) if times else 0,
        'total_time_min': round(total_time/60, 1),
    }
print('\nPer-arm summary:')
for arm, s in sorted(summary.items()):
    print(f'  {arm}: {s}')

# Per-family breakdown
families = {}
for r in results:
    fam = r.get('family', 'unknown')
    families.setdefault(fam, {'total': 0, 'ok': 0})
    families[fam]['total'] += 1
    if r.get('artifact_ok'):
        families[fam]['ok'] += 1

print('\nPer-family:')
for fam, s in sorted(families.items()):
    print(f'  {fam}: {s["ok"]}/{s["total"]}')

# Per-variant (natural vs perturbed vs insufficient)
variants = {}
for r in results:
    v = r.get('variant', 'unknown')
    variants.setdefault(v, {'total': 0, 'ok': 0})
    variants[v]['total'] += 1
    if r.get('artifact_ok'):
        variants[v]['ok'] += 1

print('\nPer-variant:')
for v, s in sorted(variants.items()):
    print(f'  {v}: {s["ok"]}/{s["total"]}')

# Save analysis
json.dump({'arm_summary': summary, 'family_breakdown': families, 'variant_breakdown': variants},
          open('runs/benchmark-v1/analysis.json', 'w'), indent=1)
print('\nSaved runs/benchmark-v1/analysis.json')
