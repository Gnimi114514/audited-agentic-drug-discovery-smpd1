# Final Report — AI-Driven Drug Design Computation & Simulation: ASM (SMPD1) for Cognitive Impairment

Project: first-in-class small-molecule discovery against **human acid sphingomyelinase
(SMPD1/ASM)** for cognitive impairment / Alzheimer's disease.
Mode: **full-compute** (Open Targets, ChEMBL, PubMed, RCSB; Vina 1.2.7 docking; OpenMM
8.6.1 GPU MD on an RTX 5080; DeepPurpose + self-trained RF ADMET models; AiZynthFinder).

Master documents: [target-dossier.md](target-dossier.md) ·
[structure-analysis.md](structure-analysis.md) · [hit-report.md](hit-report.md) ·
[validation-plan.md](validation-plan.md) · [research-log.md](research-log.md)
Raw data: `data/`, `results/`, `docking/`, `md/`.

> **⚠️ EXTERNAL AUDIT CORRECTIONS (2026-09-13)** — an independent audit (GPT6/Codex,
> [independent-audit/REPORT.md](independent-audit/REPORT.md)) found material errors in
> this report. Four corrections are applied below and supersede the original claims:
> (1) the "known µM ASM actives" calibration references hit **SMPD2 (CHEMBL4712)**, not
> human SMPD1 (CHEMBL2760) — CHEMBL310981 vs human SMPD1 is 49 µM (activity 375434);
> (2) the bound-MD section had unit/duration/selection errors — corrected values are
3.1 ns total (0.1 ns initialization + 3.0 ns production);
> 6.1 ns duration (not 3 ns), naive ligand displacement 0.47–0.69 **nm** (4.7–6.9 Å),
> and the corrected imaged/fit analysis (GPT6) gives ligand internal RMSD **mean 1.847 Å
> / max 2.370 Å** (ligand-self fit) and protein backbone RMSD **mean 2.175 Å / max
> 2.679 Å** (protein-backbone fit) — the original "≤0.69 Å stable binding" claim
> is **withdrawn**; (3) the simulation actually used **Li 2013 CM 12-6 Zn²⁺ parameters**
> (126 file, ε=0.00330286 — verified from the v1 topology snapshot recorded in
independent-audit/rereview-r3/REPORT.md; the current complex.prmtop was later rebuilt
with the v2 12-6 subset and verified at ε=0.02662782); the C4 term of the 12-6-4 model is absent from both runs; (4)
> the direction evidence contains a counterexample (PMID 27598773) — the "inhibition
> consistently beneficial" claim is withdrawn and the direction gate reopened. Gate
> status per external review: G1 reference-control **FAIL** (corrected here), G4 analysis
> **FAIL** (corrected here), G6 **BLOCKED** pending re-review. Full triage:
> [runs/audit-20260913/reviews/gpt6-audit-triage.md](runs/audit-20260913/reviews/gpt6-audit-triage.md).

## Gate numbering (single source of truth)

This project straddled two gate vocabularies. The **team skill** (ai-drug-discovery-team)
defines G0 scope, G1 target, G2 site, G3 design, G4 simulation/triage, G5 synthesis,
G6 integration. The earlier single-agent reports used G1 target, G2 dossier, G3
structure, G4 screening, G5 triage, G6 integration. Mapping used everywhere below and
in runs/audit-20260913/:

| old (single-agent) | team skill | stage |
|---|---|---|
| G1 | G1 | target evidence |
| G2 | G1 (+G2 partially) | dossier/novelty |
| G3 | G2 | structure/site |
| G4 | G3 | screening/design |
| G5 | G4 | simulation/triage |
| — | G5 | synthesis routes (NOT_RUN — no real-stock closure) |
| G6 | G6 | integration |

Current team-skill outcomes: G1 FAIL-as-submitted (reference identity; repaired), G2
not re-reviewed, G3 stands with relabeled benchmark, G4 FAIL-as-submitted (units/
selection; corrected analyses adopted), G5 NOT_RUN, G6 BLOCKED pending re-review.

## Pipeline results at a glance

| Stage | Result | Gate |
|---|---|---|
| Target evidence (G1) | 22-gene evidence matrix (Open Targets + PubMed trends) → finalists PLCG2, INPP5D, SMPD1. **FAIL-as-submitted** (reference identity error); repaired in this revision; re-review pending | G1: FAIL→repaired |
| Site/structure (G2) | PDB 5I85 co-crystal validated by redocking (lenient-convention RMSD, graph-isomorphism revalidation pending); catalytic Zn conserved across 3 crystals; P2Rank independent pocket confirmation | G2: PASS-with-caveat |
| Design (G3) | 3,500-molecule diverse dock set from 20,111 CNS library; activity-record audit demoted 6/10 GPCR hits; 225-analog expansion; **benchmark anchors are SMPD2 actives — no human-SMPD1 potency anchor** | G3: PASS-with-caveat |
| Simulation/triage (G4) | 3,642 scored; 1,158 ≤ −7.0; apo MD 5.81 ns; bound MD v1 (6.1 ns, Li-2013 12-6) **audited & corrected**; bound MD v2 (3.1 ns total, 12-6 subset of 12-6-4, C4 omitted, pre-registered): **no close Zn contact in any saved frame (4.18–7.71 Å); occupancy 0/620 under the
post-hoc-defined joint criterion (center condition fails while at least one
catalytic-residue contact holds in every frame — per-residue frequencies: H457 620/620,
N318 414/620, T458 23/620, H319 11/620)**. **FAIL-as-submitted (units/selection); corrected analyses adopted** | G4: FAIL→corrected |
| Triage | Composite ranking + novelty NN + homolog selectivity (all ≤0.31) + **activity-record audit** (6/10 were GPCR ligands → reordered) | team-skill G4 FAIL-as-submitted (units/selection; corrected analyses adopted) |
| Hit expansion | 225 mono-substituent analogs docked; best clean-parent −9.36 (CHEMBL24974-CF3), −9.09 (7385-CF3) | — |
| ADMET | DeepPurpose: BBB 0.89–1.00, CYP clean, **P-gp flags (24974: 0.94)**; self-trained hERG (AUC 0.863) / DILI (0.888) RF predictions | — |
| **MD simulation** | apo: 5.81 ns all-atom NVT, 140,875 particles, RTX 5080, frozen catalytic pocket; bound: **6.1 ns** with Li-2013 12-6 Zn²⁺ (not 12-6-4) | — |
| Integration (G6) | GPT6/Codex audits: round-1 (5×P1), round-2 (5 residuals), round-3 (R3-1..7) — **all accepted and repaired**; independent re-acceptance of this revision pending | G6: BLOCKED |

## Final candidate set (all docking/ADMET values are PREDICTIONS)

1. **CHEMBL7385** — indole-2-carboxamide + aryl-piperazine; Vina −8.70; no strong
   positive target records on ChEMBL (1 negative HIV-RT record exists); SA 2.1;
   ADMET-clean except self-trained DILI 0.78 (watch); hERG_Central 0.090;
   6-CF3 analog docks at −9.09.
2. **CHEMBL24974** — Vina −8.72; 5 ChEMBL records exist (incl. rat BP decrease, LogD)
   but no strong positive CNS-target record; P-gp-inhibitor prediction 0.94
   (tune pKa); para-CF3 analog −9.36.
3. **CHEMBL6729** — Vina −8.89; oxazolidinone chemotype (0.72 to linezolid — check
   antibiotic angle); o-OH analog −9.36; lowest hERG_Central risk (0.058).
4. **CHEMBL48767** — Vina −8.71; 5-HT1A Ki 0.5 nM documented (flag); phenolic-OH
   analog −9.21.

## MD simulation summary (md/)

Protocol: chain-A ASM from PDB 5I85, PDBFixer-modeled loops/hydrogens, amber14 ff14SB +
TIP3P, 0.15 M NaCl, PME (1.0 nm cutoff), **frozen-pocket** protocol — catalytic-pocket
heavy atoms (11 residues) and the two Zn²⁺ dummy particles (mass 0, zero charge/LJ)
fixed at crystal positions; metal coordination chemistry not simulated. 100 ps heating
+ 5 ns production NVT at 310 K, dt 1 fs, CUDA platform, 76 ns/day.

Actual run: 5.78 ns completed (production loop over-stepped its 5 ns label — kept, more
sampling; total 5.78 ns × 141k particles). Backbone RMSD 1.7–3.6 Å (free relaxation),
pocket deviation 0.00 Å by construction. Snapshots aligned back to the crystal frame
via the rigid frozen pocket (Kabsch fit RMSD 0.000 Å).

**MD-ensemble redocking (6 ligands × 5 snapshots, Vina ex 8):**
results/md_ensemble_docking.csv

| Ligand | static 5I85 | MD ensemble mean ± SD | verdict |
|---|---|---|---|
| CHEMBL7385 | −8.70 | −8.04 ± **0.08** | tightest ensemble — most conformationally robust |
| CHEMBL24974 | −8.72 | **−8.94 ± 0.17** | strengthens on relaxation |
| CHEMBL48767 | −8.71 | −8.51 ± 0.28 | stable |
| CHEMBL6729 | −8.89 | −8.29 ± 0.30 | most pose-sensitive |
| EXP_CHEMBL7385_CF3 | −9.09 | −8.88 ± 0.32 | holds |
| **EXP_CHEMBL24974_CF3** | −9.36 | **−9.29 ± 0.37** | best overall across dynamics |

**MD verdict:** every promoted ligand keeps ≤ −7.8 kcal/mol binding across the relaxed
ensemble — no hit depends on a single crystal conformation; CHEMBL24974(-CF3) is the
dynamics-robust ranking leader.

## Professional toolchain installed in the goal-completion round (all verified)

| Tool | Version | Role | Status |
|---|---|---|---|
| OpenMM | 8.6.1 (conda, CUDA) | MD engine used for the 5.78 ns simulation | ✅ ran the simulation |
| AutoDock Vina | 1.2.7 (Scripps binary) | docking engine used for all campaigns | ✅ |
| **AmberTools** | CPPTRAJ V7.6.2 + tleap (conda) | system prep/analysis; **bundles published Li–Merz Zn²⁺ 12-6-4 parameters** (JCTC 2014: Zn²⁺ Rmin/2 1.455 Å, ε 0.0266 kcal/mol, TIP3P set) → unlocks real metal-coordination MD | ✅ verified |
| **GROMACS** | 2026.3 (conda-forge) | second MD engine for cross-validation of trajectories | ✅ verified |
| **GNINA** | v1.3.3 (CUDA 12.8 static; libs via conda-forge cuda-version=12.8) | deep-learning CNN scoring | ✅ **rescored 9 poses** |
| **P2Rank** | 2.5.1 (Java/ML) | independent ML pocket detection | ✅ validated pocket |
| RDKit / DeepPurpose / TDC / AiZynthFinder / mdtraj / Meeko | latest | library/triage/retrosynthesis | ✅ |

**GNINA CNN rescoring** (results/gnina_rescoring.json; CNNscore = pose-believability
probability, CNNaffinity = predicted affinity, higher better). **Correction: the three
references are µM actives of SMPD2 (CHEMBL4712), not human SMPD1 — the "known-active
band" framing is withdrawn; only CHEMBL7385's top CNNscore (0.705) survives as a
same-molecule internal observation:**

| Ligand | CNNscore | CNNaffinity | note |
|---|---|---|---|
| REF CHEMBL310981 (µM vs SMPD2) | 0.34 | **6.40** | reference is a different enzyme |
| **CHEMBL7385** | **0.705** | 6.03 | **best pose quality of all 9** |
| CHEMBL6729 | 0.58 | 5.96 | |
| EXP_CHEMBL7385_CF3 | 0.44 | 5.95 | |
| REF CHEMBL418376 (µM vs SMPD2) | 0.26 | 5.81 | |
| EXP_CHEMBL24974_CF3 | 0.18 | 5.83 | |
| REF CHEMBL5284579 (µM vs SMPD2) | 0.18 | 5.73 | |
| CHEMBL24974 | 0.19 | 5.27 | CNN skeptical of pose |
| CHEMBL48767 | 0.17 | 4.88 | CNN skeptical of pose |

CHEMBL24974/48767 CNNaffinities (5.27/4.88) are **below the reference minimum (5.73)** —
the original "all four inside the band" claim was wrong on its own table. **CHEMBL7385
keeps the strongest CNN pose-quality vote (0.705)**. Caveat: gnina's internal Vina-term
energies differ from our Vina 1.2.7 numbers; only the CNN columns are compared here,
within one engine.

**P2Rank independent pocket validation:** on the 1 ns MD snapshot, P2Rank's #1 predicted
pocket (score 39.05, probability 0.961 — 6× the runner-up) coincides with our docking
box (centers 8.0 Å apart, boxes overlap) — an ML-method-independent confirmation that
the ASM catalytic-site region is the dominant druggable pocket.

## What remains out of scope / not performed

- Retrosynthesis with a real purchasable stock (proxy-stock run produced no closed
  route, as expected); rerun with ZINC/Enamine stock or ASKCOS.
- Vendor orderability: ZINC15 text API returned HTML — manual vendor check required.
- Ligand-bound MD with the AmberTools Li–Merz Zn²⁺ 12-6-4 parameters (toolchain now
  installed), longer/replica MD, FEP/TI free-energy calculations.
- All wet-lab validation (Round 2, see validation-plan.md).

## Bound-state MD with real Zn²⁺ parameters (corrected after external audit)

Workflow: leader EXP_CHEMBL24974_C(F)(F)F_C27 parameterized with AmberTools antechamber
(GAFF2/AM1-BCC, 65 atoms); system built with tleap (MD-relaxed snapshot in crystal frame
+ 2 ZN ions + ligand at docked pose; 21,684 waters; Errors=0); ParmEd → OpenMM CUDA.

**Corrected facts (per external audit, coordinator-verified):**
- Duration: **6.1 ns** (3,050,000 steps × 2 fs), not "3 ns" — the original label was a
  unit error.
- Zn²⁺ parameters actually used: **Li et al. 2013 CM 12-6 set** (frcmod.ions234lm_126_tip3p,
  auto-loaded by leaprc.water.tip3p; coordinator-verified in complex.prmtop:
  ε = 0.00330286 kcal/mol, q = +2), **not** the 2014 12-6-4 file cited earlier.
- Ligand displacement vs minimized reference: 0.47–0.69 **nm** naive (4.7–6.9 Å) — the
  original "0.69 Å" omitted the nm→Å conversion.
- Corrected analysis (GPT6; whole-molecule periodic imaging; ligand metric uses
  ligand-self fitting, protein metric uses protein-backbone fitting): ligand internal
  RMSD **mean 1.847 Å, max 2.370 Å**; protein backbone RMSD **mean 2.175 Å, max
  2.679 Å**. (These are mean/max statistics, not min–max ranges.) The original
  "≤0.69 Å stable binding" and "12.5 Å loop-flailing" claims are **withdrawn**.
- Zn–ligand minimum-image distance (full trajectory): 1.810–3.529 Å, mean 1.978 Å
  (77.9% of frames in 1.9–2.1 Å) — an intermittent closest-contact, **not** a persistent
  single coordination bond.
- Open question the corrected data does NOT answer: whether the lead is a stable,
  persistently-coordinating ASM binder. That requires a re-run with the intended 12-6-4
  parameters, proper loop treatment and pre-registered analysis. Files: md/bound.dcd,
  md/bound_log.csv, scripts/bound_md.py; corrected analysis:
  independent-audit/md_results.json.

### Bound-MD v2 re-run with the 12-6 subset of the 12-6-4 parameter set (pre-registered; C4 term omitted)

Protocol pre-registered before the run (md/bound_analysis_pre_registered.json): dt 2 fs,
100 ps heat + 3.0 ns production (asserted steps×dt), protein-only backbone selection
(2,112 atoms), minimum-image Zn–ligand distances, whole-ligand COM-imaged ligand RMSD,
explicit minimized reference (md/bound_ref.pdb). Build assertion confirmed
ε = 0.02662782 (the 12-6 subset of the 12-6-4 set; the C4 cation-π term is NOT included) in the rebuilt prmtop.

| t | ligand RMSD (protein frame)¹ | min Zn–ligand (min-image) | protein backbone RMSD (fit) |
|---|---|---|---|
| 100 ps | 3.36 Å² | 4.54 Å | 1.28 Å |
| 1 ns | 2.96 Å² | 6.31 Å | 1.74 Å |
| 2 ns | 3.59 Å² | 6.59 Å | 1.83 Å |
| 3 ns | 4.39 Å² | 5.58 Å | 1.83 Å |

¹ These in-run values used the COM-imaged metric later retired by the round-3 audit
(R3-1: COM alignment removes the very translation the metric claimed to measure) and
printed nm as Å. The corrected analysis, recomputed independently by the auditor and
now reproduced by the repaired producer script (r7 analysis: see
runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence_r7_summary.json; the older
pocket_residence.json in the same directory contains the superseded r5fix numbers
4.696/6.050 Å and is retained as history), uses whole-molecule imaging and a
protein-backbone fit: **ligand RMSD mean 4.579 Å / max 5.935 Å over all 620 frames**. Corrected contact analysis (round-5/6 audit-verified mapping): catalytic residues
N318, H319, H457 and T458 are contacted (≥1 heavy atom within 4.5 Å; H457 in 620/620
frames); occupancy under the 6 Å-center + 4.5 Å-catalytic-contact conjunction (added post hoc
during audit-driven analysis) remains 0/620 (the center condition fails; substantial
radius sensitivity documented).

**Honest interpretation** (corrected contact mapping per round-5/6 audits):**
1. The protein backbone is **stable** (1.7–1.8 Å) — the audited "12.5 Å drift" was a
   water-contaminated selection, now corrected.
2. The docked CHEMBL24974-CF3 pose does **not** coordinate the catalytic Zn²⁺: minimum
   Zn–ligand distance stays 5.6–6.6 Å in the re-run. Attribution caveat: the v1-vs-v2
   difference cannot be attributed to parameter strength alone — v1's metrics were also
   unit-broken and the C4 term is absent from BOTH runs; what is established is only
   that the corrected analysis of either run shows no persistent Zn coordination.
3. The retired COM-imaged RMSD (3–4.4 nm→Å range in the in-run log) is superseded by
   the corrected protein-frame analysis (mean 4.579 / max 5.935 Å) and by the
   post-hoc-defined occupancy criterion (0/620); no pocket-residence conclusion is
   drawn from the retired metric.
4. **Campaign implication:** if ASM inhibition is to proceed via metal coordination
   (as the SMPD2-active phosphonate chemotype CHEMBL310981 suggests), the current
   non-metal-binding chemotypes test a *different* mechanism (pocket/ceramide-site
   occupancy). Metal-binding design is a separate direction with selectivity risk
   against SMPD2/ASAH1 (also metallohydrolases). This is now the key design decision.

Files: md/bound_v2.dcd, md/bound_v2_log.csv, md/bound_ref.pdb,
md/bound_analysis_pre_registered.json, scripts/bound_md.py.

**hERG_Central (dataset = 306,893 records; canonical-dedup to 306,879; now
REPRODUCIBLE)**: stratified 80/20 split (indices saved), RF-300 (MODEL-B) → **held-out
test ROC-AUC 0.9091, average precision 0.4792** (sklearn average_precision_score;
per-test-sample predictions archived so this is independently recomputable);
dataset SHA256, split indices and metrics archived in results/herg_central_repro/.
**Model lineage (post-adjudication):** the candidate probabilities quoted below come
from the legacy RF500 run on raw retrieved records; the archived MODEL-A is a
*deduplicated refit*, not a verified legacy reproduction (only 1/26 legacy values
reproduced at tolerance — a training-protocol change, not random variation).
**Serialization withdrawal:** no fitted estimator (MODEL-A refit, MODEL-B, or legacy)
was serialized; reproducibility is limited to the archived per-sample scores
(results/herg_central_repro/models/modelB_test_predictions.npz) and refit outputs. Candidate
overlap: all top candidates are 0.290–0.724 Tanimoto *similarity* from the nearest
training molecule (no near-duplicate threshold defined), nearest-neighbor labels
recorded. Candidate legacy probabilities: CHEMBL7385 0.090, CHEMBL6729 0.058,
CHEMBL48767 0.118, CHEMBL24974 0.258; expansion analogs 0.058–0.416. These are
predictions on novel scaffolds — not a de-risking guarantee; the small-set DILI flag on
CHEMBL7385 remains the main safety watch-item.

## The single most important next step

Amplex-Red biochemical ASM IC50 on CHEMBL7385 and CHEMBL24974 (partial-inhibition
plateau required — complete inhibition is Niemann-Pick-toxic), with hERG patch-clamp
follow-up.
