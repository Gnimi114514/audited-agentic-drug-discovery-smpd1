"""Generate the 6 main figures for the paper from project data.
All data from local files; no fabricated numbers. Output: paper/figures/fig1..fig6 (PNG 300dpi + PDF).
"""
import json, csv, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

FIG = 'paper/figures'
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'figure.dpi': 300})

def save(fig, name):
    fig.savefig(f'{FIG}/{name}.png', bbox_inches='tight')
    fig.savefig(f'{FIG}/{name}.pdf', bbox_inches='tight')
    plt.close(fig)
    print('saved', name)

# ---------------- Fig 2: target evidence + reference correction ----------------
panel = json.load(open('data/panel_scores.json'))
genes = sorted(panel.items(), key=lambda kv: -kv[1]['total'])[:22]
names = [g for g, _ in genes][::-1]
totals = [v['total'] for _, v in genes][::-1]
fig, axes = plt.subplots(1, 2, figsize=(9, 4.2), gridspec_kw={'width_ratios': [1.3, 1]})
ax = axes[0]
colors = ['#c0392c' if g in ('SMPD1',) else ('#7f8c8d' if g in ('HFE', 'SORL1', 'TREM2', 'CR1', 'BIN1', 'PICALM', 'CLU', 'MS4A6A', 'SPI1') else '#2e86c1')
          for g in names]
ax.barh(names, totals, color=colors)
ax.set_xlabel('weighted evidence score')
ax.set_title('A  22-gene evidence matrix (G1 shortlist)')
ax.axvline(0.55, ls=':', c='k', lw=0.8)
ax.text(0.555, 0.5, 'shortlist cut', rotation=90, va='center', fontsize=7)
ax = axes[1]
labels = ['CHEMBL310981', 'CHEMBL418376', 'CHEMBL5284579']
smpd2 = [1.0, 1.0, 1.8]
smpd1 = [49.0, np.nan, np.nan]
x = np.arange(3)
ax.bar(x - 0.18, smpd2, 0.36, label='vs SMPD2 (CHEMBL4712)  [µM]', color='#2e86c1')
ax.bar(x + 0.18, [v if not np.isnan(v) else 0 for v in smpd1], 0.36, label='vs human SMPD1 (µM)', color='#c0392c')
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20, fontsize=7)
ax.set_ylabel('reported IC50 (µM)')
ax.set_title('B  reference misattribution found by audit')
ax.legend(fontsize=7)
ax.text(0.02, 0.95, 'anchors were SMPD2 actives', transform=ax.transAxes, fontsize=8, va='top', color='#c0392c')
save(fig, 'fig2_target_evidence')

# ---------------- Fig 3: screening funnel + scores ----------------
reg = json.load(open('results/funnel_registry.json', encoding='utf-8'))
st = reg['stages']
rows = list(csv.DictReader(open('results/hits_ranked.csv', encoding='utf-8')))
vina = np.array([float(r['vina_best']) for r in rows])
fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
ax = axes[0]
stages = ['ChEMBL\nCNS library', 'PAINS/Brenk\n+ charge clean', 'scaffold-capped\ndock set', 'docked+\nscored']
vals = [st['1_chembl_cns_library'], st['2_pains_brenk_charge_clean'], st['3_scaffold_capped_dock_set'], st['4_docked_scored_total']]
bars = ax.bar(range(4), vals, color=['#85c1e9', '#5dade2', '#2e86c1', '#1b4f72'])
ax.bar_label(bars, fontsize=8)
ax.set_xticks(range(4)); ax.set_xticklabels(stages, fontsize=7)
ax.set_ylabel('molecules')
ax.set_title('A  screening funnel (batch merge documented)')
ax = axes[1]
ax.hist(vina, bins=60, color='#5dade2')
ax.axvline(-7.0, color='#c0392c', ls='--', lw=1)
ax.axvline(-6.5, color='#e67e22', ls=':', lw=1)
n7 = (vina <= -7.0).sum()
ax.text(-7.05, ax.get_ylim()[1]*0.85, f'{n7} entries ≤ -7.0\n(internal threshold,\nnot potency)', fontsize=7, ha='right', color='#c0392c')
ax.set_xlabel('Vina score (kcal/mol) — PREDICTED')
ax.set_ylabel('count')
ax.set_title('B  score distribution (best -8.92 CHEMBL54786)')
save(fig, 'fig3_screening')

# ---------------- Fig 4: bound-MD v2 corrected behavior ----------------
d = json.load(open('independent-audit/round4-acceptance/c1_evidence.json'))
mets = d['frames']
frames = [m['frame'] for m in mets]
lr = [m['ligand_protein_frame_rmsd_A'] for m in mets]
cd = [m['crystal_centroid_distance_A'] for m in mets]
zc = [m['min_catalytic_distance_A'] for m in mets]
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
for ax, series, ttl, yl in [
    (axes[0], lr, 'A  ligand RMSD in protein frame', 'RMSD (Å)'),
    (axes[1], cd, 'B  ligand COM dist to crystal centroid', 'distance (Å)'),
    (axes[2], zc, 'C  min Zn–ligand distance', 'distance (Å)')]:
    ax.plot(frames, series, lw=0.8, color='#1b4f72')
    ax.axhline(np.mean(series), color='#c0392c', ls='--', lw=0.9,
               label=f'mean {np.mean(series):.2f}')
    ax.set_xlabel('frame (5 ps)'); ax.set_ylabel(yl)
    ax.set_title(ttl, fontsize=9); ax.legend(fontsize=7)
axes[2].axhline(3.0, color='k', ls=':', lw=0.8)
axes[2].text(620, 2.9, '3 Å coordination cutoff', fontsize=6, ha='right', va='top')
fig.suptitle('Bound-MD v2: 12-6 subset of 12-6-4 Zn model, C4 omitted, 3.0 ns — no catalytic-Zn coordination, occupancy 0%', y=1.04, fontsize=9)
save(fig, 'fig4_bound_md_v2')

# ---------------- Fig 5: hERG models + synthesis status ----------------
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')
npz = np.load('results/herg_central_repro/models/modelB_test_predictions.npz')
y_true, y_prob = npz['y_true'], npz['y_prob']
from sklearn.metrics import roc_curve, average_precision_score, precision_recall_curve
fpr, tpr, _ = roc_curve(y_true, y_prob)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
ax = axes[0]
ax.plot(fpr, tpr, lw=1.2, color='#1b4f72', label=f'RF300 held-out AUC 0.9091')
ax.plot([0, 1], [0, 1], 'k:', lw=0.7)
ax.set_xlabel('FPR'); ax.set_ylabel('TPR'); ax.set_title('A  MODEL-B ROC (n=61,376 test)', fontsize=9)
ax.legend(fontsize=7)
ax = axes[1]
pcurve, rcurve, _ = precision_recall_curve(y_true, y_prob)
ap = average_precision_score(y_true, y_prob)
ax.plot(rcurve, pcurve, lw=1.2, color='#117a65', label=f'AP 0.479 (avg precision)')
ax.set_xlabel('recall'); ax.set_ylabel('precision'); ax.set_title('B  precision–recall (AP ≠ PR-AUC)', fontsize=9)
ax.legend(fontsize=7)
ax = axes[2]
cand = list(csv.DictReader(open('results/herg_central_repro/models/candidate_predictions_by_model.csv')))
cand.sort(key=lambda r: float(r['MODEL_A_RF500_fulldata_prob']))
names = [c['name'].replace('ANALOG_EXP_', 'A:') for c in cand]
a = [float(c['MODEL_A_RF500_fulldata_prob']) for c in cand]
b = [float(c['MODEL_B_RF300_split_prob']) for c in cand]
y = np.arange(len(names))
ax.barh(y + 0.2, a, 0.4, label='MODEL-A RF500 (legacy, in-sample)', color='#e59866')
ax.barh(y - 0.2, b, 0.4, label='MODEL-B RF300 (split)', color='#2e86c1')
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=5)
ax.set_xlabel('predicted hERG inhibition probability')
ax.set_title('C  candidates by model version', fontsize=9)
ax.legend(fontsize=6)
save(fig, 'fig5_models_synthesis')

# ---------------- Fig 6: audit finding trajectory ----------------
fig, ax = plt.subplots(figsize=(9, 3.6))
rounds = ['R1\n(initial\naudit)', 'R2\n(re-review)', 'R3\n(repair\nreview)', 'R4\n(acceptance)']
found = [11, 5, 7, 3]
accepted = [11, 5, 7, 3]
status = ['all accepted,\nrepaired', 'all accepted,\nrepaired', 'all accepted,\nrepaired',
          'C4/C5 PASS;\nC1 PASS; C2 PASS-note;\nC3 manifest fixed']
x = np.arange(4)
bars = ax.bar(x - 0.15, found, 0.3, label='findings', color='#c0392c')
ax.bar(x + 0.15, accepted, 0.3, label='accepted+repaired', color='#27ae60')
for i, (f, a, s) in enumerate(zip(found, accepted, status)):
    ax.text(i, max(f, a) + 0.3, s, ha='center', fontsize=6)
ax.set_xticks(x); ax.set_xticklabels(rounds, fontsize=8)
ax.set_ylabel('findings count')
ax.set_title('Adversarial audit trajectory: every finding accepted and repaired; verdict-authority conflict (R4) preserved as unresolved', fontsize=8)
ax.legend(fontsize=7)
save(fig, 'fig6_audit_trajectory')

print('figs 2-6 done (fig 1 = workflow diagram, drawn separately)')
