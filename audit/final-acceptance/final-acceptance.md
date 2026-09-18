# Round 15 Final Acceptance Audit

**Audit date:** 2026-09-14 (Asia/Shanghai)  
**Scope:** `audit_manifest.json`, the reframed manuscript, full seeded benchmark,
executed real-findings replay, producer/auditor skill drafts, installed skill, and
`runs/audit-20260913/gates.json`.  
**Write boundary:** This audit created files only under
`independent-audit/final-acceptance/`.

## Overall verdict

**ACCEPT-WITH-MINOR-NOTES**

The frozen hash-bearing manifest entries all match, the manuscript's scientific and
benchmark claims are appropriately scoped, the requested benchmark outcomes and replay
counts are present, and the skill is structurally valid. Two internal bookkeeping
issues remain:

1. `benchmark_full_results.json` contains **28**, not 30, cases: 18 seeded and 10
   controls. Neither that JSON nor `scripts/benchmark_full.py` contains two additional
   supplementary cases. This does not change the reported 15/18 seeded detection result.
2. `gates.json` retains stale `outcome=BLOCKED` and
   `team_skill_gate_state.G6_integration=BLOCKED` fields, while its round-11 history and
   top-level `g6_state` establish the later controlling state as **CONDITIONAL**.

These are bounded metadata/inventory inconsistencies rather than failures of the
reported 18-seed benchmark result or the accepted frozen computational handoff.

## A. Manifest integrity

**PASS.** The manifest has 58 path entries: 56 hash-bearing file entries and two
explicit `missing: true` declarations. Independent SHA256 and byte-size recomputation
gave:

| Check | Result |
|---|---:|
| Hash-bearing entries | 56 |
| SHA256 matches | 56 |
| SHA256 mismatches | 0 |
| Byte-size matches | 56 |
| Declared-missing entries absent as declared | 2/2 |
| Unexpected missing/present paths | 0 |

`audit_manifest.json` does not list itself. The producer's description of “56 files”
is accurate if it means hash-bearing files; the complete manifest has 58 entries when
the two missing-path declarations are included.

## B. Manuscript final state

**PASS.** Review of `paper/MANUSCRIPT_DRAFT_v2_reframed.md` found:

| Requirement | Verdict | Observation |
|---|---|---|
| Forbidden overclaim markers | PASS | Exact uppercase `UNRESOLVED`, `lead pose`, `13/13 detected`, and `15 ns` are absent. Lowercase “unresolved” remains only for explicitly retained limitations. |
| Drug/translation overclaims | PASS | “validated drug” occurs only in the negated phrase “not a validated drug candidate”; `de-risked` is absent. |
| Adjudication wording | PASS | “resolved by adjudication (CONFIRM REJECT for round 4)” is present in the audit history and discussion. |
| Occupancy chronology | PASS | The occupancy criterion is described as “added post hoc during audit-driven analysis,” “defined during audit-driven analysis after the run,” and a “post-hoc addition”; it is not called pre-specified. |
| Gate numbering | PASS | The manuscript formalizes and uses team-skill G0 scope through G6 integration. |
| Replay count | PASS | The contribution statement says “12/13 detected + 1 delegated”; abstract/results/conclusion consistently describe 12 detected and R1-3 delegated/null. |
| Total MD | PASS | The headline total is `14.9 ns total MD`, consistent with 5.8 + 6.1 + 3.1 ns after rounding. |
| Finding count | PASS | `18 stable ledger findings` is used, with five intervening objections separately qualified. |
| Benchmark validation scope | PASS | Validation is expressly limited to the 18-seed/10-control within-case benchmark and is explicitly not presented as general audit sensitivity. |

The hyphenation alternates between `post hoc` and `post-hoc`, but the chronology and
meaning are consistent throughout.

## C. Benchmark integrity

**PASS-WITH-MINOR-NOTE.** Direct parsing produced:

| Item | Observed | Verdict |
|---|---:|---|
| Serialized total cases | 28 | NOTE: requested expectation was 30 |
| Seeded cases | 18 | PASS |
| Seeded detected | 15 | PASS |
| Seeded missed | C4-b, C6-a, C8-c | PASS |
| Controls | 10 | PASS |
| Apparent control false positive | C9-b | PASS |
| Miss/label analysis | Present for all four cases | PASS |

The file's `summary.total_cases` is 28 and its `cases` array also has 28 entries. The
source script registers those same 28 cases. Thus “18 seeded + 10 controls + 2
supplementary = 30” is not supported by the supplied full-benchmark artifact. C9-b is
preserved as the one apparent false positive and correctly analyzed as a ground-truth
labeling/check-semantics error, yielding zero confirmed false positives after
adjudication.

The real-findings replay **passes**: 13 replay records, 12 with `detected=true`, and one
delegated/null record, R1-3, because ParmEd was unavailable in the Windows interpreter
and verification was delegated to WSL. The JSON summary is derived from those observed
record values.

## D. Skill validity

**PASS.** The producer draft enumerates all eight requested production disciplines:
freeze order, identity, direction counterexample search, executed parameter provenance,
coordinate frames, honest scoping, model-version hygiene, and mutation testing.

The auditor draft contains seven principal deterministic check families: manifest
recomputation, frame/time arithmetic, periodic/reference-frame geometry, force-field
identity, live database identity, residue mapping, and mutation testing. Self-reference
checking is also explicitly part of manifest verification. Both halves cite mutation
testing and concrete mutation recipes/evidence.

The installed `C:/Users/Gnimi/.agents/skills/audited-drug-discovery/SKILL.md` exists.
Its YAML frontmatter is delimited correctly and contains nonempty `name` and
`description` fields; both referenced supporting files exist.

## E. Gate status

**PASS-WITH-MINOR-NOTE.** The historical chronology is clear even though two fields are
stale. Earlier `BLOCKED` values describe the pre-acceptance state. The last history
entry, round 11, records `ACCEPT-WITH-MINOR-NOTES` and “G6: CONDITIONAL for the frozen
computational handoff,” and the dedicated `g6_state` is `CONDITIONAL` with five explicit
conditions.

## Definitive G6 recommendation

**G6 = CONDITIONAL for the frozen computational handoff.** Treat the legacy
`outcome=BLOCKED` and `team_skill_gate_state.G6_integration=BLOCKED` fields as
superseded historical metadata, not the controlling current verdict. Conditions remain:
proxy-only synthesis closure, delegated R1-3 ParmEd replay, format-specific R3-6 replay,
no conversion of replay detection into scientific validation, and the stated scientific
limitations (no wet-lab validation, short unreplicated MD, omitted C4 term, single-target
case study).

The 28-versus-30 benchmark inventory note does not alter G6 because the manuscript and
benchmark conclusions use the verified 18-seed/10-control denominators rather than a
30-case claim.
