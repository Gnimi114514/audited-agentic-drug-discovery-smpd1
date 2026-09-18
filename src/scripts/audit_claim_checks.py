"""Artifact consistency checks, not biochemical validation or an LLM auditor.

Inputs must come from independently extracted evidence. This module cannot establish
that a caller-supplied topology, source record, or chronology is authentic.
"""
import hashlib
import math
from pathlib import Path


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('expected a finite number')
    if not math.isfinite(value):
        raise ValueError('expected a finite number')
    return value


def nonempty(value):
    if not isinstance(value, (str, list, dict)) or not value:
        raise ValueError('missing evidence')
    return value


def object_value(value):
    if not isinstance(value, dict) or not value:
        raise ValueError('expected a nonempty object')
    return value


def text_value(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('expected a nonempty string')
    return value


def list_value(value):
    if not isinstance(value, list) or not value:
        raise ValueError('expected a nonempty list')
    return value


def evaluate(record, evidence_root):
    """Return PASS/DEFECT/UNVERIFIABLE; never consume benchmark truth labels."""
    try:
        object_value(record)
        kind = text_value(record['kind'])
        claim, evidence = object_value(record['claim']), object_value(record['evidence'])
        if kind == 'identity':
            fields = ('target_id', 'taxon_id')
            pairs = [(text_value(claim[k]), text_value(evidence[k])) for k in fields]
            if not all(v.isdigit() and int(v) > 0 for v in pairs[1]):
                raise ValueError('taxon_id must be a positive numeric string')
            bad = any(a != b for a, b in pairs)
        elif kind == 'distance':
            scales = {'nm': 10.0, 'angstrom': 1.0}
            actual = number(evidence['value']) * scales[evidence['unit']]
            stated = number(claim['value']) * scales[claim['unit']]
            bad = not math.isclose(actual, stated, rel_tol=1e-6, abs_tol=1e-6)
        elif kind == 'duration':
            steps = evidence['steps']
            if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
                raise ValueError('invalid integration step count')
            dt = number(evidence['dt_fs'])
            if dt <= 0 or number(claim['ns']) < 0:
                raise ValueError('invalid duration or timestep')
            bad = not math.isclose(steps * dt / 1e6, claim['ns'], rel_tol=1e-6, abs_tol=1e-9)
        elif kind == 'parameters':
            # Expected coefficients must be supplied from the cited parameter source.
            expected = object_value(claim['coefficients'])
            built = object_value(evidence['coefficients'])
            bad = any(not math.isclose(number(v), number(built[k]), rel_tol=1e-6, abs_tol=1e-9)
                      for k, v in expected.items())
            terms = [text_value(t) for t in list_value(claim['required_terms'])]
            actual_terms = [text_value(t) for t in list_value(evidence['force_terms'])]
            bad = bad or not set(terms).issubset(actual_terms)
        elif kind == 'hash':
            root = Path(evidence_root).resolve()
            path = (root / nonempty(evidence['path'])).resolve()
            if not path.is_relative_to(root):
                raise ValueError('evidence path outside case root')
            digest = nonempty(claim['sha256'])
            if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
                raise ValueError('invalid SHA256')
            bad = hashlib.sha256(path.read_bytes()).hexdigest() != digest
        elif kind == 'selection':
            if claim['definition'] != 'protein_backbone':
                raise ValueError('unsupported selection claim')
            atoms = list_value(evidence['selected_atoms'])
            # Membership is topology-derived, not inferred from atom name O.
            for atom in atoms:
                object_value(atom)
                text_value(atom['name'])
                if type(atom['is_protein']) is not bool:
                    raise ValueError('missing protein membership')
            bad = any(not a['is_protein'] or a['name'] not in ('N', 'CA', 'C', 'O') for a in atoms)
        elif kind == 'upper_bound':
            values = list_value(evidence['values'])
            limit = number(claim['maximum'])
            bad = any(number(v) > limit for v in values)
        elif kind == 'residue_mapping':
            mapping = object_value(evidence['topology_to_crystal'])
            for key, value in mapping.items():
                text_value(key)
                text_value(value)
            contacts = list_value(evidence['contacts'])
            if any(type(i) is not int or i < 0 for i in contacts):
                raise ValueError('contacts must be nonnegative topology indices')
            stated = [text_value(i) for i in list_value(claim['crystal_residues'])]
            actual = {mapping[str(i)] for i in contacts}
            bad = actual != set(stated)
        elif kind == 'chronology':
            phases = {'pre_specified', 'post_hoc'}
            if claim['phase'] not in phases or evidence['phase'] not in phases:
                raise ValueError('unknown chronology phase')
            bad = claim['phase'] != evidence['phase']
        else:
            raise ValueError('unknown check kind')
        return {'status': 'DEFECT' if bad else 'PASS', 'kind': kind,
                'reason': 'claim disagrees with evidence' if bad else 'claim agrees with evidence'}
    except (KeyError, TypeError, ValueError, OSError, OverflowError) as exc:
        return {'status': 'UNVERIFIABLE', 'reason': str(exc)}
