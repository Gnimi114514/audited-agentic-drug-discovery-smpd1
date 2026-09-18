"""Build the methods-paper reframed MANUSCRIPT_DRAFT_v2."""
import re

v1 = open('paper/MANUSCRIPT_DRAFT_v1.md', encoding='utf-8').read()
i_m = v1.find('## Methods')
i_r = v1.find('## 3. Results')
i_c = v1.find('## 5. Conclusion')
i_d = v1.find('## 4. Discussion')
methods = v1[i_m:i_r].rstrip()
results = v1[i_r:i_c].rstrip()
discussion = v1[i_d:i_c].rstrip()

header = """# Benchmarking Adversarial Audit for Agentic Computational Drug-Discovery Workflows: An SMPD1 Failure-Analysis Case Study

**Authors (role disclosure):** GLM/ZCode producer agent (pipeline implementation,
computation, integration, repair); GPT/Codex auditor agent (independent verification,
objections, numerical recomputation, benchmark design review); [Human supervisor]
(conception, oversight, final scientific decisions, manuscript accountability). AI
systems are disclosed contributors, not accountable authors; human authors verify all
content before submission per journal policy.

**Target journal:** Digital Discovery (RSC) - methods/workflow contribution with a
failure-analysis case study.

## Abstract

AI agents can chain drug-discovery tools into apparently coherent research narratives
while propagating identity, unit, and provenance errors that survive self-review. We
present a seeded-error benchmark and an adversarial audit protocol for agentic
computational drug-discovery workflows, demonstrated on a complete end-to-end case
study: a target-to-candidate campaign against human acid sphingomyelinase (SMPD1,
UniProt P17405) for cognitive impairment, built from open tools (Open Targets, ChEMBL,
PDB, Vina 1.2.7, OpenMM 8.6.1, AmberTools, GNINA 1.3.3, P2Rank, DeepPurpose, TDC,
AiZynthFinder) on consumer hardware (RTX 5080 Laptop, 16 GB).

The producer agent executed the full pipeline: 22-gene evidence matrix, 3,642-molecule
virtual screen, 225-analog expansion, apo and ligand-bound MD (5.8 ns apo + 6.1 ns and
3.0 ns bound), ADMET predictions, and retrosynthesis - and produced internally
coherent reports containing 23 findings across 9 error classes: reference-target
misattribution (uM "SMPD1 actives" were SMPD2 records), unit mislabeling (nm printed
as Angstrom), force-field citation-vs-execution mismatch, a literature direction
counterexample, dataset-scale mislabeling, hash staleness, coordinate-frame errors,
and metric-definition defects. Adversarial audit in fresh contexts detected **13/13
artifact-replayable findings** with deterministic checks; 5 findings required live
literature or contextual review. A seeded-error benchmark (18 cases, 9 classes, ground
truth pre-registered) detected **15/18** injected defects; the 3 misses are expected
layer-mismatch cases (each was caught by a different check type in the actual audit);
1 control false-positive was a benchmark labeling error. The corrected campaign
conclusions are weaker than the originals: the lead pose does not coordinate the
catalytic zinc, the uM activity anchors belong to a different enzyme, and the
direction-of-modulation question remains open. The complete decision trail (D0-D27),
frozen manifests (77 entries, 5 levels), and all scripts are released for reuse. The
contribution is a validated check catalog with known coverage limits, not a validated
drug candidate.

---

"""

intro = """## 1. Introduction

AI agents can chain biomedical databases, docking engines, simulation packages, and
predictive models into research narratives that look coherent and cite real data -
while carrying identity, unit, provenance, and interpretation errors that survive
self-review. The problem is evidence transfer: a correct API response or a completed
simulation can still support an incorrect biological claim when the target identity,
the physical units, the reference frame, or the model version are silently lost between
steps.

Adversarial audit - independent fresh-context review operating on raw artifacts with
pre-registered or explicitly labeled post-hoc metrics - is one response. This paper
reports a complete cycle: an agentic producer executed a target-to-candidate drug-
discovery campaign; an independent auditor re-derived the claims from raw artifacts
across three review rounds plus an adjudication and two acceptance checks; 23 findings
were accepted and repaired; and a seeded-error benchmark was executed to quantify what
the deterministic check catalog can and cannot detect.

SMPD1 (acid sphingomyelinase) and cognitive impairment provide the case-study context.
The nomination of SMPD1 and the direction-of-modulation question are treated as
separate decisions; the audit found that the direction question remains open. The
campaign's candidates are reported as computational hypotheses, not validated leads.

Three contributions:
1. An inspectable target-to-candidate workflow (22-gene evidence matrix, 3,642-molecule
   screen, 225-analog expansion, 15 ns total MD, ADMET, model separation) with every
   headline number tied to a script and a raw artifact.
2. An adversarial audit protocol with a stable-ID finding ledger, deterministic
   check catalog, and adjudication procedure - validated by a seeded-error benchmark
   (15/18 detection; 0 false positives after labeling correction) and by real-finding
   replay (13/13 artifact-replayable findings).
3. Preserved negative and corrected results: the corrected campaign conclusions are
   weaker than the originals, and the residual open questions are stated.

"""

conclusion_new = """## 5. Conclusion

We executed an end-to-end computational drug-discovery workflow on consumer hardware,
subjected it to three rounds of adversarial independent audit plus an adjudication and
two acceptance checks, and applied repairs for every accepted finding (repair
completeness varies per the finding ledger: some verified repairs, some verified
withdrawals, some partial or open items remain). We then measured the deterministic
check catalog's coverage on a seeded-error benchmark: **15/18 injected defects
detected (83%), zero false positives after labeling correction, with all 3 misses
attributed to expected check-layer mismatches documented in the audit record.** The
real-findings replay confirmed 13/13 artifact-replayable audited findings are
reproducible by deterministic checks.

The surviving scientific output is deliberately modest: a testable, weakly-anchored
SMPD1 hypothesis; a candidate set whose docking and predictive-model positions are
internally consistent but experimentally unvalidated; a corrected simulation analysis
that rules out persistent catalytic-zinc coordination for the lead pose under the
modeled conditions; and a documented audit protocol with quantified coverage limits.
The most transferable result is the audit protocol itself and its measured coverage:
fresh-context reviewers operating on raw artifacts with pre-registered (where
applicable) and explicitly labeled post-hoc metrics found errors that summary-level
review missed in this campaign. Whether heterogeneous artifact-level checking
outperforms single-verifier review in general requires controlled evaluation we did
not perform.
"""

figure_legends = """
## Figure legends

**Figure 1 - Pipeline, agents, and audit loop** (G0-G6 stages; producer/auditor/human
roles; three audit rounds; blocked synthesis branch; verdict-authority conflict
resolved by adjudication). Source: AUTOMATION.md, runs/audit-20260913/gates.json.

**Figure 2 - Target evidence and reference-identity correction.** (A) 22-gene
weighted evidence matrix. (B) The uM anchors are SMPD2 records; CHEMBL310981 vs human
SMPD1 = 49 uM (single-molecule record). Source: data/panel_scores.json,
data/ot_associations.json.

**Figure 3 - Screening funnel and score interpretation.** (A) 20,111 -> 11,758 -> 3,500
-> 3,642 with registered batch merges. (B) Vina distribution; -7.0 = internal ranking
convention (best raw: CHEMBL54786, -8.92). Source: results/funnel_registry.json,
results/hits_ranked.csv.

**Figure 4 - Corrected bound-state MD (v2).** (A) Ligand RMSD in protein frame (mean
4.579/max 5.935 A). (B) Ligand-center distance to crystal centroid. (C) Min Zn-ligand
distance (saved-frame range 4.18-7.71 A; no frame below 4 A). Occupancy 0/620 under
the conjunction recorded post hoc in md/bound_analysis_pre_registered.json (8 A ->
30.3%, 10 A -> 100%); catalytic contacts present in every frame; C4 term omitted from
both runs. Source: md/bound_v2.dcd,
independent-audit/round8-acceptance/c1_evidence.json.

**Figure 5 - Model separation and synthesis boundaries.** (A) MODEL-B held-out ROC
(AUC 0.9091, independently recomputed; n = 61,376). (B) Precision-recall (AP 0.479).
(C) Candidate probabilities by model version - legacy RF500 run is stochastic-approximate
at re-training; MODEL-A is a deduplicated refit, not a verified legacy reproduction.
(Inset: synthesis closures are PROXY only.) Source:
results/herg_central_repro/models/, runs/audit-20260913/tasks/syn-01/.

**Figure 6 - Audit trajectory.** Findings per review round (11/5/7/3 in the respective
reports; five intervening objections summarized, not counted as independent findings);
all producer-accepted and repaired at their revision; ledger statuses per finding
(some partial or open). Round-4 verdict-authority conflict resolved by adjudication
(CONFIRM REJECT). Source: runs/audit-20260913/gates.json,
independent-audit/round4-acceptance/adjudication.md.
"""

v2 = (header + intro + "\n---\n\n" + methods + "\n\n---\n\n"
      + results + "\n\n---\n\n" + discussion + "\n\n---\n\n"
      + conclusion_new + "\n" + figure_legends)
open('paper/MANUSCRIPT_DRAFT_v2_reframed.md', 'w', encoding='utf-8', newline='\n').write(v2)
words = len(re.findall(r'\S+', v2))
print('MANUSCRIPT_DRAFT_v2_reframed.md assembled:', words, 'words')
