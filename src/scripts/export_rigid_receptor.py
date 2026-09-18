"""Lossless atom-record projection, not receptor chemical preparation."""
import argparse
import base64
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def project(data):
    atoms, kept, removed, charges, ids = [], [], [], [], set()
    controls = Counter()
    for number, raw in enumerate(data.splitlines(keepends=True), 1):
        line = raw.rstrip(b"\r\n").decode("ascii")
        if line.startswith(("ATOM  ", "HETATM")):
            if len(line) < 78:
                raise ValueError(f"line {number}: short atom record")
            try:
                serial = int(line[6:11])
                xyzq = [float(line[a:b]) for a, b in [(30,38),(38,46),(46,54),(70,76)]]
                int(line[22:26])
            except ValueError as exc:
                raise ValueError(f"line {number}: malformed atom numeric field") from exc
            if serial <= 0 or serial in ids:
                raise ValueError(f"line {number}: duplicate or nonpositive atom id")
            if not all(math.isfinite(x) for x in xyzq):
                raise ValueError(f"line {number}: nonfinite coordinate/charge")
            if not line[12:16].strip() or not line[17:20].strip() or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", line[77:].strip()):
                raise ValueError(f"line {number}: missing identity or malformed atom type")
            ids.add(serial)
            charges.append(xyzq[-1])
            atoms.append(raw)
            kept.append(raw)
            continue
        # Preserve comments and empty lines byte-for-byte; reject every unknown record.
        if not line.strip() or line == "REMARK" or line.startswith("REMARK "):
            kept.append(raw)
            continue
        kind = next((k for k in ("ENDBRANCH", "ENDROOT", "TORSDOF", "BRANCH", "ROOT") if line.startswith(k)), None)
        if kind is None:
            raise ValueError(f"line {number}: unexpected record")
        tail = line[len(kind):]
        if kind in ("ROOT", "ENDROOT"):
            valid = not tail.strip()
        elif kind == "TORSDOF":
            valid = bool(re.fullmatch(r"\s+\d+\s*", tail))
        else:
            spaced = re.fullmatch(r"\s+(\d+)\s+(\d+)\s*", tail)
            fixed = len(tail) == 8 and all(re.fullmatch(r" *[0-9]+", tail[i:i+4]) for i in (0,4))
            valid = bool(spaced or fixed)
            if valid:
                pair = [int(x) for x in spaced.groups()] if spaced else [int(tail[:4]),int(tail[4:])]
                valid = all(x > 0 for x in pair) and pair[0] != pair[1]
        if not valid:
            raise ValueError(f"line {number}: malformed {kind} record")
        controls[kind] += 1
        removed.append({"line": number, "record": kind, "text": line, "raw_base64": base64.b64encode(raw).decode()})
    if not atoms:
        raise ValueError("no atom records")
    output = b"".join(kept)
    return output, {
        "scope": "rigid atom-record export only; no ligand-tree validation or chemical preparation",
        "input_sha256": sha(data), "output_sha256": sha(output),
        "atom_count": len(atoms), "atom_bytes_sha256": sha(b"".join(atoms)),
        "atom_records_byte_identical": True,
        "removed_counts": dict(controls), "removed_records": removed,
        "torsion_context": "not validated; recognized records removed regardless of balance",
        "charge_audit": {"count": len(charges), "zero_count": sum(q == 0 for q in charges), "minimum": min(charges), "maximum": max(charges), "sum": sum(charges)},
        "ad4_readiness": "NOT_READY_FOR_AD4" if all(q == 0 for q in charges) else "NOT_VALIDATED_FOR_AD4",
        "limitations": ["All-zero charges cannot establish receptor electrostatic preparation; Zn zero charge alone may be intentional in AD4Zn.", "No hydrogen, protonation, metal-state, parameter-consumption or model validation.", "No grids, docking or G2 acceptance."],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output_dir", type=Path)
    args = p.parse_args()
    output, report = project(args.input.read_bytes())
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "rigid.pdbqt").write_bytes(output)
    (args.output_dir / "export.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k != "removed_records"}, indent=2))


if __name__ == "__main__":
    main()
