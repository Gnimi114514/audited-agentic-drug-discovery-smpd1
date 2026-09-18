# Round 8 independent acceptance audit

**Overall: REJECT. G6 recommendation: remain BLOCKED.**

Fresh-session review on 2026-09-14 of the files present in the supplied workspace. The new crystal-to-analysis fit reproduces the requested numerical results, but disclosure, replay implementation, freeze integrity and report integration still fail. Producer repair assertions in research-log.md are not corroborated by the submitted bytes.

| Claim | Verdict | Independently checked evidence |
|---|---|---|
| 1. New saved-trajectory pocket analysis | PASS for requested numerical reproduction; periodic-box implementation caveat | Rerun: 620 frames, fit RMSD 1.875 Å, mapped centroid (52.181, 56.884, 42.440) Å, occupancy 0/620, contacts [318,319,457,458], ligand RMSD mean 4.579 / max 5.935 / final 5.638 Å. See geometry supplement below. |
| 2. Post-hoc disclosure propagated | FAIL | JSON and final-report.md explicitly disclose post-hoc additions. Both manuscript Results versions still say “occupancy criterion fixed in advance”; assembled abstract still says “recorded before the run.” |
| 3. Replay counting and artifact-backed checks | FAIL | Counting remains at line 164, before R1-10 append at 165. Saved records contain 12 true + 1 null, but summary.detected is 11. R1-2, R3-1 and R3-6 remain literal checks. |
| 4. Final-byte freeze and handoffs | FAIL | Correct five-level counts 35/15/7/2/7, totaling 66. Only 65/66 hashes and sizes match. research-log.md is stale. Evidence handoff exits 0; reports handoff exits 1. |
| 5. Report residuals | FAIL | Mean/max labels and 3.1 ns v2 total are present, and the obsolete non-catalytic-surface assertion is removed. Threshold, ensemble, per-residue-frequency and retired-metric contradictions remain. |
| Assembled manuscript Results sync | FAIL as a corrected-deliverable claim | Results body matches the section draft exactly, but both contain the same uncorrected provenance claim. Actual file is paper/MANUSCRIPT_DRAFT_v1.md; the requested paper/manuscript_MANUSCRIPT_DRAFT_v1.md does not exist. |

## Mandatory findings

**R8-1 — Manuscript provenance remains contradictory (R7-2 not closed).** `paper/manuscript_results_discussion.md:82` and `paper/MANUSCRIPT_DRAFT_v1.md:203` call the criterion “fixed in advance,” contradicting their later “added post hoc” disclosure. The assembled abstract at lines 29–31 says the specification was recorded before the run. Figure 4 at lines 336–342 still only cites the pre-registration-named JSON without explicitly disclosing the post-hoc criterion. The JSON's `post_hoc_additions` and final report lines 214–215 are successful partial repairs. Reconcile the abstract, Results, Methods/legend provenance and section source together; a later disclaimer does not resolve the earlier false chronology.

**R8-2 — Replay source and output are still inconsistent (R7-3 not closed).** `scripts/findings_replay_executed.py:164` computes detected_n before the R1-10 record at line 165. The saved output now has extra `detected_true: 12`, `delegated: 1` fields and a revised detection_rate string, but retains `detected: 11`; those extra fields/string are not produced by the current source. R1-2 at lines 34–40 compares literal 0.47 × 10 with 4.7 and never opens bound_run.log. R3-1 at lines 137–140 supplies a literal observation and True. R3-6 at lines 159–162 evaluates a literal list without parsing structure-analysis.md. Move counting after registration, implement actual artifact-backed checks, and regenerate the complete output from the repaired source. A delegated/null record is not a successful executed detection.

**R8-3 — The research-log freeze is still stale (R7-4 not closed).** Root manifest and reports handoff expect 60,461 bytes and SHA256 `15546e473610ddded1f286c821ee6f5fb72b4ca938a63454b793f4e0d818a2b9`. Current bytes are 62,685 and SHA256 `38010a0c3e33e56db5d8557241b60d07e53440f72410458a96a774674c41115a`. The reports checker reports `artifacts[5]: artifact SHA256 mismatch`. D22 itself asserts the final freeze passed, but is not included in the frozen bytes. Complete edits, freeze leaves, rebuild dependent handoffs, then freeze their root hashes without subsequently appending to frozen reports. The other 65 root entries pass; the root has no self-reference.

**R8-4 — Report residuals and canonical evidence remain unreconciled (R7-5 not closed).**

- `hit-report.md:17` still says reference chemotypes yield ≤ −7.0, although its table shows −6.96/−6.34/−6.01.
- `structure-analysis.md:58–62` acknowledges crystal/MD ensemble docking but retains the dangling “and no ensemble docking was performed / campaign)” contradiction.
- `final-report.md:63` still implies all four named catalytic residues persist in every frame. Its detailed paragraph gives H457 620/620 but omits the other per-residue frequencies; the manuscript correctly lists N318 414/620, H319 11/620, H457 620/620 and T458 23/620.
- `final-report.md:226–227` still infers pocket occupancy from the retired COM-imaged RMSD, contradicting both the metric's retirement and the joint-criterion zero-occupancy result.
- `final-report.md:210` cites `runs/audit-20260913/tasks/sim-02/attempt-1/pocket_residence.json` for 4.579/5.935 Å. That canonical artifact still contains the rejected r5fix translation method and RMSD 4.696/6.050/final 5.753 Å. The new r7 summary is correct numerically but has not replaced or been properly linked as the authoritative evidence. Preserve old results as explicitly superseded and update current citations.

## Geometry supplement

The independent calculation pulled the mapped center back into each trajectory frame using a separately implemented row-vector SVD fit, then applied minimum imaging in the native cell. It confirms **0/620 at 6 Å, 188/620 (30.323%) at 8 Å, and 620/620 at 10 Å**. Center distances span **6.554525–9.992969 Å**. Contact counts independently reproduce **N318 414, H319 11, H457 620, T458 23**; all other seven selected pocket residues have zero contacts. Protein-frame ligand RMSD is mean **4.579386 Å**, max **5.935434 Å**. The 2,112 selected backbone atom names match the crystal ordering.

**R8-N1 — Non-blocking for this trajectory, but repair before reuse:** producer lines 94–95 minimum-image a fitted vector using the unrotated cell. A general implementation must rotate the cell with the coordinates or pull the center back into the native frame. Its contact distances also omit pairwise minimum imaging. Here the independent native-cell calculation agrees with the rounded producer distances within **0.000503 Å** and reproduces all contact/occupancy results, so these implementation limitations do not invalidate the verified numbers for these saved frames. The crystal-frame repair closes the numerical R7-1/R7-1b regression; it does not close the stale canonical-artifact integration finding.

## Scope, execution and limitations

Only `independent-audit/round8-acceptance/` was written. `run_pocket.py` executes the unchanged producer source using WSL `~/miniforge/envs/md/bin/python -B`; a guarded open redirects its two output JSON files into this audit directory. No new dynamics were run. Source inspection showed that the requested direct invocation would overwrite producer artifacts, so it was not used unguarded. Rerun stdout and both generated JSON files are retained here.

`check_artifacts.py` independently streamed SHA256 over all 66 root entries, checked byte sizes, and invoked the installed `check_handoff.py` with `--root` and `--require artifacts` for both r8 handoffs. It independently counted saved replay records and inspected source/line order; the full live-network/TDC replay suite was not rerun, and the delegated parmed check was not newly executed. No claim of full replay-suite execution is made.

As a supplementary integration check, the existing `paper/manuscript_revision_manifest.json` has seven mismatches, including both manuscript files, audit_manifest.json, final-report.md and research-log.md. It is an older D18 snapshot, not the new root freeze; this does not negate the 65 root matches, but it cannot certify the current paper. Detailed paths are retained in manifest_checks.json.

Acceptance here concerns the consistency and reproducibility of the submitted evidence package. Zero occupancy under an audit-added criterion does not demonstrate experimental nonbinding. Existing direction, short/unreplicated MD, omitted C4, graph-aware redocking and real-stock synthesis limitations remain; this review does not waive any upstream gate. G6 should remain BLOCKED until the mandatory repairs are implemented, regenerated, frozen and independently rechecked.
