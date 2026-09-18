# Cover Letter

Dear Editors,

**Corresponding author:** Yiming Zuo, School of Chemistry, Chemical Engineering and Life Sciences, Wuhan University of Technology, Luoshi Road 122, Hongshan District, Wuhan 430070, Hubei Province, China. Email: Gnimi114514@whut.edu.cn. ORCID: 0009-0001-3280-1027.

We submit our manuscript "Auditing an AI-Agent Computational Drug-Discovery Workflow Through an SMPD1 Case Study" for consideration in *Scientific Reports*.

## Why this work fits Scientific Reports

Digital Discovery publishes work that advances methods for data- and AI-driven chemical discovery. Our manuscript reports three contributions in that scope:

1. **An inspectable, fully computational target-to-candidate workflow** built from open tools (Open Targets, ChEMBL, PDB, Vina, OpenMM, AmberTools, GNINA, P2Rank, DeepPurpose, TDC, AiZynthFinder) on consumer hardware (RTX 5080 Laptop, 16 GB). Every headline number is tied to a script and a raw artifact; the complete decision trail (28 decision entries) is released.

2. **An adversarial audit protocol with measured development-test coverage.** Fresh-context audit identified consequential errors including reference-target misattribution, unit mislabeling, a force-field citation-versus-execution mismatch, and a literature direction counterexample. Repairs and withdrawals were tracked across revisions. A project-specific seeded test detected 15/18 cases; because the same project designed the checks and cases, we do not present this value as general sensitivity or as an independent benchmark. A control-label defect also prevents a zero-false-positive claim.

3. **Preserved negative and corrected results.** The corrected campaign conclusions are weaker than the originals: the µM activity anchors belong to a different enzyme (SMPD2, not SMPD1), the lead pose does not coordinate the catalytic zinc under the modeled conditions, and the direction-of-modulation question remains open. These are reported as first-class findings, not suppressed.

## What this work is not

This is not a validated drug candidate. No wet-lab engagement, efficacy, selectivity, safety, or purchasability data exist. All affinities and toxicities are predictions. The simulations are short and unreplicated. The audit protocol's generalization beyond this single case study is untested. We state all of these limitations explicitly.

## Why the audit protocol matters

The most transferable result is the documented observation that raw-artifact recomputation changed conclusions that survived producer self-review. We provide the audit trail, stable finding identifiers, and mutation-test recipes so that others can inspect and extend the protocol. We make no comparative performance claim because the three-arm pilot assessed execution feasibility rather than scientific correctness.

## AI disclosure

Two AI systems contributed to this work as disclosed tools (not accountable authors): a GLM/ZCode producer agent (pipeline implementation, computation, repair) and a GPT/Codex auditor agent (independent verification, benchmark evaluation). The human supervisor provided conception, oversight, and final scientific decisions. All AI-generated content was verified by the human supervisor.

## Data and code availability

Code, compact project-generated data, audit records, development benchmarks, figures, and manuscript sources are publicly available at https://github.com/Gnimi114514/audited-agentic-drug-discovery-smpd1 (release `v0.1.0`). Multi-gigabyte molecular-dynamics trajectories and third-party datasets are not hosted on GitHub; their identities, checksums, and scope are documented in the repository. No wet-laboratory data were generated. A DOI-backed archival release is planned separately.

## Reviewer and editorial disclosures

The author does not propose specific reviewers or request the exclusion of any reviewer at this stage. The author has had no prior discussion of this manuscript with a Scientific Reports Editorial Board Member.

Sincerely,

Yiming Zuo  
Electronically signed by the corresponding author
