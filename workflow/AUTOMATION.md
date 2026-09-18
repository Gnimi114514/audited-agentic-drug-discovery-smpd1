# AUTOMATION.md — AI-agent full-pipeline automation

This directory contains a complete, re-runnable autonomous drug-discovery research
pipeline. Every phase is a script with logged inputs/outputs and a gate decision; the
agent (ZCode + ai-drug-discovery skill) drove all of it end-to-end without manual
intervention, self-correcting at each failure (see research-log.md for the audit trail).

## One-command reproduction

```bash
bash scripts/run_all.sh          # full pipeline, ~3-4 h on 24 cores + RTX 5080
```

## Pipeline map (agent loop: fetch → compute → verify → gate → iterate)

| # | Phase | Script | Output | Gate |
|---|---|---|---|---|
| 0 | Scope lock | (agent decision, logged) | research-log.md | G0 |
| 1 | Target evidence matrix | scripts/ot_fetch_assoc.py, ot_fetch_targets.py, ot_scores_trends.py, score_panel.py | data/ot_*.json, data/panel_scores.json | G1 |
| 2 | Dossier + novelty | scripts/chembl_check.py, pubmed_direction.py | data/chembl_*.json, data/pubmed_direction.json | G2 |
| 3 | Structure & pocket | scripts/prep_5i85.py, redock.py (+ ensemble_prep.py, ensemble_dock.py) | structures/, docking/redock_* | G3 |
| 4 | Library + screening | scripts/build_library_v2.py, diversity_prefilter.py, rdkit_prepare.py, dock_runner.py | docking/, data/dock_set.smi | G4 |
| 5 | Triage & ranking | scripts/triage.py, pose_contacts.py (+ herg_dili.py, admet_predict.py, homolog check) | results/hits_ranked.csv | G5 |
| 6 | Hit expansion | scripts/analog_scan.py, expansion.py | results/expansion_results.json | — |
| 7 | MD simulation | scripts/md_run.py (apo), md_extract.py, md_ensemble_dock.py; bound_md.py (ligand-bound, real Zn) | md/ | — |
| 8 | Rescoring/validation | scripts/gnina_rescore.py (CNN), p2rank_run.sh (pocket ML), herg_karim.py (big-data hERG) | results/ | — |
| 9 | Reports | final-report.md + 4 dossier docs (written by the agent at each gate) | *.md | — |

## Agent behaviors that made it autonomous

- **Fetch, don't recall**: every bioactivity/score/structure number came from a live API
  call (Open Targets GraphQL, ChEMBL REST, PubMed E-utilities, RCSB, Zenodo), logged with
  date; memory only proposed, databases confirmed.
- **Self-critique gates**: G1–G5 each have a written pass/kill decision with the strongest
  counter-argument included (e.g., SMPD1 has no human-genetics line; 6/10 top docking hits
  were known GPCR ligands and were demoted after the activity-record audit).
- **Verify-by-recomputation**: redocking RMSD < 2 Å before screening; cross-crystal
  replication; µM-active benchmark anchoring; P2Rank independent pocket detection;
  GNINA CNN second opinion; frame-consistency checks (the MD "5 ns was actually 5 ps"
  step-math bug was caught by frame counting).
- **Timeboxing**: GNINA deps / ZINC API / zenodo 504 stalls were capped at ~3 attempts,
  recorded as limitations, and worked around (conda-forge cuda-version=12.8 pin; proxy
  stock; manual vendor check).

## Environment (as built here)

- Windows host: Python 3.12, RDKit 2026.03, Vina 1.2.7 (Scripps binary), Meeko, DeepPurpose,
  PyTDC, scikit-learn; conda envs: `ob` (OpenBabel for receptor prep).
- WSL2 Ubuntu (CybergymUbuntu): miniforge envs — `md` (OpenMM 8.6.1 CUDA + pdbfixer +
  mdtraj + parmed), `amber` (AmberTools: tleap/antechamber/cpptraj + Li–Merz Zn²⁺ 12-6-4
  parameters), `gmx` (GROMACS 2026.3), `gnina12` (CUDA 12.8 runtime libs) + `/tmp/gnina`
  (GNINA 1.3.3 CUDA static), `p2r` (OpenJDK) + `/tmp/p2rank_2.5.1`.
- GPU: RTX 5080 Laptop 16 GB (76 ns/day for the 141k-atom apo system).
