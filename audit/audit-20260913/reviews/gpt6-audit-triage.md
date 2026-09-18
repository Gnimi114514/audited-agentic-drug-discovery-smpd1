# Coordinator triage — external audit (GPT6/Codex, independent-audit/REPORT.md)

Date: 2026-09-13. Coordinator: ZCode session (producer of the audited work). Reviewer: independent external agent (GPT6). Mode: audit-repair.

## Triage of the 11 findings

| # | Finding (severity) | Coordinator verdict | Basis |
|---|---|---|---|
| 1 | [P1] Reference µM activities belong to SMPD2 (CHEMBL4712), not human SMPD1 (CHEMBL2760); CHEMBL310981 vs human SMPD1 = 49 µM | **ACCEPT** | Live re-verification: CHEMBL4712 pref_name = "Sphingomyelin phosphodiesterase 2"; activity 375434 = CHEMBL2760, IC50 49,000 nM. My own earlier homolog-resolution output had already listed CHEMBL4712 as SMPD2 — the mislabel ('SMPD1_human_B') happened in chembl_finalists_extra.json interpretation. Calibration anchor WITHDRAWN. |
| 2 | [P1] Bound-MD units/duration/backbone-selection errors (0.69 is nm→6.9 Å; 6.1 ns not 3 ns; backbone included 21,684 water O) | **ACCEPT** | bound_md.py:48-49 confirmed (nm not converted, mislabeled Å); log last step 3,050,000 × 2 fs = 6.1 ns; selection bug confirmed by reading the script. GPT6's recomputed metrics (whole-molecule imaging + protein-backbone fit: ligand internal RMSD 1.847/2.370 Å; protein bbRMSD 2.175/2.679 Å) accepted as the corrected analysis. "≤0.69 Å stable binding" claim WITHDRAWN. |
| 3 | [P1] Actual Zn params = Li 2013 CM 12-6 (126 file), not 2014 12-6-4 | **ACCEPT** | Coordinator re-verification via ParmEd on complex.prmtop: eps = 0.00330286 kcal/mol — exact match to the 126 set; 1264 would be 0.02662782. Root cause: leaprc.water.tip3p auto-loads the 126 file; my 1264 loadamberparams came later in the script order? No — never loaded (tleap_bound.in only sourced water.tip3p). "File exists" ≠ "file used". |
| 4 | [P1] Direction evidence contains counterexample (PMID 27598773) | **ACCEPT** | Abstract (fetched by auditor) shows ASM overexpression without measured memory deficit and amitriptyline impairment in female WT with overexpression protection — a genuine direction contradiction. Direction gate REOPENED; "inhibition consistently beneficial" withdrawn. |
| 5 | [P1] hERG_Central n≈12k unreproducible; actual 306,893 | **ACCEPT** | TDC returns 306,893 rows for hERG_Central/hERG_inhib; my "n≈12k" was recalled, not measured. Training was on the full set (script has no sampling); AUC 0.904 unverified as described. Description corrected; AUC marked unverified-pending-rerun. |
| 6 | [P2] Manifest hash 39/40 (research-log.md grew post-hash) | **ACCEPT** | D12 append happened after hashing — design flaw of the manifest protocol. Regenerated manifest supersedes the old one. |
| 7 | [P2] "Zn contact 1.9–2.1 Å throughout" overstated | **ACCEPT** | Full-trajectory min-image: 1.810–3.529 Å, mean 1.978, 77.87% in 1.9–2.1. "Throughout" withdrawn; min-atom-pair does not track a single coordination bond. |
| 8 | [P2] First row of screening table is composite-best (−8.84), not best Vina (−8.92 CHEMBL54786); dock_set 3,500; 152-name batch merge; prep_failures 10 | **ACCEPT** | All verifiable from files. Wording corrected; batch merge registered. |
| 9 | [P2] "no prior activity records" inaccurate (CHEMBL7385: 1 negative HIV RT record; CHEMBL24974: 5 records); audit command used CHEMBL28132 instead of 28172 | **ACCEPT** | Wording corrected to "no strong positive target records"; command typo noted. |
| 10 | [P2] Redocking RMSD used element-swap matching (1.757 Å lenient; constrained 1.914; name-based 2.524) | **ACCEPT** | Symmetric-rotation-tolerant matching is defensible only as a stated convention; formal graph-isomorphism revalidation pending. 1.76 Å relabeled "lenient convention". |
| 11 | [P2] CNN "all four in reference band" contradicts own table; references are (now known) SMPD2 | **ACCEPT** | Doubly wrong: 2 of 4 below reference minimum, and the references are a different enzyme. Corrected. |

No finding REJECTED. The auditor also correctly preserved failed/operational evidence and did not accept its own 400-error as fatal (self-recovered).

## Gate outcomes after external review

- G1 (target evidence): **FAIL** as submitted (reference identity) — target evidence panel itself survives; direction REOPENED.
- G4 (simulation/triage analysis): **FAIL** as submitted (units, selection, parameter identity) — raw trajectories remain valid artifacts; corrected analyses are the GPT6 recomputations.
- G6 (integration): **BLOCKED** pending corrected reports (this repair) and re-review.
- G3 (design): stands with relabeled benchmark (ranking within the campaign remains internally meaningful; the external µM anchor is withdrawn).
- G2/G5 (OLD single-agent numbering: dossier / triage): not disputed by the audit beyond wording fixes applied here. NOTE the gate vocabulary: under the team-skill numbering these correspond to G1-target/G4-simulation respectively, and "not disputed" does NOT mean accepted — G4-simulation is FAIL-as-submitted per the audit's finding 2.

## Repairs applied (this revision)

1. final-report.md — audit-corrections banner; reference anchor relabeled (SMPD2); bound-MD section rewritten with GPT6 recomputed metrics + 6.1 ns duration + Li-2013 params; hERG_Central n corrected; direction counterexample added; CNN band claim corrected; novelty wording corrected.
2. hit-report.md — calibration table relabeled (SMPD2), thresholds withdrawn; funnel numbers (3,500; batch merge; prep failures); CNN section corrected; novelty wording corrected.
3. structure-analysis.md — redocking RMSD relabeled as element-swap-lenient with all three match conventions listed; revalidation pending.
4. target-dossier.md — direction counterexample added to evidence matrix; human SMPD1 49 µM record added.
5. research-log.md — D13 entry; manifest regenerated post-repair (supersedes pre-repair manifest).
6. runs/audit-20260913/gates.json — outcomes recorded per above.
