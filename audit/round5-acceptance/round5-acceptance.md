# Round 5 acceptance audit

**Decision: REJECT. G6 must remain BLOCKED pending repair and fresh acceptance.**

Fresh-session review of the repaired revision, 2026-09-14 (Asia/Shanghai). All audit outputs and redirected reruns are confined to this directory; producer artifacts were not modified. This is artifact acceptance, not experimental validation.

| Requested repair | Result | Evidence |
|---|---|---|
| 1. Pocket analysis | PARTIAL / FAIL scientifically | Box scaling and placeholder removal repaired; requested RMSD 4.579/5.935 Å, `[319,458]`, units note, and preserved v1 all present. Residue selection still uses `id2ord[r]+1` against zero-based topology resSeq, omitting contacted catalytic N318/H457. Correct crystal contacts are `[318,319,457,458]`. Crystal pocket center is also not transformed into the minimized-reference frame. See `pocket_checks.json`. |
| 2. MODEL-A lineage | Disclosure PASS; explicit serialization withdrawal incomplete | Both reports distinguish raw-record legacy RF500 from canonical-deduplicated refit, and disclose 1/26 agreement. MODEL-B owns the held-out AUC. Final report makes no fitted-estimator serialization claim and describes saved-score evaluation, but does not explicitly withdraw serialization or state fitted estimators are absent. |
| 3. Integrated report closures | FAIL | Corrective paragraphs were inserted without removing contradictory current conclusions; details below. |
| 4. Manifest freeze | FAIL | Correct five-level structure, no root self-reference; only **54/55** root hashes and sizes match. R6 reports checker exits **1**; R6 evidence checker exits **0**. |
| 5. Benchmarks | Seeded PASS; claimed replay FAIL | Five classes/5 detections/zero false positives reproduce. Stored replay counts are 13 plus five context-only, but the script hardcodes detection statuses, executes no artifact replay, and reruns to stale `18/18` summary text. |

## Integrated report findings

The following T numbers follow the user's round-5 checklist. The original round-4 evidence uses different numbering (T3 mean/max, T4 old gate, T5 threshold, T6 ensemble denial); both sets were checked.

- **T1 FAIL:** final-report.md:207–211 contains corrected RMSD and center-condition-fails language, but line 59 still describes the obsolete non-catalytic surface residues, and lines 221–222 still assert pocket occupancy from retired COM-imaged RMSD.
- **T2 PASS:** final-report.md:232–244 and hit-report.md:200–213 disclose the legacy/refit distinction and 1/26 reproduction.
- **T3 PASS:** final-report.md:234 labels 0.4792 as average precision and identifies `average_precision_score`.
- **T4 FAIL:** final-report.md:175–176 labels mean/max, but banner lines 20–21 still present 1.85–2.37 and 2.18–2.68 Å as unlabeled ranges.
- **T5 FAIL:** literal `old-G1 PASS` and `G5 PASS |` are absent, but line 60 retains `old-G5 PASS` outside the historical mapping table. Narrow string checks do not close the actual finding.
- **T6 FAIL:** no internal-ranking-convention disclosure appears in final-report.md. It exists in structure-analysis.md:41–42, while hit-report.md:17 still claims the references yield ≤ −7.0 despite its table listing −6.96, −6.34, −6.01.
- **T7 FAIL:** final-report.md:23 and 169 cite current `complex.prmtop` for v1 parameters; no rereview-r3 snapshot citation appears.
- **Original R4-T6 also FAIL:** structure-analysis.md:58–59 denies ensemble docking despite its line-34 ensemble results.

## Mechanical evidence

`manifest_checks.json` records every L1–L5 entry, expected/actual SHA256, size, and checker stdout. The only stale root leaf is `research-log.md`:

- Expected: `3b846393c022900bb276db2db51f052c02b3636c334ef7f3a188936ce10505d2`, 54,211 bytes.
- Actual: `b9af72bd976430384f27ae985375410d094f19f2283985291d0d5a1a7be6086c`, 56,642 bytes.
- R6 reports fails `artifacts[5]: artifact SHA256 mismatch` on that same file. R6 evidence passes all supplied artifact checks.
- Reviewed root SHA256: `18194bde7d5b16974b4ffb28a21c3a6f1bb08d17bc437318031bd69a694ebf6f`.

An append-only-history explanation does not make an outdated frozen hash valid.

## Mandatory repairs

1. Fix actual catalytic-residue selection, validate residue identities against crystal numbering, and transform the crystal pocket center into the analysis reference frame. Regenerate pocket output and update contacts throughout reports. The requested `[319,458]` literal is present but is not the complete independently verified contact set; do not preserve that incomplete target as a correctness criterion.
2. Remove or explicitly supersede all report contradictions listed above, cite the frozen v1 topology provenance, and explicitly limit model reproducibility to archived scores/refit outputs rather than fitted-estimator serialization.
3. Execute actual artifact-backed checks for the 13 replayable findings, deriving counts from observations, and make the producing script regenerate the corrected denominator. Until then, label the hardcoded list as a coverage inventory rather than executed replay. Correct the seeded script's 15-case documentation to its actual five-case/five-control design; the five simplified fixtures do not establish broader error-detection sensitivity.
4. After all changes, freeze the reports including the final research-log bytes, then regenerate nested handoffs and root manifest. Require both handoff checks and every root entry to pass without subsequent leaf changes.

Supporting machine-readable results: `round5_checks.json`, `text_checks.json`, `manifest_checks.json`, `pocket_checks.json`, `benchmark_checks.json`. Passing numerical and disclosure subchecks do not override the remaining deterministic failures.
