# Structure & Pocket: SMPD1 (human acid sphingomyelinase)

## Model provenance

| Item | Value |
|---|---|
| Structure source | **PDB 5I85** — "aSMase with zinc and phosphocholine", X-ray, **2.5 Å**, human ASM (UniProt P17405), chain A |
| Ligands present | phosphocholine (**PC**, 11 heavy atoms) in active site; **Zn²⁺ ×2** (Zn714/Zn715, catalytic dinuclear center); glycosylation (NAG/MAN/BMA) and SO4 removed |
| Backup structures | PDB 5I81 (2.25 Å, apo + Zn); PDB 5JG8 (2.8 Å, human ASM) |
| Confidence at pocket | experimental structure → atomic confidence; no AF model needed. Catalytic residues resolved and coincide with ligand-contact set |
| Receptor prep | chain A + 2 Zn; waters/glycans/SO4 stripped; H added at pH 7.4 (OpenBabel); rigid receptor PDBQT (torsion records removed — obabel's ligand-style records are rejected by Vina 1.2.7); Zn charge 0.000 (conservative, obabel default) |

## Pocket definition

| Item | Value |
|---|---|
| Method | **ligand transfer** (co-crystal PC centroid) — most reliable tier |
| Box center (redocking) | (−13.710, −34.100, −28.720), 18 Å cube |
| Box (screening) | same center, **24 Å cube** — widened to cover the hydrophobic lipid-tail channel adjacent to the headgroup pocket |
| Pocket residues (protein atoms within 5 Å of crystal PC, chain A) | **ASP206, HIS208, ASP278, HIS282, ASN318, HIS319, HIS425, HIS457, THR458, HIS459, TYR488** |
| Mechanistic sanity | residue set is exactly the annotated ASM catalytic site (dizinc ligating Asp/His pairs + His/Thr catalytic loop) — pocket is the true orthosteric site, not a detector artifact |

## Docking validation

| Test | Result |
|---|---|
| Protocol | Vina 1.2.7, exhaustiveness 32, seed 42, 18 Å box, 9 modes |
| **Redocking RMSD (top-ranked pose)** | 1.76 Å under a **lenient element-swap convention** (unconstrained permutation of same-element atoms — this is NOT a chemically-equivalence-aware matching); connectivity-constrained match 1.91 Å; name-based 2.52 Å. **Formal bond-order/protonation-aware graph-isomorphism revalidation NOT done — the redocking gate is PASS-with-caveat at best** |
| Redocking RMSD (best of 9 modes) | 0.96 Å (mode 7, −4.26 kcal/mol); modes 1-2 at 1.76/1.69 Å |
| **Cross-crystal redocking (5I81, 528-Ca Kabsch superposition, Ca-RMSD 0.17 Å)** | **1.52 Å → PASS** |
| **Cross-crystal redocking (5JG8, Ca-RMSD 0.54 Å)** | **1.77 Å → PASS** |
| Catalytic-Zn conservation across crystals | matched-pair displacement 0.15–0.70 Å (an initial "3.25 Å 5JG8 Zn shift" was a file-ordering artifact; QC-corrected) |
| Reference-inhibitor docking (screening protocol, 24 Å box, ex 8) | CHEMBL418376 (1.0 µM **vs SMPD2**): **−6.96**; CHEMBL5284579 (1.8 µM vs SMPD2): **−6.34**; CHEMBL310981 (1.0–3.3 µM vs SMPD2; 49 µM vs human SMPD1): **−6.01** kcal/mol — **reference identity corrected after external audit; the µM anchors are NOT verified human-SMPD1 actives** |
| Ensemble re-docking of top 20 (5I81 / 5JG8; cross-crystal ensemble, see above) | 5I81 |Δ| median 0.17 (max 0.34) kcal/mol; 5JG8 systematically ~0.3–1.4 lower but all hits −6.99…−9.07; top-4 clean hits stable in all three crystals |

Empirical benchmark — **WITHDRAWN after external audit**: the "known 1–2 µM ASM
inhibitors" are µM actives of SMPD2 (CHEMBL4712), not human SMPD1 (CHEMBL310981 vs
human SMPD1 = 49 µM, activity 375434). Their docked scores here are −6.96, −6.34 and −6.01 (none ≤ −7.0); they demonstrate
only that the protocol scores sphingomyelinase-family binders in this range. They are
NOT a human-SMPD1 potency anchor and NOT evidence that sub-−7.0 scores indicate
activity. The campaign's −7.0 threshold is retained only as an
internal ranking convention, not a potency calibration.

## Caveats

- The only available validation ligand is **phosphocholine (11 heavy atoms)** — a small,
  headgroup ligand. Redocking under-constrains the hydrophobic tail channel; poses in
  that channel carry higher uncertainty than headgroup-region poses. No drug-like
  co-crystal exists for ASM, so a second-tier validation is impossible today (recorded
  as a permanent limitation of this target class).
- Zn²⁺ partial charges were left at 0.0 — metal-ligand interactions are therefore
  under-weighted by the Vina score; chemotypes that genuinely chelate the dizinc center
  may be undervalued (a bias *against* false positives, but possibly missing true
  metal-binding hits; note that permanent metal-chelators would also have poor
  selectivity — acceptable bias).
- 5I85 glycosylation loops were removed; glycan-stabilized surface regions remote from
  the catalytic pocket are unaffected by this choice.
- Ensemble docking WAS subsequently performed across three crystals and 5 MD snapshots
  (results/ensemble_scores.csv, results/md_ensemble_docking.csv); what remains un-done is
  multi-conformation ensemble docking *within* a single crystal field (e.g. side-chain
  rotamer ensembles). Flexible-loop (SMD/MD) effects on the entry channel are unassessed.
