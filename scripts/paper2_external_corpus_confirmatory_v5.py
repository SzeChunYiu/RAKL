"""Paper II external-corpus confirmatory runner, v5 multi-family epoch.

Implements research/paper2_external_corpus_v1/PROTOCOL_V5_REDUCER.json:

    acquisition -> schema binding -> admission -> B3' FIRST (hard falsifier
    ordering) -> remaining battery -> confirmatory gates -> terminal

The v1..v4 line answered the question "does the next reducer discharge the
residual?" four times. This epoch asks instead whether the residual is
discharged by the *class* Paper II names -- a learned extractor -- by reading a
pre-registered set of correspondence families in one CONFIRM execution. A
negative then bounds the class rather than being re-attributed to a fifth
reducer.

The governing negative control is ``b3_prime``, not the original B3: the
original has expectation ``0.2304*(r_witness - r_control)`` under a
balance-preserving shuffle and so measures differential abstention. Both are
reported. See research/paper2_battery_repair_v1/.

Harness (pair construction, splits, scoring, bootstrap, scramble) is imported
from the v4 runner rather than re-implemented, so the split and the seeds are
the frozen ones by construction and cannot drift.

Usage:
    PYTHONPATH=src:. python scripts/paper2_external_corpus_confirmatory_v5.py \
        --csv research/paper2_external_corpus_v1/data/arn.csv \
        --out research/paper2_external_corpus_v1/results_v5_multifamily
"""

from __future__ import annotations

import argparse
import bisect
import csv
import json
import random
import statistics
import sys
from pathlib import Path

import numpy as np
import spacy
from sentence_transformers import SentenceTransformer

from rakl.battery_probes import b3_prime
from rakl.reduction_validation import AdmissionVerdict, ReducerProfile, admit_reducer
from rakl.structure_space import ReducedStructure
from rakl.support_solver import Atom, Obstruction, SupportEdge, SupportStructure

import scripts.paper2_external_corpus_confirmatory_v4 as H  # frozen harness

PROTOCOL = "research/paper2_external_corpus_v1/PROTOCOL_V5_REDUCER.json"
SPACY_MODEL = "en_core_web_sm"
ENCODER = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TRIPLES = 12
NEG_MISMATCH_FACTOR = 0.5

# Frozen grids (parent grids; ascending first-max tie-break via H.fit_theta).
GRID_COSINE = [round(0.02 * k, 2) for k in range(1, 50)]
GRID_LEXICAL = [round(0.02 * k, 2) for k in range(1, 50)]


# --- extraction ----------------------------------------------------------------

_nlp = None
_st = None


def _models():
    global _nlp, _st
    if _nlp is None:
        _nlp = spacy.load(SPACY_MODEL)
    if _st is None:
        _st = SentenceTransformer(ENCODER)
    return _nlp, _st


def triples(text: str) -> list[tuple[str, str, str, bool]]:
    """Predicate-argument triples with a negation flag, in document order."""
    nlp, _ = _models()
    out: list[tuple[str, str, str, bool]] = []
    for sent in nlp(text).sents:
        for tok in sent:
            if tok.pos_ != "VERB":
                continue
            subj = [c.lemma_.lower() for c in tok.children if c.dep_ in ("nsubj", "nsubjpass")]
            obj = [c.lemma_.lower() for c in tok.children if c.dep_ in ("dobj", "obj", "attr", "dative")]
            if not subj and not obj:
                continue
            neg = any(c.dep_ == "neg" for c in tok.children)
            out.append((subj[0] if subj else "_", tok.lemma_.lower(), obj[0] if obj else "_", neg))
    return out[:MAX_TRIPLES]


def masked(text: str) -> str:
    """Every content token replaced by its coarse class and syntactic role."""
    nlp, _ = _models()
    out: list[str] = []
    for sent in nlp(text).sents:
        for tok in sent:
            if tok.is_stop or tok.is_punct:
                continue
            if tok.pos_ in ("NOUN", "PROPN"):
                if tok.ent_type_ in ("PERSON", "NORP"):
                    cls = "PERSON"
                elif tok.ent_type_ in ("GPE", "LOC", "FAC"):
                    cls = "PLACE"
                else:
                    cls = "THING"
                out.append(f"{cls}-{tok.dep_}")
            elif tok.pos_ == "VERB":
                out.append(("NOT-" if any(c.dep_ == "neg" for c in tok.children) else "") + "ACT")
            elif tok.pos_ == "ADJ":
                out.append("ATTR")
    return " ".join(out)


def obstructed_lemmas(text: str) -> set[str]:
    """Lemmas lying under a negation or contrast in their own sentence.

    AMENDMENT_02. The first surface used only spaCy's ``neg`` dependency and was
    rejected by the admission gate's obstruction harvest: on the frozen parity
    calibration source the negations are a determiner ("no assignment satisfies
    all three") and a contrast verb ("x differs from z"), neither of which
    carries a ``neg`` arc, so the reducer surfaced no obstruction and the gate
    fail-closed. That is the gate doing its job -- an obstruction-blind reducer
    produces spaces that are unsound to navigate.

    The repair reuses the negation/contrast marker lexicon already frozen in this
    lineage (``narrative_reducer_v2.NEGATION_MARKERS``, used unchanged by v1-v4)
    in union with the ``neg`` arc, so the obstruction coordinate is continuous
    with the parent chain rather than newly invented here.
    """
    nlp, _ = _models()
    from rakl.narrative_reducer_v2 import NEGATION_MARKERS

    out: set[str] = set()
    for sent in nlp(text).sents:
        marked = any(t.lower_ in NEGATION_MARKERS for t in sent) or any(
            c.dep_ == "neg" for t in sent for c in t.children
        )
        if not marked:
            continue
        for tok in sent:
            if tok.pos_ in ("NOUN", "PROPN", "VERB") and not tok.is_stop:
                out.add(tok.lemma_.lower())
    return out


def reduce_narrative_v5(text: str) -> ReducedStructure:
    """Reducer surface for the admission gate.

    Roles are the triple arguments; relations are the subject/object pairs;
    obstructions cover the lemmas under a negation or contrast.
    """
    tr = triples(text)
    roles = frozenset(t for (s, v, o, _) in tr for t in (s, o) if t != "_")
    relations = frozenset((s, o) for (s, v, o, _) in tr if s != "_" and o != "_")
    atoms = tuple(Atom(atom_id=r) for r in sorted(roles))
    edges = tuple(
        SupportEdge(source=s, target=o, cost=1.0, licensed_at=0)
        for (s, o) in sorted(relations)
    )
    # An obstruction may only cover atoms the structure declares.
    obstructed = sorted(obstructed_lemmas(text) & set(roles))
    obstructions = (
        (
            Obstruction(
                obstruction_id="negation-or-contrast",
                cover=frozenset(obstructed),
                detail="lemmas in a sentence carrying a frozen negation/contrast marker or a `neg` arc",
            ),
        )
        if obstructed
        else ()
    )
    structure = SupportStructure(
        structure_id="arn-v5", atoms=atoms, edges=edges, obstructions=obstructions
    )
    return ReducedStructure(
        structure=structure,
        roles=roles,
        relations=relations,
        provenance="narrative_reducer_v5",
    )


# --- scores --------------------------------------------------------------------


class Scores:
    """Precomputed per-pair scores for every registered arm.

    Encoding is batched over the distinct strings of the split, so the scores do
    not depend on pair order.
    """

    def __init__(self, pairs):
        nlp, st = _models()
        texts = sorted({p.query_text for p in pairs} | {p.candidate_text for p in pairs})
        self.trip = {t: triples(t) for t in texts}

        whole = st.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
        self.whole = dict(zip(texts, whole))

        msk = st.encode([masked(t) for t in texts], normalize_embeddings=True,
                        batch_size=64, show_progress_bar=False)
        self.masked = dict(zip(texts, msk))

        tstr = sorted({f"{s} {v} {o}" for t in texts for (s, v, o, _) in self.trip[t]})
        temb = st.encode(tstr, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
        self.temb = dict(zip(tstr, temb))

    @staticmethod
    def _cos(a, b) -> float:
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        return float(a @ b / (na * nb)) if na and nb else 0.0

    def structural(self, q: str, c: str) -> float:
        """Instance-paired greedy correspondence over predicate-argument triples."""
        Q, C = self.trip[q], self.trip[c]
        if not Q or not C:
            return 0.0
        used: set[int] = set()
        total = 0.0
        for (s, v, o, ng) in Q:
            best, bj = 0.0, -1
            for j, (s2, v2, o2, ng2) in enumerate(C):
                if j in used:
                    continue
                val = float(self.temb[f"{s} {v} {o}"] @ self.temb[f"{s2} {v2} {o2}"])
                if ng != ng2:
                    val *= NEG_MISMATCH_FACTOR
                if val > best:
                    best, bj = val, j
            if bj >= 0:
                used.add(bj)
                total += best
        return total / len(Q)

    def masked_cos(self, q: str, c: str) -> float:
        return self._cos(self.masked[q], self.masked[c])

    def semantic(self, q: str, c: str) -> float:
        return self._cos(self.whole[q], self.whole[c])


def threshold_decision(score: float, theta: float) -> str:
    return "ACCEPT" if score >= theta else "REJECT"


def auc(scores: list[float], golds: list[str]) -> float:
    pos = sorted(s for s, g in zip(scores, golds) if g == "ACCEPT")
    neg = sorted(s for s, g in zip(scores, golds) if g == "REJECT")
    if not pos or not neg:
        return float("nan")
    total = 0.0
    for p in pos:
        lo = bisect.bisect_left(neg, p)
        hi = bisect.bisect_right(neg, p)
        total += lo + 0.5 * (hi - lo)
    return total / (len(pos) * len(neg))


# --- main ----------------------------------------------------------------------


def run(csv_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "schema_version": "paper2-external-corpus-result-v5-multifamily",
        "protocol": PROTOCOL,
        "grants_scientific_authority": False,
        "spacy_model": SPACY_MODEL,
        "encoder": ENCODER,
    }

    if not csv_path.exists():
        return {**result, "terminal": "CANNOT_CHECK__ACQUISITION", "reason": str(csv_path)}
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    result["acquisition"] = {
        "file": csv_path.name,
        "sha256": H.sha256_file(csv_path),
        "bytes": csv_path.stat().st_size,
        "n_rows": len(rows),
    }

    mapping = H.bind_mapping(header)
    if mapping is None:
        return {**result, "terminal": "CANNOT_CHECK__SCHEMA_MISMATCH", "header": header}
    result["mapping"] = mapping
    pairs, skipped = H.build_pairs_m3(rows, mapping)
    if len(pairs) < H.MIN_USABLE_PAIRS:
        return {**result, "terminal": "CANNOT_CHECK__SCHEMA_MISMATCH", "reason": f"{len(pairs)} pairs"}
    dev, confirm = H.split_pairs(pairs)
    result["pairs"] = {"total": len(pairs), "dev": len(dev), "confirm": len(confirm),
                       "skipped_rows": skipped}

    # --- admission -------------------------------------------------------------
    sample_groups: list[str] = []
    sample_sources: list[str] = []
    import hashlib
    for p in sorted(dev + confirm,
                    key=lambda p: hashlib.sha256(f"{p.group}:{H.SPLIT_SALT}".encode()).hexdigest()):
        if p.group not in sample_groups:
            sample_groups.append(p.group)
            sample_sources.append(p.query_text)
        if len(sample_sources) == 8:
            break
    profile = ReducerProfile(
        reducer_id="narrative_reducer_v5_multifamily",
        author="RAKL programme (same-context; LLM-assisted)",
        external_label_author="Sourati, Ilievski, Sommerauer, Jiang (ARN, TACL 2024)",
    )
    admission = admit_reducer(profile, reduce_narrative_v5, sample_sources, seed=H.SEED_SCRAMBLE)
    result["admission"] = {
        "verdict": admission.verdict.value,
        "admitted_kind": admission.admitted_kind.value if admission.admitted_kind else None,
        "reasons": list(admission.reasons),
    }
    if admission.verdict is not AdmissionVerdict.ADMITTED:
        return {**result, "terminal": "ADMISSION_REJECTED"}

    # --- DEV threshold fitting -------------------------------------------------
    print(f"encoding DEV ({len(dev)} pairs) ...", file=sys.stderr, flush=True)
    sdev = Scores(dev)
    dev_gold = [p.gold for p in dev]

    def fit(score_fn, grid):
        vals = [score_fn(p.query_text, p.candidate_text) for p in dev]
        return H.fit_theta(grid, lambda th: H.exact(
            [threshold_decision(v, th) for v in vals], dev_gold)), vals

    theta_struct, dev_struct = fit(sdev.structural, GRID_COSINE)
    theta_mask, dev_mask = fit(sdev.masked_cos, GRID_COSINE)
    theta_sem, dev_sem = fit(sdev.semantic, GRID_COSINE)
    theta_l = H.fit_theta(GRID_LEXICAL, lambda th: H.exact(
        [H.lexical_decision(p.query_text, p.candidate_text, th) for p in dev], dev_gold))

    dev_arms = {
        "control_semantic": [threshold_decision(v, theta_sem) for v in dev_sem],
        "control_lexical": [H.lexical_decision(p.query_text, p.candidate_text, theta_l) for p in dev],
        "control_band": [H.band_decision(p.band) for p in dev],
        "always_accept": ["ACCEPT"] * len(dev),
        "always_reject": ["REJECT"] * len(dev),
        "always_cannot_check": ["CANNOT_CHECK"] * len(dev),
    }
    control_dev_exact = {}
    for name, decisions in dev_arms.items():
        dble = [(d, g) for d, g in zip(decisions, dev_gold) if d != "CANNOT_CHECK"]
        control_dev_exact[name] = H.exact(*zip(*dble)) if dble else 0.0
    strongest = max(control_dev_exact, key=control_dev_exact.get)
    result["dev_fit"] = {
        "theta_structural": theta_struct, "theta_masked": theta_mask,
        "theta_semantic": theta_sem, "theta_lexical": theta_l,
        "control_dev_exact": control_dev_exact, "strongest_control": strongest,
        "dev_auc": {
            "witness_structural_v5": auc(dev_struct, dev_gold),
            "witness_masked_v5": auc(dev_mask, dev_gold),
            "control_semantic": auc(dev_sem, dev_gold),
        },
    }

    # --- CONFIRM ---------------------------------------------------------------
    print(f"encoding CONFIRM ({len(confirm)} pairs) ...", file=sys.stderr, flush=True)
    sconf = Scores(confirm)
    gold = [p.gold for p in confirm]
    raw = {
        "witness_structural_v5": [sconf.structural(p.query_text, p.candidate_text) for p in confirm],
        "witness_masked_v5": [sconf.masked_cos(p.query_text, p.candidate_text) for p in confirm],
        "control_semantic": [sconf.semantic(p.query_text, p.candidate_text) for p in confirm],
    }
    arms = {
        "witness_structural_v5": [threshold_decision(v, theta_struct) for v in raw["witness_structural_v5"]],
        "witness_masked_v5": [threshold_decision(v, theta_mask) for v in raw["witness_masked_v5"]],
        "control_semantic": [threshold_decision(v, theta_sem) for v in raw["control_semantic"]],
        "control_lexical": [H.lexical_decision(p.query_text, p.candidate_text, theta_l) for p in confirm],
        "control_band": [H.band_decision(p.band) for p in confirm],
        "always_accept": ["ACCEPT"] * len(confirm),
        "always_reject": ["REJECT"] * len(confirm),
        "always_cannot_check": ["CANNOT_CHECK"] * len(confirm),
    }
    control = arms[strongest]

    # --- battery: B3' FIRST ----------------------------------------------------
    shuffled = list(gold)
    random.Random(H.SEED_SHUFFLED_GOLD).shuffle(shuffled)
    battery: dict = {"B1_gold_arm_distinctness": "pass (arms receive texts/band only by signature)"}
    witnesses = ["witness_structural_v5", "witness_masked_v5"]

    battery["B3_prime_shuffled_gold"] = {}
    battery["B3_shuffled_gold_original"] = {}
    for w in witnesses:
        rep = b3_prime(control, arms[w], shuffled, mde=H.MDE)
        battery["B3_prime_shuffled_gold"][w] = {
            "advantage": rep.advantage, "n_scored": rep.n_scored, "fires": rep.fires,
            "abstention_witness": rep.abstention_witness,
            "abstention_control": rep.abstention_control,
            "predicted_confound_term": rep.predicted_confound,
            "g1_fails_as_required": not rep.fires,
        }
        orig = H.paired_advantage(control, arms[w], shuffled)
        battery["B3_shuffled_gold_original"][w] = {
            "advantage": orig, "fires": orig >= H.MDE, "governing": False,
        }
    if any(v["fires"] for v in battery["B3_prime_shuffled_gold"].values()):
        result["battery"] = battery
        return {**result, "terminal": "BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE",
                "reason": "B3_prime passed on at least one witness arm; stopped before confirmatory gates"}

    rng = random.Random(H.SEED_SCRAMBLE)
    scrambled_pairs = [(H._scramble_text(p.query_text, rng), H._scramble_text(p.candidate_text, rng))
                       for p in confirm]
    print("encoding scrambled CONFIRM (B2) ...", file=sys.stderr, flush=True)

    class _P:
        def __init__(self, q, c, band, gold, group):
            self.query_text, self.candidate_text = q, c
            self.band, self.gold, self.group = band, gold, group

    sc_pairs = [_P(q, c, p.band, p.gold, p.group)
                for (q, c), p in zip(scrambled_pairs, confirm)]
    ssc = Scores(sc_pairs)
    battery["B2_text_destruction"] = {}
    for w, fn, th in (("witness_structural_v5", "structural", theta_struct),
                      ("witness_masked_v5", "masked_cos", theta_mask)):
        sc_scores = [getattr(ssc, fn)(p.query_text, p.candidate_text) for p in sc_pairs]
        sc_dec = [threshold_decision(v, th) for v in sc_scores]
        changed = sum(1 for a, b in zip(sc_dec, arms[w]) if a != b) / len(confirm)
        sc_exact = H.exact(sc_dec, gold)
        battery["B2_text_destruction"][w] = {
            "decision_changed_fraction": changed, "scrambled_exact": sc_exact,
            "scrambled_auc": auc(sc_scores, gold),
        }

    battery["B4_trivial_floor"] = {}
    for t in ("always_accept", "always_reject", "always_cannot_check"):
        va = sum(1 for d, g in zip(arms[t], gold) if g == "ACCEPT" and d == "ACCEPT") / gold.count("ACCEPT")
        fa = sum(1 for d, g in zip(arms[t], gold) if g == "REJECT" and d == "ACCEPT") / gold.count("REJECT")
        battery["B4_trivial_floor"][t] = {"valid_accept": va, "invalid_false_accept": fa,
                                          "attains_G2": va >= 0.60 and fa <= 0.20}
    battery["B4_pass"] = not any(v["attains_G2"] for v in battery["B4_trivial_floor"].values())
    battery["B5_paired_variance"] = {
        w: statistics.pvariance([H.brier(d, g) for d, g in zip(arms[w], gold)])
        for w in witnesses + [strongest]
    }
    battery["probe_H_matched_pair"] = "N/A: no self-authored renderer; third-party surfaces"
    result["battery"] = battery

    # --- confirmatory gates ----------------------------------------------------
    gates: dict = {}
    for w in witnesses:
        adv = H.paired_advantage(control, arms[w], gold)
        lo, hi = H.bootstrap_ci(control, arms[w], gold)
        va = sum(1 for d, g in zip(arms[w], gold) if g == "ACCEPT" and d == "ACCEPT") / gold.count("ACCEPT")
        fa = sum(1 for d, g in zip(arms[w], gold) if g == "REJECT" and d == "ACCEPT") / gold.count("REJECT")
        cc = sum(1 for d in arms[w] if d == "CANNOT_CHECK") / len(confirm)
        gates[w] = {
            "G1_advantage": {"advantage": adv, "ci": [lo, hi], "mde": H.MDE,
                             "pass": adv >= H.MDE and lo > 0},
            "G2_joint": {"valid_accept": va, "invalid_false_accept": fa,
                         "pass": va >= 0.60 and fa <= 0.20},
            "G3_abstention": {"cannot_check_rate": cc, "dominant": cc > 0.50},
        }
    result["gates"] = gates

    qband = {p.group + p.query_text: p.band for p in confirm if p.gold == "ACCEPT"}
    result["diagnostic_auc"] = {
        "note": "threshold-free; enters no terminal",
        "overall": {k: auc(v, gold) for k, v in raw.items()},
    }
    for slice_name in ("near", "far"):
        idx = [i for i, p in enumerate(confirm) if qband.get(p.group + p.query_text) == slice_name]
        if idx:
            g = [gold[i] for i in idx]
            result["diagnostic_auc"][f"analogy_level_{slice_name}"] = {
                "n": len(idx), **{k: auc([v[i] for i in idx], g) for k, v in raw.items()}
            }
    result["arm_confirm_exact"] = {
        k: H.exact(*zip(*[(d, g) for d, g in zip(v, gold) if d != "CANNOT_CHECK"]))
        if any(d != "CANNOT_CHECK" for d in v) else 0.0
        for k, v in arms.items()
    }

    any_positive = any(
        gates[w]["G1_advantage"]["pass"] and gates[w]["G2_joint"]["pass"]
        and not gates[w]["G3_abstention"]["dominant"] for w in witnesses
    )
    if any_positive:
        terminal, scope = "POSITIVE_SCOPED__EXTERNAL_LABEL", None
    elif all(gates[w]["G1_advantage"]["ci"][1] < H.MDE or not gates[w]["G2_joint"]["pass"]
             or gates[w]["G3_abstention"]["dominant"] for w in witnesses):
        terminal, scope = "NEGATIVE__CAPABILITY_ABSENT", "MULTI_FAMILY"
    else:
        terminal, scope = "INDETERMINATE__CI_STRADDLES_MDE", None
    result["terminal"] = terminal
    if scope:
        result["terminal_scope"] = scope
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    result = run(args.csv, args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "RESULT.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"terminal": result.get("terminal"),
                      "scope": result.get("terminal_scope")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
