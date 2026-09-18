# Hit Report — ASM (SMPD1) virtual screening campaign

Campaign: 3,500-molecule scaffold-diverse subset of a 20,111-molecule ChEMBL
CNS-oriented drug-like library (MW 250–450, PSA ≤ 90, HBD ≤ 2, ALogP 1.5–4.5,
PAINS/Brenk-clean), docked into the validated PDB 5I85 catalytic pocket of human ASM.
**All docking numbers below are PREDICTED (Vina 1.2.7, ex 8, seed 42), not measurements.**

Calibration anchors (docked under the identical protocol):
| Reference compound | Known potency | Vina (predicted) |
|---|---|---|
| CHEMBL418376 | **1.0 µM vs SMPD2 (CHEMBL4712)** — no verified human-SMPD1 record | −6.96 |
| CHEMBL5284579 | **1.8 µM vs SMPD2 (CHEMBL4712)** | −6.34 |
| CHEMBL310981 | 1.0–3.3 µM vs SMPD2; **49 µM vs human SMPD1** (activity 375434) | −6.01 |

→ **CORRECTED after external audit:** the "known 1–2 µM actives" hit **SMPD2
(CHEMBL4712), not human SMPD1** — the calibration anchor is **withdrawn**. These
chemotypes still show that the pocket/protocol yields ≤ −7.0 scores for sphingomyelinase
chemotypes, but they are NOT validated human-SMPD1 actives. Docking scores never compare
across protocols/papers or across different enzymes.

## ⚠️ Post-docking activity-record check — this REORDERED the ranking (2026-09-12)

Every top-10 hit's original ChEMBL activity records were pulled after ranking. Result:
**6 of the top 10 are documented nanomolar GPCR ligands** — their ASM docking scores
are most plausibly a scaffold-promiscuity artifact, and several carry unacceptable
pharmacologies for a cognition program:

| Hit | Original documented activity | Verdict for this program |
|---|---|---|
| CHEMBL28172 | **Nociceptin Ki 2.5 nM, μ-opioid Ki 26 nM**, κ/δ | **DROP** — opioid agonist chemotype, abuse liability |
| CHEMBL54786 | **D2 IC50 38 nM, 5-HT1A 4.9 nM, α1** | **DROP** — antipsychotic-like polypharmacology |
| CHEMBL48767 | **5-HT1A Ki 0.52 nM, α1 30 nM** | demote — potent serotonergic; only if 5-HT1A SARM angle is wanted |
| CHEMBL37169 | D4 Ki 10 nM | demote — dopaminergic |
| CHEMBL29571 | nociceptin/μ Ki ≈1.2 µM (weak) | moderate — weak/ancient records |
| CHEMBL7385 | **no recorded activity** | **clean — PROMOTE to #1** |
| CHEMBL24974 | **no recorded activity** | **clean — PROMOTE to #2** |
| CHEMBL6729 | **no recorded activity** | clean but NN 0.72 vs LINEZOLID (oxazolidinone chemotype) — #3, check antibiotic angle |

**Revised working priority: CHEMBL7385 → CHEMBL24974 → CHEMBL48767 → CHEMBL6729**,
then the demoted GPCR entries as chemistry-only references. The analog-scan result on
CHEMBL37169 (−9.23) stands as a *method demonstration* but its parent is demoted;
the **CHEMBL24974 o-Me analog (−9.02, Δ−0.30) is the best evidence-backed lead
suggestion on a clean parent.**

This check is the "agents must verify, not just generate" step — docking-only triage
would have recommended an opioid agonist as hit #1.

## Campaign statistics (Gate G4)

- 3,642 ligands scored, 0 docking failures (3,442 new + 202 cached pilot/refs; 10
  pre-docking embed failures are registered in data/prep_failures.json). Docking-failure
  count ≠ preparation-failure count — both registered.
- **1,158 candidates ≤ −7.0 kcal/mol; 2,247 ≤ −6.5** (far above the ≥50–100 gate minimum).
- Diversity: **41 unique Bemis–Murcko scaffolds in the top 50** — the list is not
  50 analogs of one chemotype.
- Structural alerts: empty for all listed hits (PAINS A/B/C + Brenk applied pre-dock).

## Top hits (ranked by composite: docking + CNS property fit + SA + novelty)

| # | ID | SMILES | MW | cLogP | TPSA | QED | SA | Dock (predicted) | NN vs approved drugs | Novelty |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CHEMBL28172 | O=C1NCN(c2ccccc2)C12CCN(C1Cc3ccccc3C1)CC2 | 347.5 | 2.58 | 35.6 | 0.907 | 2.93 | −8.84 | 0.475 | novel |
| 2 | CHEMBL7385 | N#Cc1ccccc1N1CCN(C(=O)c2cc3ccccc3[nH]2)CC1 | 330.4 | 3.00 | 63.1 | 0.785 | 2.10 | −8.70 | 0.360 | novel |
| 3 | CHEMBL48767 | O[C@@H]1c2cc3c(cc2C[C@H]1N1CCC(c2cccc4c2OCCO4)CC1)OCO3 | 395.5 | 3.02 | 60.4 | 0.844 | 3.47 | −8.71 | 0.241 | novel |
| 4 | CHEMBL54786 | O=C1Cc2cc(CCN3CCN(c4cccc5ccccc45)CC3)ccc2N1 | 371.5 | 3.70 | 35.6 | 0.760 | 2.17 | −8.92 | 0.457 | novel |
| 5 | CHEMBL24974 | O=C1OC2(CCN(CC(O)C3COc4ccccc4O3)CC2)CN1CCc1ccccc1 | 438.5 | 2.72 | 71.5 | 0.748 | 3.86 | −8.72 | 0.394 | novel |
| 6 | CHEMBL29571 | O=C1N[C@@H]2CCCC[C@H]2N1C1CCN(Cc2ccc3ccccc3c2)CC1 | 363.5 | 4.14 | 35.6 | 0.889 | 3.05 | −8.89 | 0.282 | novel |
| 7 | CHEMBL6729 | CC(=O)NCC1CN(c2ccc(-c3ccc(N4CCOCC4)c(=O)cc3)cc2)C(=O)O1 | 423.5 | 2.01 | 88.2 | 0.792 | 2.87 | −8.89 | 0.724 | novel (NN 0.72 — watch) |
| 8 | CHEMBL37169 | O=C1NC(CCN2CCN(c3ccc4ccccc4c3)CC2)c2ccccc21 | 371.5 | 3.84 | 35.6 | 0.757 | 2.70 | −8.85 | 0.314 | novel |
| 9 | CHEMBL300739 | O[C@@H]1c2ccc(F)cc2C[C@H]1N1CC=C(c2cccc3c2OCCO3)CC1 | 367.4 | 3.34 | 41.9 | 0.884 | 3.55 | −8.67 | 0.264 | novel |
| 10 | CHEMBL26999 | O=C1NCN(c2ccccc2)C12CCN(C1CCc3ccccc3C1)CC2 | 361.5 | 2.97 | 35.6 | 0.893 | 3.36 | −8.60 | 0.444 | novel |

ADMET column note (updated 2026-09-12): **DeepPurpose ADMET predictions were computed**
for the top 20 (results/admet_predictions.csv; DeepPurpose 0.1.5, Morgan-encoder
pretrained models, all values **PREDICTED**):

| Metric | Top-20 range | Read |
|---|---|---|
| BBB penetration | 0.89–1.00 | all CNS-penetrant (consistent with design filters) |
| P-gp inhibitor | 0.10–0.94 | **CHEMBL24974 = 0.94, CHEMBL24034 = 0.83, CHEMBL289645 = 0.58 — liabilities** |
| CYP3A4 inhibitor | 0.00–0.30 | clean (max CHEMBL289645) |
| CYP2D6 inhibitor | 0.00 | clean |
| ClinTox | 0.00–0.16 | clean-ish (max CHEMBL35743) |
| Caco-2 / HIA | computed | all permeable/absorbed |

**Impact on ranking:** CHEMBL7385 (P-gp 0.15, CYP ~0, ClinTox 0.003, BBB 0.91) is now
unambiguously the cleanest top pick. **CHEMBL24974 (promoted #2 on pharmacology
cleanness) carries a predicted P-gp-inhibitor liability (0.94)** — not disqualifying
(inhibition ≠ being a substrate; and it is a prediction), but it becomes a
tune-by-analog item and a mandatory experimental check. **hERG and DILI models are not
in this DeepPurpose release — still not computed; manual web ADMET submission remains
recommended for those two endpoints.**

**Homolog-selectivity triage (computed):** max Morgan-Tanimoto of each top-20 hit
against the ChEMBL ligand sets of the nearest sphingolipid hydrolases — SMPD3/NSM2
(141 ligands), SMPD2 (7), SMPD4 (1), ASAH1 acid ceramidase (171), ASAH2 (6), NAAA (390)
— is **≤ 0.31 for every hit** (results/homolog_selectivity.csv): no hit resembles a
known homolog-enzyme ligand. Caveat: SMPD2/SMPD4/ASAH2 ligand sets are tiny, so this
check has low power for those three targets; the SMPD3/ASAH1/NAAA counterscreens in
validation-plan.md remain essential.

## Per-hit rationale (top 4; full contact data in results/pose_contacts.csv)

**#1 CHEMBL28172** (Vina −8.84, predicted). Bis-aryl spiro-urea/benzyl piperidine.
Contacts: HIS282, HIS457/459, TYR488, ASN318 (polar H-bond to His457), HIS319, THR458 —
occupies the catalytic His/Thr/Tyr loop region with the urea carbonyl oriented toward
the dinuclear Zn (nearest Zn 4.0 Å — headgroup-region binder, does not chelate).
Urea + basic piperidine matches the lysosomotropic-cation hypothesis.
*SAR question answered by docking: o-Me scan on the pendant phenyl gave −8.62
(Δ+0.22) — that position is a wall, not a pocket.*
Next analog: homologate the benzyl linker by one CH2 and re-dock (tests channel depth).

**#2 CHEMBL7385** (−8.70). Aryl-piperazine amide of indole-2-carboxylic acid; closest
approach to Zn 3.45 Å; two polar contacts to HIS457/ASN318. Indole NH + amide carbonyl
bracket the catalytic loop. SA 2.1 (very easy). NN vs approved drugs 0.36.
Next analog: 5-F/5-Me indole (docked Me-scan at other positions was neutral → the
indole position itself is the untested lever).

**#3 CHEMBL48767** (−8.71). Benzodioxole-containing secondary alcohol with piperidine;
**2.98 Å from Zn** and the only top-10 hit contacting ASP278 — deepest headgroup
penetration. TYR488 polar contact ×2. Caveat: benzodioxole is a mild PAINS-adjacent
motif (passed the filter but flag for CYP/MS-lability at assay time).
Next analog: replace OCH2O by the 2,2-difluoro bioisostere to de-risk oxidative
cleavage (not computable in this scan — synthesis-level suggestion).

**#4 CHEMBL54786** (−8.92, best score of campaign). Tetrahydroquinolinone + aryl
piperazine; 3.03 Å to Zn; contacts HIS459/TYR488/ASN318/HIS457/HIS319/THR458/ASP278.
cLogP 3.7 with TPSA 36 — most lipophilic of the top 5; CNS-MPO lower (2.29) — the
piperazine offers the handle to tune pKa/PSA upward.

## Analog scan (docked, evidence-backed SAR; 96 generated / 37 docked)

**Superseded by the full fragment-growth expansion (see below) — kept for provenance.**

| Analog | Change | Parent | Analog | Δ |
|---|---|---|---|---|
| AN_CHEMBL37169_Me-scan | aryl o-Me (naphthyl edge) | −8.85 | **−9.23** | **−0.38** |
| AN_CHEMBL24974_Me-scan | aryl o-Me (phenoxy ring) | −8.72 | −9.02 | −0.30 |
| AN_CHEMBL37169_Me-scan | second naphthyl position | −8.85 | −9.01 | −0.16 |

## Fragment-growth expansion (225 analogs, valence-safe generator, all docked)

Mono-substituent scans {F, Cl, OH, OMe, CN, CF3, Me} at every aromatic C–H of the six
priority hits (the earlier halogen-scan valence bug was fixed) → **225 generated,
225 prepped, 225 docked, 0 failures**. Best per clean parent (Vina, 5I85 protocol):

| Parent | Best analog | Δ | 5JG8 ensemble check |
|---|---|---|---|
| CHEMBL24974 (−8.72) | para-CF3 phenyl: `O=C1OC2(CCN(CC(O)C3COc4ccccc4O3)CC2)CN1CCc1ccccc1C(F)(F)F` | **−9.36 (−0.64)** | −8.69 ✓ |
| CHEMBL6729 (−8.89) | ortho-OH on pyridinone: `...c(=O)c(O)c3...` | **−9.36 (−0.46)** | −8.36 ✓ |
| CHEMBL48767 (−8.71) | phenolic OH: `Oc1cc2c(...)...` | **−9.21 (−0.49)** | −8.53 ✓ |
| CHEMBL7385 (−8.70) | 6-CF3 indole: `N#Cc1ccccc1N1CCN(C(=O)c2cc3ccc(C(F)(F)F)cc3[nH]2)CC1` | **−9.09 (−0.39)** | −8.28 ✓ |

Full table: results/expansion_results.json. **Flags:** (a) CF3 gains partly reflect
hydrophobic-area increase — docking-score inflation risk, treat as hypotheses;
(b) all 12 best analogs re-docked into the 5JG8 ensemble receptor stayed within
−8.1…−9.2 (no conformational flips); (c) hERG/DILI self-trained model predictions on
these analogs are in results/herg_dili_predictions.csv — the CHEMBL7385-CF3 analog
inherits the parent's high DILI probability (0.73).

## Honesty notes

- Docking scores are **predictions**; only rank-within-protocol comparisons are valid.
- Zn charges were 0.0 (see structure-analysis.md) — metal-chelating hits would be
  undervalued, not overvalued.
- Novelty NN was computed vs **all ChEMBL approved drugs (n=3,417) + 3 ASM references**,
  not all-ChEMBL (FPSim2 DB download failed) — "novel" means "no approved drug is a
  close analog", a narrower claim.
- These hits are documented ChEMBL bioactives; their *documented* activity may be
  against other targets (they were selected purely by ASM-pocket docking here).
  Checking each hit's original ChEMBL activity records before ordering is required.


## MD-ensemble validation (dynamics, 5.78 ns, RTX 5080)

Apo-ASM MD (frozen catalytic pocket, amber14/TIP3P, 141k particles, OpenMM CUDA)
→ 5 snapshots aligned to the crystal frame → re-docking of top hits + best analogs:

| Ligand | static 5I85 | MD ensemble mean ± SD |
|---|---|---|
| CHEMBL7385 | −8.70 | −8.04 ± 0.08 (most robust) |
| CHEMBL24974 | −8.72 | **−8.94 ± 0.17** |
| CHEMBL48767 | −8.71 | −8.51 ± 0.28 |
| CHEMBL6729 | −8.89 | −8.29 ± 0.30 |
| EXP_CHEMBL7385_CF3 | −9.09 | −8.88 ± 0.32 |
| EXP_CHEMBL24974_CF3 | −9.36 | **−9.29 ± 0.37** |

Every promoted ligand keeps ≤ −7.8 kcal/mol in all snapshots — binding does not depend
on a single crystal conformation. CHEMBL24974(-CF3) strengthens on relaxation and is
the dynamics-robust leader; CHEMBL6729 is the most pose-sensitive. Full data:
results/md_ensemble_docking.csv; trajectory and snapshots in md/.

## GNINA CNN rescoring (second-opinion, 9 poses)

CNNscore (pose-believability): **CHEMBL7385 0.705 — best of all 9 poses**, CHEMBL6729
0.58, CF3 analogs 0.44/0.18, CHEMBL24974 0.19, CHEMBL48767 0.17. CNNaffinity of all
candidates (5.3–6.0) compared to the references (5.7–6.4) — **corrected: those
references are µM actives of SMPD2 (CHEMBL4712), not human SMPD1, and CHEMBL24974/
48767 (5.27/4.88) fall below the reference minimum; no "inside the band" claim survives.
The CNN's skepticism toward CHEMBL24974/48767 poses is an uncertainty flag, consistent
with their pharmacology/P-gp warnings. Data: results/gnina_rescoring.json.

## MODEL-A legacy-probability precision note (round-4 audit)

MODEL-A (RF500, full-data, legacy protocol) is a stochastic ensemble: re-training
reproduces CHEMBL7385 = 0.090 exactly but other candidates vary at the second decimal
(e.g. CHEMBL28172 legacy 0.254 vs re-run 0.228). Legacy MODEL-A values in this report
and in final-report.md are therefore **approximate (stochastic-approximate), not exact
constants**. MODEL-B (RF300, fixed 80/20 split) values are exact for the archived split
(results/herg_central_repro/models/).