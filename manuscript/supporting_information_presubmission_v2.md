# Supporting Information

**Auditing an AI-Agent Computational Drug-Discovery Workflow Through an SMPD1 Case Study**

Yiming Zuo

School of Chemistry, Chemical Engineering and Life Sciences, Wuhan University of Technology, Wuhan 430070, China

## SI-1: Complete evidence matrix (22-gene panel)

Full weighted scoring table. Source: `data/panel_scores.json`, `data/ot_associations.json`, `data/pubmed_trends.json`, `scripts/score_panel.py`.

Weights: genetics/omics 0.30, mechanism 0.20, novelty 0.20, safety 0.20, druggability 0.10.

Columns: gene, total score, genetics, mechanism, novelty, safety, druggability, approved drugs, clinical candidates, notes.

## SI-2: Screening funnel and full ranked output

- Library: `data/chembl_library.jsonl` (20,111 ChEMBL entries, CNS filters)
- Filtered: `data/library_filtered.csv` (11,758 passing PAINS/Brenk/charge)
- Dock set: `data/dock_set.smi` (3,500 scaffold-capped)
- Full ranking: `results/hits_ranked.csv` (3,642 rows: ligand, Vina score, properties, novelty)
- Funnel registry: `results/funnel_registry.json`
- Preparation failures: `data/prep_failures.json` (10 embed-failures)

## SI-3: Analog expansion results

225 analogs (F/Cl/OH/OMe/CN/CF₃/Me at aromatic C–H positions of 6 priority hits), all prepped, docked, 0 failures.
`results/expansion_results.json`

## SI-4: ADMET and hERG/DILI predictions

- DeepPurpose ADMET (BBB, P-gp, CYP3A4/2D6, Caco-2, HIA, ClinTox) for top 20: `results/admet_predictions.csv`
- Self-trained RF500 hERG (655-mol set) + RF500 DILI (475-mol set): `results/herg_dili_predictions.csv`
- hERG_Central RF300 reproducibility package: `results/herg_central_repro/` (dataset SHA256, split indices, metrics, candidate overlap)

## SI-5: MD trajectories and analyses

- Apo frozen-pocket MD: `md/prod.dcd` (1,161 frames in the audited trajectory inventory), `md/solvated.pdb`, `md/log.csv`
- Bound v1 (Li-2013 12-6 Zn): `md/bound.dcd`, `md/bound_log.csv` — **superseded by v2**
- Bound v2 (12-6 subset of 12-6-4): `md/bound_v2.dcd`, `md/bound_v2_log.csv`, `md/bound_ref.pdb`, `md/bound_analysis_pre_registered.json`
- Pocket-residence analysis: `runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence.json`
- Snapshots: `md/snapshot_{1..5}ns_al.pdb` (crystal-aligned)
- MD ensemble docking: `results/md_ensemble_docking.csv`

## SI-6: Audit trail

- Round-1 audit: `independent-audit/REPORT.md` + 5 verification JSONs
- Round-3 re-review: `independent-audit/rereview-r3/REPORT.md` + checks
- Round-4 adjudication: `independent-audit/round4-acceptance/adjudication.md`
- Round-11 acceptance: `independent-audit/round11-acceptance/round11-acceptance.md`
- Final acceptance: `independent-audit/final-acceptance/final-acceptance.md` + `final_checks.json`
- Verdict-authority resolution: `independent-audit/round4-acceptance/verdict-authority-status.json` (superseded by adjudication)

## SI-7: Seeded-error benchmark

- 18 seeded cases across 9 error classes, plus the recorded controls
- Expected outcomes frozen in `scripts/benchmark_full.py` before that development run; the cases and checks were designed within the same project and were not independently preregistered or held out
- Results: `runs/benchmark-full/benchmark_full_results.json`
- Real-findings replay (13 executed): `runs/benchmark-seeded/real_findings_replay_executed.json`
- Miss analysis: C4-b (numeric-only check cannot catch citation mismatch), C6-a (atom-name filter cannot catch residue-name contamination), C8-c (naive numbering cannot catch mapping errors). C9-b exposed a control-label/semantics defect; no zero-false-positive claim is made.

## SI-8: Frozen integrity manifest

`audit_manifest.json`: 5-level leaf-to-root SHA256 manifest (L1 evidence, L2 scripts, L3 reports, L4 nested handoffs, L5 audit artifacts). No self-reference. 77 entries. research-log.md frozen at D23 state.

## SI-9: GNINA CNN rescoring

9 poses (6 candidates + 3 references). CNNscore and CNNaffinity table. Source: `results/gnina_rescoring.json`.

## SI-10: P2Rank pocket prediction

Top pocket: score 39.05, probability 0.961 (6× runner-up), centers overlap with docking box. Source: `results/p2rank_out/`.

## SI-11: Model separation

MODEL-A (RF500 full-data legacy) vs MODEL-B (RF300 held-out split) — candidate probabilities side-by-side. Source: `results/herg_central_repro/models/candidate_predictions_by_model.csv`, `results/herg_central_repro/models/model_provenance.json`.

## SI-12: Homolog selectivity

Max Tanimoto vs SMPD3/SMPD2/SMPD4/ASAH1/ASAH2/NAAA ligand sets ≤ 0.31 for all top-20. Source: `results/homolog_selectivity.csv`.

---

**All SI items are included in the project directory and are individually hash-tracked via audit_manifest.json.**
