"""Fig 1: workflow/agents/gates/coverage diagram (matplotlib, no external deps)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(11, 5.2))
ax.set_xlim(0, 11); ax.set_ylim(0, 5.6); ax.axis('off')

def box(x, y, w, h, text, fc='#d6eaf8', ec='#1b4f72', fs=8):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.08', fc=fc, ec=ec, lw=1.2)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fs, wrap=True)

def arrow(x1, y1, x2, y2, color='#1b4f72', style='-'):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                 mutation_scale=12, color=color, lw=1.2, linestyle=style))

# pipeline chain
stages = [
    (0.2, 4.3, 'G1 Target\nOpen Targets\nPubMed\n22-gene matrix', '#d6eaf8'),
    (2.1, 4.3, 'G2 Site/Structure\nPDB 5I85/5I81/5JG8\nredocking 1.76 Å\n(lenient conv.)', '#d5f5e3'),
    (4.0, 4.3, 'G3 Design\n20,111→3,500\nVina screen\n225 analogs', '#d6eaf8'),
    (5.9, 4.3, 'G4 Simulation\napo 5.81 ns\nbound v1 6.1 ns\nbound v2 3.0 ns\n(12-6, C4 om.)', '#fadbd8'),
    (8.1, 4.3, 'G6 Integration\nreports+audit\nG6 BLOCKED\n(re-review pend.)', '#fdebd0'),
]
for x, y, t, c in stages:
    box(x, y, 1.7, 1.0, t, fc=c, fs=7)
for x1, x2 in [(1.9, 2.1), (3.8, 4.0), (5.7, 5.9), (7.6, 8.1)]:
    arrow(x1, 4.8, x2, 4.8)

# synthesis branch (blocked)
box(8.1, 2.9, 1.7, 0.9, 'G5 Synthesis\nAiZynthFinder\nZINC stock: 504\n→ PROXY only', fc='#eaeded', ec='#566573', fs=7)
arrow(8.95, 4.3, 8.95, 3.8, color='#566573', style='--')
ax.text(9.9, 3.3, 'service-\nblocked', fontsize=7, color='#566573')

# agents row
box(0.2, 1.7, 2.4, 0.75, 'Producer agent\nGLM/ZCode (this work)', fc='#f9e79f', ec='#9a7d0a', fs=8)
box(3.0, 1.7, 2.6, 0.75, 'Auditor agent\nGPT/Codex — fresh context\n(rounds 1-3 + acceptance)', fc='#f9e79f', ec='#9a7d0a', fs=8)
box(6.0, 1.7, 2.4, 0.75, 'Human supervisor\nconception, oversight,\nfinal decisions', fc='#f9e79f', ec='#9a7d0a', fs=8)

# audit loop arrows
arrow(1.4, 1.7, 1.4, 2.4, color='#9a7d0a')
ax.annotate('', xy=(4.3, 2.45), xytext=(1.4, 1.9),
            arrowprops=dict(arrowstyle='-|>', color='#9a7d0a', lw=1.1,
                            connectionstyle='arc3,rad=-0.25'))
ax.annotate('', xy=(1.4, 2.45), xytext=(4.3, 1.9),
            arrowprops=dict(arrowstyle='-|>', color='#9a7d0a', lw=1.1,
                            connectionstyle='arc3,rad=-0.25'))
ax.text(2.85, 2.75, '3 audit rounds: 23 findings\nall accepted & repaired', fontsize=7,
        ha='center', color='#9a7d0a')

# findings trajectory box
box(0.2, 0.3, 8.2, 0.95,
    'Audit-detected corrections (producer-accepted; per-report findings, repeated objections not deduplicated):  reference µM anchors were SMPD2 not SMPD1  ·  '
    'bound-MD unit/duration/selection errors  ·  Zn params actually Li-2013 12-6 (not 12-6-4)  ·  '
    'direction counterexample (PMID 27598773)  ·  hERG n mislabeled  ·  pocket residence 0% (non-catalytic contacts)  ·  '
    'COM-imaged metric retired  ·  MODEL-A stochastic precision  ·  manifest self-hash/stale-nested fixed',
    fc='#fdedec', ec='#c0392c', fs=7)
arrow(4.3, 1.7, 4.3, 1.25, color='#c0392c')

ax.text(10.0, 5.3, 'verdict authority conflict\n(R4 ACCEPT vs REJECT)\npreserved UNRESOLVED',
        fontsize=6.5, ha='center', color='#7b241c',
        bbox=dict(boxstyle='round', fc='#fdedec', ec='#c0392c', lw=0.8))

ax.set_title('Fig. 1 — Auditable multi-agent pipeline: stages, gates, agents, and adversarial audit loop', fontsize=10)
import os
os.makedirs('paper/figures', exist_ok=True)
fig.savefig('paper/figures/fig1_workflow.png', bbox_inches='tight', dpi=300)
fig.savefig('paper/figures/fig1_workflow.pdf', bbox_inches='tight')
print('fig1 saved')
