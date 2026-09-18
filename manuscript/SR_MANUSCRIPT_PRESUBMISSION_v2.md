# Auditing an AI-Agent Computational Drug-Discovery Workflow Through an SMPD1 Case Study

**Author:**

Yiming Zuo¹

¹ School of Chemistry, Chemical Engineering and Life Sciences, Wuhan University of Technology, Luoshi Road 122, Hongshan District, Wuhan 430070, Hubei Province, China.

* Corresponding author: Yiming Zuo (Gnimi114514@whut.edu.cn), ORCID: 0009-0001-3280-1027.

**AI disclosure:** Two AI systems (GLM/ZCode producer agent and GPT/Codex auditor agent) contributed as tools under human direction. They are not authors. All AI-generated content was verified by the corresponding author. The producer agent implemented the pipeline and executed computations; the auditor agent independently verified claims and identified defects; the human supervisor designed the study, approved all corrections, and takes full scientific accountability.

## Abstract

AI agents can chain drug-discovery tools into coherent research narratives while propagating errors that survive self-review. We report a computational case study targeting human acid sphingomyelinase (SMPD1) for cognitive impairment, built from open tools on consumer hardware and subjected to fresh-context adversarial audit. The producing agent executed target nomination, virtual screening, analog expansion, short molecular-dynamics simulations, predictive triage, and retrosynthesis. Audit changed central conclusions by identifying reference-target misattribution, unit errors, an executed-versus-cited force-field mismatch, and a literature counterexample to the proposed modulation direction. A development test detected 15 of 18 seeded cases, but its checks and cases were designed within the same project and therefore do not estimate general audit sensitivity. A three-arm feasibility pilot produced artifacts from single-agent, multi-agent, and audited multi-agent configurations without scoring scientific correctness. The surviving result is an inspectable failure-analysis case study and a reusable audit protocol, not a validated drug candidate or evidence that one agent configuration outperforms another.

**Keywords:** AI agents; computational drug discovery; scientific audit; reproducibility; molecular simulation; workflow evaluation

---

## Introduction

AI agents can chain biomedical databases, docking engines, simulation packages, and predictive models into research narratives that appear coherent and cite real data, while carrying identity, unit, provenance, and interpretation errors that survive self-review. The problem is evidence transfer: correct API responses and completed simulations can still support incorrect biological claims when target identity, physical units, reference frames, or model versions are silently lost between processing steps.

Adversarial audit - fresh-context review operating on raw artifacts with prospective or explicitly labeled post-hoc metrics - is one response. This paper reports a complete cycle: an agentic producer executed a target-to-candidate campaign; an auditor repeatedly re-derived claims from raw artifacts; an adjudication resolved a verdict-authority conflict; and later acceptance checks verified scoped repairs and withdrawals. The final G6 status remained CONDITIONAL because the computational handoff was auditable but key scientific gates and experimental validation remained incomplete (Figure 1).

SMPD1 (acid sphingomyelinase, UniProt P17405; EC 3.1.4.12) and cognitive impairment provide the case-study context [23]. SMPD1 catalyzes the hydrolysis of sphingomyelin to ceramide and phosphocholine in the lysosome and has been discussed in neurological disease contexts [14-16]. Biallelic loss-of-function causes Niemann-Pick disease type A/B; complete pharmacological inhibition is therefore contraindicated, and a partial-inhibition strategy is required. The nomination of SMPD1 as a target and the direction-of-modulation question are treated as separate decisions. The campaign's candidates are reported as computational hypotheses, not validated leads.

### Relationship to prior work

AI-agent systems for drug discovery and chemistry have combined tool use with role specialization, while scientific workflow research has established provenance and reproducibility as distinct requirements. Contemporary computational workflows draw on docking [3,5], pocket prediction [6], predictive modeling [7,8], retrosynthesis [9], and protein-structure prediction [22]. The present contribution is a documented integration of a target-to-candidate workflow with stable-ID findings, artifact-bound verification, mutation-tested checks, and preserved negative results. The work is positioned as a retrospective systems case study. It does not establish priority over all related systems, general audit sensitivity, or the effectiveness of multi-agent orchestration.

Scientific workflow verification has precedents in reproducibility research and provenance tracking (W3C PROV model), but application to agentic drug-discovery workflows is novel. Seeded-error evaluation has roots in software fault-injection testing; our adaptation uses chemistry-specific error classes derived from audit findings.

---

## Results

### Target nomination and reference-identity correction

A 22-gene evidence matrix was assembled from Open Targets GraphQL associations [1], PubMed literature trends informed by Alzheimer's disease genetics [13], ChEMBL target records [2,12], and per-target safety annotations. Weighted scoring (genetics/omics 0.30, mechanism 0.20, novelty 0.20, safety 0.20, druggability 0.10) shortlisted SMPD1 (0.590), PLCG2 (0.655), and HFE (0.660). SMPD1 was selected for the docking funnel based on structure availability in the Protein Data Bank [24] (PDB 5I85 with co-crystal phosphocholine), database evidence (the ChEMBL target CHEMBL2760 returned zero mechanism records on 2026-09-12; scoped to that endpoint), and a then-claimed beneficial direction of inhibition (Figure 2A).

The direction claim did not survive audit. The µM "ASM inhibitor" anchors bind SMPD2 (CHEMBL4712, "sphingomyelin phosphodiesterase 2"), not human SMPD1. CHEMBL310981 inhibits human SMPD1 with IC50 = 49,000 nM (activity 375434) — a single-molecule record that does not constitute a target-wide potency ranking. PMID 27598773 contains a direction counterexample: ASM overexpression without measured memory deficits, and amitriptyline impairing object memory in female wild-type mice with overexpression protection. The direction-of-modulation gate is reopened (Figure 2B).

### Structure, screening, and corrected score interpretation

The docking protocol was checked with AutoDock Vina [3] by redocking the co-crystal phosphocholine of PDB 5I85. Three matching conventions were evaluated: element-swap assignment (RMSD 1.76 Å), connectivity-constrained matching (1.91 Å), and name-based matching (2.52 Å). Formal bond-order/protonation-aware graph-isomorphism revalidation has not been performed; the redocking gate carries a caveat. Cross-crystal replication on 5I81 and 5JG8 gave 1.52 Å and 1.77 Å (Ca-RMSD 0.17/0.54 Å). P2Rank 2.5.1 [6] independently ranked the catalytic site as the dominant druggable pocket (score 39.05, probability 0.961, six times the runner-up) (Figure 3A).

The screening funnel processed 20,111 ChEMBL molecules through CNS-oriented filters (11,758 passing PAINS/Brenk and charge rules), a Bemis–Murcko scaffold cap (3,500 selected; 2,138 unique scaffolds), and docking (3,642 scored, including batch-merged pilot and reference entries; 10 preparation failures registered separately from zero docking failures). Of these, 1,158 scored ≤ −7.0 kcal/mol — an internal ranking convention, not a potency calibration (Figure 3B). The composite-ranked table demoted six of its top ten entries after an activity-record audit showed they were documented GPCR ligands (e.g., CHEMBL28172, nociceptin-receptor K_i = 2.5 nM).

### Simulations: corrected conclusions

The apo simulation (5.78 ns production after 100 ps heating; 140,875 particles; frozen catalytic pocket; RTX 5080 Laptop GPU) passed frame-count and reproducibility audits. The first ligand-bound simulation (6.1 ns total = 3,050,000 steps × 2 fs, including initialization) carried three defects found by audit: coordinates printed in nanometers but labeled Å, a "backbone" selection that included 21,684 water oxygens, and a Zn²⁺ parameter identity error (Li-2013 12-6 CM set, ε = 0.00330286 kcal/mol, not the intended Li–Merz 2014 12-6-4 subset, ε = 0.02662782). The corrected analysis (whole-molecule periodic imaging, protein-backbone Kabsch fit) gives ligand internal RMSD mean 1.847 Å / max 2.370 Å and protein backbone RMSD mean 2.175 Å / max 2.679 Å.

A second run (3.1 ns total = 0.1 ns initialization + 3.0 ns production, with the 12-6 subset of the 12-6-4 parameter set [18] — the C4 cation-induced-polarization term is not implemented in AmberTools and is absent from both runs) examined the mechanism question. The crystal phosphocholine centroid was mapped into the analysis frame via the backbone Kabsch transform (fit RMSD 1.875 Å). Occupancy under the audit-recorded 6 Å-center + 4.5 Å-catalytic-contact conjunction (added post hoc during audit-driven analysis; the original pre-registration contained no occupancy criterion) was 0/620 frames — the center condition fails, not the contact condition. Catalytic residues N318, H319, H457, and T458 (crystal numbering) are contacted in every saved frame: H457 in 620/620 frames, N318 in 414/620, T458 in 23/620, H319 in 11/620, with the nearest catalytic-residue heavy atom at 2.63–3.93 Å. Radius sensitivity is substantial: relaxing the center cutoff from 6 Å to 8 Å changes occupancy to 30.3%; 10 Å to 100%. The supported conclusion is narrow: under the recorded joint criterion the ligand fails the center condition while maintaining at least one catalytic-residue contact in every frame. Neither result establishes absence of binding or stable metal coordination (Figure 4).

### Predictive triage: model separation

Three model artifacts are distinguished using data resources and modeling tools described below [7,8] (Figure 5). (i) The legacy RF500 run (raw retrieved records, scripts/herg_karim.py) produced earlier candidate probabilities. (ii) MODEL-A is a refit on canonicalized, deduplicated full data (scripts/herg_model_separation.py) — not a verified legacy reproduction (only 1/26 legacy values reproduced at tolerance; a training-protocol change, not random variation). (iii) MODEL-B (RF300) is trained on the archived 80% stratified split of the deduplicated hERG_Central dataset (306,879 canonical records; SHA256 and split indices archived); held-out ROC-AUC = 0.909147 (95% CI not computed due to single split; AP = 0.4792 by sklearn average_precision_score), independently recomputed by the auditor from saved per-sample predictions. The 80/20 split is random (not scaffold-based); chemical-series leakage is possible and not assessed. Candidates lie 0.290–0.724 Tanimoto similarity from their nearest training molecule (no near-duplicate threshold was defined; the observed range is the directly supported statement). Random-split performance and Morgan similarity do not establish scaffold-level generalization; these values are screening priors, not safety verdicts.

### Three-arm feasibility pilot

Five natural target-evidence tasks were executed across three arms: A (single agent, 14.6 min total), B (multi-agent, 36.3 min), C (audited multi-agent, 40.8 min). All 15 executions produced non-trivial artifacts. This is a feasibility demonstration of the benchmark infrastructure, not an effectiveness comparison: no prespecified accuracy rubric was applied, no blinded human assessment was obtained, and agent call counts differ across arms (A: 5 calls; B: 15; C: 20). Arm A nominated ACHE; Arms B/C nominated APP — multiple explanations (prompt differences, role framing, evidence access) are possible and were not controlled.

### Seeded-error development test and coverage

The project exercised 18 seeded cases across 9 error classes. Case definitions and expected outcomes were frozen in `scripts/benchmark_full.py` before that execution, but the checks and cases were designed within the same project and this was not an externally registered or held-out benchmark. The checks detected 15/18 seeded cases (83%). Three misses exposed check-layer mismatches (C4-b: a numeric epsilon check cannot catch a citation-versus-execution mismatch; C6-a: an atom-name whitelist cannot catch residue-name contamination; C8-c: naive numbering cannot catch mapping errors without the id2ord cross-table). One control case (C9-b) exposed a labeling/semantics defect, so the run does not support a zero-false-positive claim. In a separate development replay, 12/13 artifact-replayable findings produced detection flags; one delegated ParmEd record remained null. These results describe coverage of this project-specific test suite, not general sensitivity or 12 new scientific validations (Figure 6).

### Synthesis planning

The AiZynthFinder installation [9] was checked by running a stock-present target through the pipeline (trivial closure, demonstrating only that the software executes end-to-end). CHEMBL7385 is present in the proxy stock (0-step closure) and EXP_CHEMBL24974-CF3 returned no closed route. Because the official ZINC stock file (1.34 GB) could not be retrieved (persistent zenodo gateway 504; best transfer 77%), all closures are PROXY closures and no purchasability claim is made.

---

## Discussion

**What the audit cycle changed.** Iterative audit and repair converted a coherent-looking report into a materially different one. The reference-anchor error removed a claimed potency calibration. The unit, selection, and parameter errors invalidated the original mechanistic interpretation; the corrected trajectory showed no saved frame below the stated 4 Å zinc-distance threshold. The direction counterexample changed the clinical framing from "consistently beneficial" to "contested, model-dependent." In this campaign, artifact-level checks exposed errors that the producing agent's summaries did not surface; whether artifact-level review generally outperforms summary-level review requires controlled evaluation.

**Negative and corrected results as outputs.** The pipeline's corrections include: a reference misattribution (SMPD2/SMPD1), a parameter-identity error (12-6 executed, 12-6-4 cited), a unit error (nm as Å), a direction counterexample (PMID 27598773), a metric that could not measure what it claimed (COM-imaged RMSD), and a stochastic-precision hazard (legacy RF500 outputs vary at the second decimal upon re-training). Each was found by a different check type — frame counting, force-field inspection, live re-query, literature fetch, independent recomputation, re-training — supporting the use of heterogeneous check types, though no controlled comparison of check-type effectiveness was performed.

**SMPD1 as case-study target.** After the direction counterexample and the reference misattribution were discovered, SMPD1's suitability as a case-study target was reassessed. It remains defensible: the enzyme has structural availability (PDB 5I85), a clear catalytic mechanism (dizinc hydrolase), database evidence of absent approved small-molecule drugs (zero ChEMBL mechanism records at CHEMBL2760, scoped to that endpoint), and a real connection to cognitive impairment through Niemann-Pick disease and sphingolipid signaling. The weakness is the absence of a human-genetic evidence line and the contested direction of modulation — both documented rather than hidden.

**Limitations.** No wet-lab data exist; all affinities and toxicities are predictions. Simulations are short (apo 5.81 ns, bound 6.1 + 3.1 ns), unreplicated, lack the C4 polarization term of the 12-6-4 model, and used single receptor conformations. The redocking validation uses a lenient matching convention pending graph-aware revalidation. The synthesis stage never reached real purchasability assessment (service-blocked stock; PROXY closures only). The study covers one target; the seeded-error benchmark measures within-case coverage but does not establish general audit sensitivity; no controlled comparison against a no-audit or checklist-only baseline was performed. The round-4 verdict-authority conflict was resolved by adjudication (CONFIRM REJECT), but repair acceptance required subsequent rounds — the distinction between accepting findings and accepting repairs is a key methodological lesson.

**Positioning.** We offer this work as an inspectable computational case study with its full audit trail — a documented failure analysis, not a validated drug-discovery result. The pipeline is designed to be target-agnostic; the audit protocol is designed to be agent-agnostic. Transfer to other targets and agent stacks remains to be demonstrated.

### Conclusion

We executed an end-to-end computational drug-discovery workflow, subjected it to adversarial audit across multiple rounds, and measured the deterministic check catalog's coverage on a project-specific seeded-error development test. The surviving output is deliberately modest: a testable hypothesis with contested direction and weak anchoring; a candidate set whose docking scores and predictive-model rankings remain experimentally unvalidated; and a documented audit protocol whose transfer beyond this case is untested. In this campaign, raw-artifact verification exposed errors that producing-agent summaries missed. Controlled held-out evaluation of audit sensitivity, false acceptance, repair completeness, and resource cost remains future work.

---

## Methods

### Ethics and AI disclosure

This study is entirely computational and involves no human subjects, animal experiments, or wet-laboratory work. Two AI systems (GLM/ZCode and GPT/Codex) contributed as tools under human direction and supervision. All AI-generated content was verified by the corresponding author. The producing AI system's outputs were audited by the auditing AI system; the human supervisor approved all corrections and final scientific decisions. The full AI interaction log (research-log.md, entries D0–D29) is provided in supplementary materials.

### Target-evidence integration

Open Targets GraphQL API v4 [1] (platform-api.opentargets.org/api/v4/graphql) was queried for disease-gene associations using EFO identifier MONDO_0004975 (Alzheimer disease) and HP_0100543 (cognitive impairment). Per-target data retrieved included known drugs, tractability assessments, safety liabilities, genetic constraint scores, mouse phenotypes, baseline expression (RNA-TPM), and prioritisation items. PubMed E-utilities were queried for literature trend counts (gene AND Alzheimer/cognitive, 2015–2019 vs 2023–2025; gene AND inhibitor, 2015–2025). ChEMBL REST API v33 [2,12] was queried for target records (CHEMBL2760), activities, and mechanisms. All data were retrieved on 2026-09-12. Scripts: scripts/ot_fetch_assoc.py, scripts/ot_fetch_targets.py, scripts/ot_scores_trends.py, scripts/score_panel.py, scripts/chembl_check.py, scripts/pubmed_direction.py.

### Structure preparation and docking

PDB 5I85 [24] (human ASM with Zn and phosphocholine, 2.5 Å resolution) chain A was retained. OpenBabel 3.1.1 added hydrogen atoms at pH 7.4. Torsion records were stripped to produce a rigid receptor PDBQT. AutoDock Vina 1.2.7 [3] docking used exhaustiveness 8, seed 42, a 24 Å box centered at (−13.710, −34.100, −28.720), and num_modes 5. Redocking validation used exhaustiveness 32, an 18 Å box, and 9 modes. The docking box center was set from the co-crystal phosphocholine centroid. Cross-crystal ensemble docking on 5I81 and 5JG8 used Ca-Kabsch superposition (528 matched Ca atoms). Scripts: scripts/prep_5i85.py, scripts/redock.py, scripts/ensemble_prep.py, scripts/ensemble_dock.py.

### Virtual screening library and ligand preparation

A 20,111-molecule library was retrieved from ChEMBL [2,12] (filters: MW 250–450, TPSA ≤ 90, HBD ≤ 2, ALogP 1.5–4.5; retrieved 2026-09-12 via REST API with checkpointing). PAINS A/B/C, Brenk, and charge filters (via RDKit FilterCatalog [10]) reduced this to 11,758 molecules. A Bemis–Murcko scaffold cap (≤4 per scaffold) produced a 3,500-molecule docking set (2,138 unique scaffolds). Ligands were prepared with RDKit ETKDGv3 [10] for 3D embedding and MMFF94s for optimization; Meeko 0.8.0 generated PDBQT files. Molecule identifiers were cross-checked against PubChem where applicable [11]. Calculated property definitions were interpreted against established drug-likeness, solubility, and permeability literature [19-21]. pH 7.4 protonation rules: carboxylic acids deprotonated, aliphatic amines protonated, aromatic/azole N neutral. Scripts: scripts/build_library_v2.py, scripts/diversity_prefilter.py, scripts/rdkit_prepare.py, scripts/dock_runner.py.

### Molecular dynamics

OpenMM 8.6.1 [4] (conda-forge, CUDA platform, mixed precision) on NVIDIA RTX 5080 Laptop GPU (16 GB). Force field: Amber14 ff14SB protein + TIP3P water. Solvation: 10 Å padding, 0.15 M NaCl, PME 1.0 nm cutoff. PDBFixer modeled missing residues and hydrogens.

**Apo simulation (frozen-pocket protocol):** 140,875 particles; catalytic-pocket heavy atoms and 2 Zn²⁺ mass-0 dummy particles at crystal positions; all other particles free; Langevin middle integrator, 310 K, dt 1 fs, NVT; 100 ps heating + 5.78 ns production; DCD frames every 5 ps. Scripts: scripts/md_run.py.

**Bound v2 simulation:** 73,333 particles; chain A from the 1 ns apo snapshot (crystal frame, heavy atoms only); + LIG (GAFF2/AM1-BCC via antechamber) at docked pose; + 2 ZN (charge +2, Li–Merz 12-6 subset from frcmod.ions234lm_1264_tip3p; build-time assertion confirmed ε = 0.02662782); TIP3P 21,684 waters; Langevin middle, 310 K, dt 2 fs, constraints on H–bonds; 100 ps heating + 3.0 ns production; DCD frames every 5 ps. Scripts: scripts/build_bound.sh, scripts/bound_md.py.

**Pocket-residence analysis:** scripts/pocket_residence_r7.py, with trajectory handling cross-checked against MDAnalysis conventions [17]; crystal PC centroid mapped into the analysis frame via backbone Kabsch transform (fit RMSD 1.875 Å); occupancy = ligand center within 6 Å of mapped centroid AND ≥1 catalytic-residue heavy atom within 4.5 Å (criterion added post hoc during audit-driven analysis; not in original preregistration).

### Predictive models

DeepPurpose 0.1.5 [7] (Morgan fingerprint encoder, pretrained): BBB penetration, P-gp inhibitor, CYP3A4/2D6 inhibitor, Caco-2 permeability, HIA, ClinTox. Scripts: scripts/admet_predict.py.

**hERG and DILI models:** Trained from Therapeutics Data Commons datasets [8]. hERG: 306,879 canonical-dedup records from hERG_Central; RF300; stratified 80/20 split (indices archived in results/herg_central_repro/split_indices.npz); held-out ROC-AUC 0.9091. DILI: 475 molecules; RF500; held-out ROC-AUC 0.888. Scripts: scripts/herg_central_repro.py, scripts/herg_dili.py.

### Retrosynthesis

AiZynthFinder 4.4.1 [9] with USPTO ONNX policy and filter models. Proxy stock: 20,111 ChEMBL molecules (InChIKey CSV). Config: aizynth_config.yml (time_limit 120 s, max_depth 6). Official ZINC stock service-blocked (zenodo 504).

### Adversarial audit protocol

The audit was conducted through fresh-context GPT/Codex sessions using the same model family as an auditing tool; this provides procedural role separation, not model diversity or statistical independence. The record contains iterative review, repair, re-review, an adjudication, and later acceptance checks through R11, followed by a scoped final acceptance record. In each cycle, the producer supplied reports and frozen artifacts; the auditor re-derived selected claims, recorded stable findings and evidence paths; the producer repaired or withdrew claims in new revisions; and the auditor checked the resulting revision. Mutation testing required altered copies to make applicable deterministic checks fail. The full audit trail is retained in `independent-audit/` and `research-log.md`.

### Seeded-error benchmark

Eighteen cases across nine error classes were defined and frozen in `scripts/benchmark_full.py` before execution of that development run. The classes were identity swap, unit swap, duration error, parameter swap, hash staleness, selection contamination, numeric claim, residue mapping, and chronology claim. The check authors also designed the cases, and two labels (C4-b and C9-b) required correction after design errors; the exercise is therefore reported as a development test rather than a preregistered or held-out benchmark. Scripts: `scripts/benchmark_full.py`, `scripts/findings_replay_executed.py`.

### Three-arm pilot

Arm A: single codex exec per task (no role separation). Arm B: three sequential role calls (target-analyst → molecular-designer → simulation-analyst). Arm C: four calls including an independent auditor. 5 tasks × 3 arms. Scripts: scripts/benchmark_runner.py, runs/benchmark-v1/.

### Statistical methods

Proportions reported with exact numerator/denominator. Continuous metrics: mean, max, final values. No formal statistical hypothesis tests were performed because this study is a single-arm case study without a priori power calculation. McNemar's test and Wilcoxon signed-rank are specified in PROTOCOL_v1.md for future three-arm comparisons but were not executed in this iteration.

---

## Data availability

The local submission package contains the scripts, fetched data, computed results, trajectories, audit reports, and frozen manifests used for this case study. The complete decision trail is in `research-log.md`, and the development-test definitions are in `scripts/benchmark_full.py`. A public, versioned repository with a persistent identifier has not yet been created. The corresponding author must deposit the release and replace this statement with its URL, DOI, license, and access date before submission.

## References

[1] Open Targets Platform. https://platform.opentargets.org (accessed 12 September 2026).

[2] ChEMBL Database. https://www.ebi.ac.uk/chembl (accessed 12 September 2026).

[3] Trott, O. & Olson, A. J. AutoDock Vina: improving the speed and accuracy of docking with a new scoring function. *J. Comput. Chem.* **31**, 455–461; https://doi.org/10.1002/jcc.21334 (2010).

[4] Eastman, P. et al. OpenMM 7: rapid development of high performance algorithms for molecular dynamics. *PLoS Comput. Biol.* **13**, e1005659; https://doi.org/10.1371/journal.pcbi.1005659 (2017).

[5] McNutt, A. T. et al. GNINA 1.0: molecular docking with deep learning. *J. Cheminform.* **13**, 43; https://doi.org/10.1186/s13321-021-00522-2 (2021).

[6] Krivák, R. & Hoksza, D. P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites from protein structure. *J. Cheminform.* **10**, 39; https://doi.org/10.1186/s13321-018-0285-8 (2018).

[7] Huang, K. et al. DeepPurpose: a deep learning library for drug-target interaction prediction. *Bioinformatics* **36**, 2464–2466; https://doi.org/10.1093/bioinformatics/btaa1005 (2021).

[8] Huang, K. et al. Therapeutics Data Commons: machine learning datasets and tasks for drug discovery and development. *arXiv* 2102.09548; https://doi.org/10.48550/arXiv.2102.09548 (2021).

[9] Genheden, S. et al. AiZynthFinder: a fast, robust and flexible open-source software for retrosynthetic planning. *J. Cheminform.* **12**, 39; https://doi.org/10.1186/s13321-020-00472-1 (2020).

[10] RDKit: open-source cheminformatics. https://www.rdkit.org (accessed 18 September 2026).

[11] Kim, S. et al. PubChem Substance and Compound databases. *Nucleic Acids Res.* **44**, D1202–D1213; https://doi.org/10.1093/nar/gkv951 (2016).

[12] Zdrazil, B. et al. The ChEMBL Database in 2023: a drug discovery platform spanning multiple target classes and disease areas. *Nucleic Acids Res.* **52**, D1180–D1192; https://doi.org/10.1093/nar/gkad1004 (2024).

[13] Kunkle, B. W. et al. Genetic meta-analysis of diagnosed Alzheimer's disease identifies new risk loci and implicates Aβ, tau, immunity and lipid processing. *Nat. Genet.* **51**, 414–430; https://doi.org/10.1038/s41588-019-0358-2 (2019).

[14] Jenkins, R. W. et al. Acid sphingomyelinase as a pathological and therapeutic target in neurological disorders: focus on Alzheimer's disease. *Exp. Mol. Med.* **56**, 1656–1667; https://doi.org/10.1038/s12276-024-01176-4 (2024).

[15] Novellino, F. et al. Inhibition of acid sphingomyelinase reduces reactive astrocyte secretion of mitotoxic extracellular vesicles. *Acta Neuropathol. Commun.* **11**, 131; https://doi.org/10.1186/s40478-023-01633-7 (2023).

[16] Ledesma, M. D. et al. Role of sphingomyelinases in neurological disorders. *Expert Opin. Ther. Targets* **19**, 1–14; https://doi.org/10.1517/14728222.2015.1071794 (2015).

[17] Michaud-Agrawal, N. et al. MDAnalysis: a toolkit for the analysis of molecular dynamics simulations. *J. Comput. Chem.* **32**, 2319–2327; https://doi.org/10.1002/jcc.21787 (2011).

[18] Li, P., Song, L. F. & Merz, K. M. Parameterization of highly charged metal ions using the 12-6-4 LJ-type nonbonded model in explicit water. *J. Phys. Chem. B* **118**, 663–675; https://doi.org/10.1021/jp505875v (2014).

[19] Daina, A. et al. SwissADME: a free web tool to evaluate pharmacokinetics, drug-likeness and medicinal chemistry friendliness of small molecules. *Sci. Rep.* **7**, 42717; https://doi.org/10.1038/srep42717 (2017).

[20] Delaney, J. S. ESOL: estimating aqueous solubility directly from molecular structure. *J. Chem. Inf. Comput. Sci.* **44**, 1000–1005; https://doi.org/10.1021/ci034243x (2004).

[21] Egan, W. J. & Lauri, G. Prediction of intestinal permeability. *Adv. Drug Deliv. Rev.* **54**, 273–289; https://doi.org/10.1016/S0169-409X(02)00004-2 (2002).

[22] Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold. *Nature* **596**, 583–589; https://doi.org/10.1038/s41586-021-03819-2 (2021).

[23] The UniProt Consortium. UniProt: the Universal Protein Knowledgebase in 2023. *Nucleic Acids Res.* **51**, D523–D531; https://doi.org/10.1093/nar/gkac1052 (2023).

[24] Berman, H. M. et al. The Protein Data Bank. *Nucleic Acids Res.* **28**, 235–242; https://doi.org/10.1093/nar/28.1.235 (2000).

## Acknowledgements

The author acknowledges the use of GLM/ZCode and GPT/Codex as disclosed computational tools. No AI system is listed as an author.

## Funding

The author reports that this research received no external funding.

## Author contributions

Yiming Zuo: Conceptualization, methodology, software, investigation, supervision, project administration, writing — original draft, writing — review and editing, final scientific decisions, accountability.

**AI tool contributions (disclosed, not authorship):** GLM/ZCode producer agent — pipeline implementation, computation, data curation, initial draft preparation. GPT/Codex auditor agent — independent verification, numerical recomputation, objection generation.

## Competing interests

The author declares no competing interests.

## Additional information

Correspondence and requests for materials should be addressed to Yiming Zuo (Gnimi114514@whut.edu.cn).

## Figure legends

**Figure 1** Pipeline, agents, and audit loop (G0–G6 stages; producer/auditor/human roles; audit rounds; blocked synthesis branch; verdict-authority conflict resolved by adjudication). Source: AUTOMATION.md, runs/audit-20260913/gates.json.

**Figure 2** Target evidence and reference-identity correction. (A) 22-gene weighted evidence matrix (weights: genetics 0.30, mechanism 0.20, novelty 0.20, safety 0.20, druggability 0.10); SMPD1 highlighted. (B) µM anchors are SMPD2 records; CHEMBL310981 vs human SMPD1 = 49 µM (single-molecule record). Source: data/panel_scores.json, data/ot_associations.json.

**Figure 3** Screening funnel and score interpretation. (A) 20,111 → 11,758 → 3,500 → 3,642 with registered batch merges. (B) Vina distribution; −7.0 = internal ranking convention; best raw: CHEMBL54786, −8.92 kcal/mol. Source: results/funnel_registry.json, results/hits_ranked.csv.

**Figure 4** Corrected bound-state MD (v2). (A) Ligand RMSD in protein frame (mean 4.579/max 5.935 Å). (B) Ligand-center distance to crystal centroid. (C) Min Zn–ligand distance (saved-frame range 4.18–7.71 Å; no frame below 4 Å). Occupancy 0/620 frames under the conjunction recorded in md/bound_analysis_pre_registered.json post_hoc_additions section (6 Å center + 4.5 Å catalytic contact; the center condition fails while the contact condition holds in every frame; substantial radius sensitivity: 8 Å → 30.3%, 10 Å → 100%); catalytic contacts present in every saved frame; C4 term omitted from both runs. Source: md/bound_v2.dcd, independent-audit/round8-acceptance/c1_evidence.json.

**Figure 5** Model separation and synthesis boundaries. (A) MODEL-B held-out ROC (AUC 0.9091, independently recomputed; n = 61,376). (B) Precision–recall (AP 0.479, labeled as average precision). (C) Candidate probabilities by model version — MODEL-A is a deduplicated refit, not a verified reproduction of the legacy RF500 run; the discrepancy is a training-protocol change, not random variation. (Inset: synthesis closures are PROXY only.) Source: results/herg_central_repro/models/, runs/audit-20260913/tasks/syn-01/.

**Figure 6** Audit trajectory. Findings raised per review round (R1: 11, R2: 5, R3: 7, R4: 3, R5: 4 + residuals, R6: 4 + residuals, R7: 5 + residuals, R8: 4 + residuals, R9: 3 + residuals, R10: 2, R11: 0 [ACCEPT]). All producer-accepted. Round-4 verdict-authority conflict resolved by adjudication (CONFIRM REJECT). Source: runs/audit-20260913/gates.json, independent-audit/round4-acceptance/adjudication.md.
