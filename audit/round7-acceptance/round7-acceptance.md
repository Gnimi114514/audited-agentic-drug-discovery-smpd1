# Round 7 acceptance audit

**Overall: REJECT. G6 recommendation: remain BLOCKED.**

Fresh-session review, 2026-09-14. The claim that all round-6 mandatory repairs are complete is not supported. Only this audit directory was written.

| Requested item | Result | Independent evidence |
|---|---|---|
| 1. Crystal-center transform | **FAIL** | Saved-trajectory rerun exits 0 and reproduces **0/620**, units note and translated-center definition. However, the center remains **133.1095 Å** from its independently mapped position in the analysis reference frame. |
| 2. Occupancy provenance | **FAIL** | JSON explicitly marks **ADDED POST HOC** and denies an original occupancy criterion. Final report still says **pre-specified**; Figure 4 does not explicitly identify the criterion as audit-added/post hoc. |
| 3. R1-10 replay | **FAIL** | R1-10 is now appended and independently reproduces **1.756967144 Å**. There are 13 records, 12 true and 1 delegated/null, but saved summary incorrectly says **11 detected / 13**. Hardcoded replay observations remain. |
| 4. Freeze | **FAIL** | Five levels, **62 entries**, no self-reference; **61/62** current hashes/sizes match. `research-log.md` is stale. Reports handoff exits **1**; evidence handoff exits **0**. |
| 5. Report residuals | **FAIL** | Contact mapping, banner mean/max labels and 3.1 ns total are repaired. The hit-report threshold and structure-analysis ensemble contradictions remain. Current RMSD output also disagrees with the report. |

## Mandatory findings

**R7-1 — Coordinate frames remain inconsistent.** `scripts/pocket_residence_r5fix.py:64-74` assumes `bound_ref.pdb` is in the raw crystal frame. Its backbone centroid is actually (58.0209, 51.6798, 43.8364) Å, close to DCD frame 0. The computed offset is only (−0.17134, −0.05080, −0.01567) Å. Adding this to the raw crystal PC centroid produces (−13.8843, −34.1489, −28.7403) Å. Independently fitting 2,112 crystal backbone atoms to the analysis reference instead maps the center to (52.1805, 56.8840, 42.4398) Å. The fit RMSD is 1.875 Å; this does not explain the 133.11 Å frame discrepancy. The claimed rigid translation also has per-atom offset standard deviations of 0.484–0.575 Å, not approximately zero.

At lines 92–101 the ligand is fitted to unchanged `ref_bb`, then compared with `POCKET_CENTER_DCD0`. Minimum imaging does not repair this mismatched coordinate origin; box vectors must also be expressed consistently with fitted coordinates. Zero occupancy from this calculation is not validated scientific evidence. Map the crystal center through an explicit matched crystal-to-analysis transform and use a coherent coordinate/box convention throughout.

**R7-1b — New RMSD regression.** Line 74 translates `ref_lig` without translating the backbone reference to which `lig_p` is fitted. The rerun and current producer summary now report ligand RMSD **mean 4.696 / max 6.050 / final 5.753 Å**. `final-report.md:211-212` retains **4.579 / 5.935 Å**. Correct the frame implementation before deciding which output to propagate; do not merely replace the report numbers with the inconsistent calculation.

**R7-2 — Post-hoc disclosure is incomplete.** `md/bound_analysis_pre_registered.json` honestly labels the additions and explicitly states the original pre-registration had no occupancy criterion. But `final-report.md:214` still calls the conjunction pre-specified. The assembled manuscript retains fixed-in-advance/pre-specified claims, and its Figure 4 legend merely points to the pre-registration-named JSON. A filename reference does not disclose post-hoc provenance. Reconcile all occurrences and revisit radius-sensitivity claims after the frame correction.

**R7-3 — Replay summary still omits R1-10 from the numerator.** `scripts/findings_replay_executed.py:164` computes `detected_n` before the append at line 165. Thus the saved output has 12 true records and one null but reports 11/13. Recording via direct append satisfies the requested registration mechanism; counting before registration does not. R1-2 still checks literal 0.47 × 10 against 4.7; R3-1 supplies a literal observation and `True`; R3-6 checks a literal score list. These cannot support the blanket assertion that every finding is replayed against its cited artifact.

**R7-4 — Current-byte freeze fails.** `research-log.md` is **60,461 bytes**, versus frozen **58,520**. Expected SHA256 is `5e79363a5d5123b41a9a2a86f287c9bdf52b9a765428176d86cd5d36bffb36ef`; actual is `15546e473610ddded1f286c821ee6f5fb72b4ca938a63454b793f4e0d818a2b9`. Reports handoff reports `artifacts[5]: artifact SHA256 mismatch`. The root's append-after-hash note cannot waive the current-byte requirement. Complete edits before rebuilding dependent handoffs and the root freeze. The manifest note also says L1 has 32 entries although the actual level has 33; this is minor metadata beside the hash failure.

**R7-5 — Report contradictions remain.** `hit-report.md:17` still says reference results yield ≤ −7.0, contradicted by −6.96/−6.34/−6.01. `structure-analysis.md:58-60` acknowledges ensemble docking, but lines 61–62 retain the dangling “and no ensemble docking was performed … campaign)” claim. The final report's obsolete non-catalytic-surface sentence is removed, the N318/H319/H457/T458 mapping and H457 620/620 statement are present, mean/max banner labels are explicit, and timing now states 3.1 ns total. These successful repairs do not close the remaining failures.

The report also retains the retired COM-imaged-RMSD pocket-occupancy inference at `final-report.md:226-227`. Line 63 ambiguously implies all four named residues contact in every frame; the archived round-4 contact counts are N318 414/620, H319 11/620, H457 620/620, and T458 23/620. Phrase persistent aggregate catalytic contact separately from each residue's frequency.

## Execution and acceptance boundary

The WSL rerun executed the producer pocket computation with only its output destination redirected into this directory. It loaded the saved trajectory; no new simulation was run. Additional diagnostics independently fitted crystal backbone coordinates to the analysis reference. R1-10's actual parser/assignment block was executed in isolation against the current PDB/PDBQT; the full network/TDC replay suite was not rerun. All 62 root entries were hashed, and both handoffs were executed through the installed skill's `check_handoff.py` with `--require artifacts`.

Original pre-registration absence is corroborated by contemporaneous audit records and the current explicit correction; original pre-edit bytes were not recovered. Machine-readable verdicts are in `round7_checks.json`; supporting results are in `pocket_rerun.json`, `frame_diagnostics.json`, `pocket_stdout.txt`, `replay_checks.json`, `manifest_checks.json`, and `report_review.json`. This is rejection of the submitted computational evidence package, not proof of binding or nonbinding. G6 must remain blocked pending correction and fresh independent acceptance.
