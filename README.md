# Audited Agentic Drug Discovery SMPD1 Case Study

This repository contains the code, audit trail, development benchmarks, figures, and manuscript sources for an AI-agent computational drug-discovery case study centered on human acid sphingomyelinase (SMPD1).

The scientific contribution is an inspectable workflow and failure-analysis record. It is not an experimentally validated drug-discovery result. The candidates, docking scores, predictive-model outputs, simulations, and routes are computational hypotheses. The final computational gate was conditional and did not establish affinity, efficacy, selectivity, safety, purchasability, synthesis feasibility, or experimental validation.

## What is included

- `src/scripts/`: analysis, orchestration, audit, and benchmark scripts.
- `workflow/`: audit protocol, automation notes, decision log, and frozen manifest.
- `audit/`: independent review, repair, adjudication, and acceptance records.
- `benchmarks/`: seeded-error development test, finding replay, and three-arm feasibility pilot.
- `results/`: compact computed tables and model summaries.
- `data-snapshots/`: selected small source snapshots used in the case study.
- `case-study/`: target, structure, hit, validation, and integrated reports.
- `manuscript/`: Scientific Reports-formatted manuscript, cover letter, supplementary information, and figures.

## Important evaluation boundaries

- The 15/18 seeded-error result measures coverage of a test designed within this project. It is not a held-out estimate of general audit sensitivity.
- The three-arm pilot demonstrates execution feasibility. The 15 outputs were not independently scored for scientific correctness, and the arms used unequal numbers of Agent calls.
- Fresh-context producer and auditor roles provide procedural separation. They do not establish model diversity or statistical independence.
- Proxy stock closure is not evidence of current availability or experimental synthesis.

## Large artifacts

Multi-gigabyte molecular-dynamics trajectories, third-party model weights, the interrupted ZINC stock download, build caches, and redistributable third-party datasets are excluded from GitHub. Their identities, checksums, and scope are documented in the audit records and manuscript. A separate archival deposit is required for long-term preservation of large project-owned artifacts.

## Reproduction entry points

Start with:

1. `workflow/AUDIT.md`
2. `workflow/research-log.md`
3. `workflow/audit_manifest.json`
4. `manuscript/SR_MANUSCRIPT_PRESUBMISSION_v2.md`
5. `audit/round11-acceptance/round11-acceptance.md`

Commands and environments are heterogeneous because the case study spans Windows and WSL2. See `ENVIRONMENT.md` before running scripts. A successful process exit does not imply scientific acceptance; inspect the associated result, review, and gate record.

## Authorship and AI disclosure

Yiming Zuo is the accountable human author. GLM/ZCode and GPT/Codex were used as disclosed computational tools and are not authors.

## Citation

See `CITATION.cff`. Replace the repository URL and release identifier in downstream citations after the first public release is created.

## License

Code is released under the MIT License. Original text, figures, and project-generated data are released under CC BY 4.0. Third-party data and software retain their original licenses and are not relicensed by this repository.
