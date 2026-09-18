# Validation Plan — SMPD1 (ASM) partial inhibitors for cognitive impairment

Scope: hits from the PDB-5I85 docking campaign (this project). Everything in Round 1 is
computational and reproducible from the scripts in `scripts/`; Round 2 onward requires a
wet lab and institutional oversight.

## Round 1 (computational — done / possible now) — STATUS AFTER "GO BIG" ROUND

**Done:**
1. Structure validated — now **three crystals**: redocking RMSD 1.76 Å (5I85 top pose),
   **cross-crystal 1.52 Å (5I81) / 1.77 Å (5JG8)**; catalytic-Zn geometry conserved
   (matched displacement 0.15–0.70 Å); top-20 re-docked in all three crystals with no
   rank flips among clean hits (results/ensemble_scores.csv).
2. Campaign triage unchanged (see hit-report.md).
3. Reference anchoring unchanged (−6.0…−7.0 for known µM actives).
4. Pose inspection unchanged (results/pose_contacts.csv).
5. **Fragment-growth expansion (done)**: 225 analogs, 0 failures; best clean-parent
   improvements −9.36 (CHEMBL24974-CF3), −9.21 (48767-OH), −9.36 (6729-OH),
   −9.09 (7385-CF3); 12 best verified in the 5JG8 ensemble (results/expansion_results.json).
6. **ADMET (done)**: DeepPurpose BBB/P-gp/CYP/Caco2/HIA/ClinTox on top-20
   (results/admet_predictions.csv).
7. **hERG & DILI (done)**: locally trained RF models (TDC data; CV AUC 0.863 / 0.888);
   predictions in results/herg_dili_predictions.csv — hERG risk broadly elevated across
   the basic-amine chemotypes; CHEMBL7385 carries a high DILI probability (0.78).
8. **Selectivity vs homolog hydrolases (done)**: all top-20 ≤ 0.31 Tanimoto to
   SMPD3/SMPD2/SMPD4/ASAH1/ASAH2/NAAA ligand sets (results/homolog_selectivity.csv).

**Attempted / deferred (with reasons, resumable):**
- **GNINA CNN rescoring**: binary downloaded (v1.3.3, cuda12.8 static, runs in WSL on
  the RTX 5080); dependency chain incomplete (cudnn ✓, cudart ✓, cublas/cufft/cusparse
  wheels downloading). Resumable: `wsl … LD_LIBRARY_PATH=… /tmp/gnina --score_only`.
- **Retrosynthesis (AiZynthFinder 4.4.1 + USPTO ONNX models)**: executed on
  CHEMBL7385 with a 20,111-molecule ChEMBL proxy stock — 175 routes explored, **no
  closed route** (expected: proxy stock ≪ true purchasable space). Config preserved
  (aizynth_config.yml). Rerun with ZINC-all / Enamine stock, or ASKCOS, for a real
  SA-feasibility read.
- **MD simulation (done 2026-09-12)**: 5.78 ns all-atom apo-ASM NVT (amber14/TIP3P,
  141k particles, RTX 5080, 76 ns/day, frozen-pocket protocol — see research-log D8).
  Snapshot-ensemble redocking of top hits + best analogs: all ≤ −7.8 kcal/mol in every
  snapshot (results/md_ensemble_docking.csv). Ligand-bound MD with explicit Zn²⁺
  12-6-4 parameters and longer trajectories remain the next upgrade.

## Round 2 (assays — needs lab)

| Assay | Purpose | Controls | Go/no-go criterion | Est. cost/time |
|---|---|---|---|---|
| Biochemical ASM IC50 (Amplex Red sphingomyelinase or fluorogenic substrate, recombinant human ASM) | primary potency vs target | Positive: published inhibitor (CHEMBL418376-class) or desipramine (functional inhibitor); Negative: DMSO; Zn-control: EDTA-only well | IC50 ≤ 5 µM with partial inhibition plateau (residual activity ≥ 30–40% at solubility limit) | ~$2–5k, 2–4 weeks |
| Counterscreen SMPD3/NSM2 + SMPDL3A | selectivity vs neutral SMases | same as above | ≥10-fold selectivity for ASM | ~$3k, 2–3 weeks (parallel to above) |
| Phospholipidosis counterscreen (NBD-PE accumulation in HepG2 or hiPSC macrophages) | flag lysosomotropic cation liability | amiodarone positive, DMSO negative | no PLD signal ≤ 30 µM | ~$2k, 2 weeks |
| Cell target engagement (ceramide/SMS quantification LC-MS in ASM-inhibited cells) | cellular mechanism | ASM siRNA as orthogonal suppression; desipramine comparator | dose-dependent SM accumulation matching biochemical potency | ~$5–8k, 4–6 weeks |
| Disease-relevant cellular model (hiPSC microglia/astrocyte co-culture; mitotoxic EV secretion readout per PMID 37605262) | phenotypic reversal | isogenic SMPD1 KD; desipramine | partial inhibition reverses EV-mitotoxicity phenotype without cytotoxicity | ~$15–25k, 2–3 months |
| hERG / CYP panel (CRO) | developability | terfenadine/diltiazem controls | IC50 > 10 µM hERG | ~$5k, 3 weeks |

**Biosafety & ethics:** no pathogen/toxin work; recombinant enzyme and human cell lines
only → standard BSL-2 cell-culture and institutional chemical safety are sufficient.
Any *in vivo* work requires IACUC-style approval and is out of scope of this plan.
Note for the "cognitive enhancement in healthy people" framing: any future human-use
conversation is a regulatory matter (enhancement is not a treatment indication); this
plan addresses disease-context (impairment) research only.

## Decision tree

- If biochemical IC50 ≤ 5 µM **and** partial-inhibition plateau confirmed →
  counterscreens → cell engagement → hit-expansion around scaffold (Round 3).
- If biochemical active but no cellular effect → check lysosomal accumulation (PLD
  counterscreen + LC-MS in cells); redesign for pKa/permeability (add basic center or
  reduce P-gp).
- If biochemical inactive despite good docking → suspect Zn-charge artifact or
  headgroup-only binding; re-examine poses, consider metal-parameterized re-docking
  (Zn charge +2 or cation–water correction) before discarding chemotype.
- If nothing survives Round 2 → fall back to runner-up target track: INPP5D
  direction-resolving experiment (SHIP1 activity vs NLRP3/complement phenotypes) and
  PLCG2 activator discovery via non-docking modalities (DEL/fragment against the
  autoinhibitory cSH2 interface).
