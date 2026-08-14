from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import SGDClassifier

URL = "https://huggingface.co/datasets/JoeyCheng/story_analogy/resolve/main/StoryAnalogy.csv"
SEED_BOOT = 20260814991
LABELS = ("REJECT", "CANNOT_CHECK", "ACCEPT")
L2I = {v: i for i, v in enumerate(LABELS)}


def norm_text(s: str) -> str:
    return re.sub(r"[ \t\r\n]+", " ", str(s).strip())


def story_digest(s: str) -> str:
    return hashlib.sha256(norm_text(s).encode("utf-8")).hexdigest()


def pair_surface(a: str, b: str) -> str:
    a, b = norm_text(a), norm_text(b)
    if story_digest(a) > story_digest(b):
        a, b = b, a
    return f"STORY_A\n{a}\nSTORY_B\n{b}"


def lexical_score(a: str, b: str) -> float:
    tok = lambda s: set(re.findall(r"[a-z0-9]+", norm_text(s).lower()))
    A, B = tok(a), tok(b)
    return len(A & B) / max(1, len(A | B))


class UF:
    def __init__(self):
        self.p = {}
    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            if a > b:
                a, b = b, a
            self.p[b] = a


def gold_label(entity: float, relation: float) -> str:
    if entity <= 1.0 and relation >= 2.0:
        return "ACCEPT"
    if entity >= 2.0 or relation <= 1.0:
        return "REJECT"
    return "CANNOT_CHECK"


def load_text_rows(raw: bytes):
    text = io.StringIO(raw.decode("utf-8-sig"))
    rdr = csv.DictReader(text)
    required = {"s1", "s2", "entity", "relation", "domain"}
    if not required.issubset(set(rdr.fieldnames or [])):
        raise RuntimeError("SCHEMA_INCOMPATIBLE_CANNOT_CHECK:" + repr(rdr.fieldnames))
    rows = []
    for idx, row in enumerate(rdr):
        rows.append({"idx": idx, "s1": row["s1"], "s2": row["s2"], "domain": row["domain"]})
    return rows


def load_labels(raw: bytes, wanted: set[int]):
    text = io.StringIO(raw.decode("utf-8-sig"))
    rdr = csv.DictReader(text)
    out = {}
    for idx, row in enumerate(rdr):
        if idx in wanted:
            ent, rel = float(row["entity"]), float(row["relation"])
            out[idx] = {"entity": ent, "relation": rel, "gold": gold_label(ent, rel)}
    if set(out) != set(wanted):
        raise RuntimeError("label_index_mismatch")
    return out


def partitions(rows):
    uf = UF()
    active = [r for r in rows if r["idx"] >= 100]
    for r in active:
        uf.union(story_digest(r["s1"]), story_digest(r["s2"]))
    members = defaultdict(list)
    for r in active:
        roots = [uf.find(story_digest(r["s1"])), uf.find(story_digest(r["s2"]))]
        root = min(roots)
        members[root].append(r["idx"])
    assign = {}
    component_meta = []
    for root, idxs in members.items():
        # Root identity is the lexicographically smallest story digest in component.
        digests = []
        for idx in idxs:
            r = rows[idx]
            digests += [story_digest(r["s1"]), story_digest(r["s2"])]
        key = min(digests)
        bucket = int(key[:8], 16) % 100
        part = "DEV" if bucket <= 59 else "CALIBRATION" if bucket <= 79 else "CONFIRMATORY"
        for idx in idxs:
            assign[idx] = part
        component_meta.append((key, part, len(idxs)))
    return assign, component_meta


def metrics(y, pred):
    y = np.asarray(y, dtype=int); pred = np.asarray(pred, dtype=int)
    n = len(y)
    acc = float(np.mean(y == pred)) if n else 0.0
    acc_mask, rej_mask, cc_mask = y == L2I["ACCEPT"], y == L2I["REJECT"], y == L2I["CANNOT_CHECK"]
    cc_pred = pred == L2I["CANNOT_CHECK"]
    return {
        "n": n,
        "exact3": acc,
        "valid_accept": float(np.mean(pred[acc_mask] == L2I["ACCEPT"])) if np.any(acc_mask) else 0.0,
        "invalid_false_accept": float(np.mean(pred[rej_mask] == L2I["ACCEPT"])) if np.any(rej_mask) else 0.0,
        "cannot_check_recall": float(np.mean(pred[cc_mask] == L2I["CANNOT_CHECK"])) if np.any(cc_mask) else 0.0,
        "cannot_check_precision": float(np.mean(y[cc_pred] == L2I["CANNOT_CHECK"])) if np.any(cc_pred) else 0.0,
        "gold_counts": dict(Counter(LABELS[i] for i in y)),
        "pred_counts": dict(Counter(LABELS[i] for i in pred)),
    }


def choose_lex(cal_scores, y):
    best = None
    vals = [i / 20 for i in range(21)]
    for lo in vals:
        for hi in vals:
            if not lo < hi:
                continue
            pred = np.where(cal_scores <= lo, L2I["REJECT"], np.where(cal_scores >= hi, L2I["ACCEPT"], L2I["CANNOT_CHECK"]))
            m = metrics(y, pred)
            key = (m["exact3"], -m["invalid_false_accept"], m["valid_accept"], -lo, -hi)
            if best is None or key > best[0]:
                best = (key, lo, hi, pred, m)
    return best[1:]


def direct_predict(proba, classes, tau):
    classes = np.asarray(classes, dtype=int)
    arg = np.argmax(proba, axis=1)
    cls = classes[arg]
    conf = proba[np.arange(len(proba)), arg]
    return np.where((cls == L2I["CANNOT_CHECK"]) | (conf >= tau), cls, L2I["CANNOT_CHECK"])


def choose_direct(proba, classes, y):
    best = None
    for tau in [0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90]:
        pred = direct_predict(proba, classes, tau)
        m = metrics(y, pred)
        key = (m["exact3"], -m["invalid_false_accept"], m["valid_accept"], -tau)
        if best is None or key > best[0]:
            best = (key, tau, pred, m)
    return best[1:]


def factor_predict(p_rel, p_ent, tr, te):
    acc = (p_rel >= tr) & (p_ent >= te)
    rej = (p_rel <= 1-tr) | (p_ent <= 1-te)
    return np.where(acc, L2I["ACCEPT"], np.where(rej, L2I["REJECT"], L2I["CANNOT_CHECK"]))


def choose_factor(p_rel, p_ent, y):
    best = None
    grid = [0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90]
    for tr in grid:
        for te in grid:
            pred = factor_predict(p_rel, p_ent, tr, te)
            m = metrics(y, pred)
            if m["invalid_false_accept"] > 0.15 + 1e-15 or m["valid_accept"] < 0.50 - 1e-15:
                continue
            key = (m["exact3"], -m["invalid_false_accept"], m["valid_accept"], -tr, -te)
            if best is None or key > best[0]:
                best = (key, tr, te, pred, m)
    return None if best is None else best[1:]


def build_vectorizer():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1,2), min_df=2, sublinear_tf=True, max_features=120000, lowercase=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3,5), min_df=2, sublinear_tf=True, max_features=120000, lowercase=True)),
    ])


def clf(seed):
    return SGDClassifier(loss="log_loss", alpha=1e-5, max_iter=2000, tol=1e-4, random_state=seed, class_weight="balanced")


def bootstrap_diff(a_ok, b_ok, reps=10000, seed=SEED_BOOT):
    rng = np.random.default_rng(seed)
    diff = a_ok.astype(float) - b_ok.astype(float)
    n = len(diff)
    vals = np.empty(reps, dtype=float)
    for i in range(reps):
        vals[i] = float(np.mean(diff[rng.integers(0, n, size=n)]))
    return float(np.mean(diff)), [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(URL, timeout=120) as r:
        raw = r.read()
    source_sha = hashlib.sha256(raw).hexdigest()
    rows = load_text_rows(raw)
    assign, components = partitions(rows)
    bypart = {p: sorted(i for i,v in assign.items() if v == p) for p in ("DEV","CALIBRATION","CONFIRMATORY")}
    if set(range(min(100, len(rows)))) & set(assign):
        raise RuntimeError("preview_quarantine_failed")

    # Text-only preprocessing and split construction are allowed before label access.
    surfaces = {r["idx"]: pair_surface(r["s1"], r["s2"]) for r in rows if r["idx"] in assign}
    stories = {r["idx"]: (norm_text(r["s1"]), norm_text(r["s2"])) for r in rows if r["idx"] in assign}
    domains = {r["idx"]: r["domain"] for r in rows if r["idx"] in assign}

    devcal = set(bypart["DEV"] + bypart["CALIBRATION"])
    labels_dc = load_labels(raw, devcal)
    ydev = np.array([L2I[labels_dc[i]["gold"]] for i in bypart["DEV"]], dtype=int)
    ycal = np.array([L2I[labels_dc[i]["gold"]] for i in bypart["CALIBRATION"]], dtype=int)
    if len(set(ydev)) < 3 or len(set(ycal)) < 3:
        receipt = {"terminal":"SCHEMA_INCOMPATIBLE_CANNOT_CHECK","reason":"development/calibration lacks all three gold classes","source_sha256":source_sha}
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        return 4

    Xdev_text = [surfaces[i] for i in bypart["DEV"]]
    Xcal_text = [surfaces[i] for i in bypart["CALIBRATION"]]
    vec = build_vectorizer()
    Xdev = vec.fit_transform(Xdev_text)
    Xcal = vec.transform(Xcal_text)

    # P0 lexical parent.
    lex_dev = np.array([lexical_score(*stories[i]) for i in bypart["DEV"]])
    lex_cal = np.array([lexical_score(*stories[i]) for i in bypart["CALIBRATION"]])
    lex_lo, lex_hi, pred_lex_cal, m_lex_cal = choose_lex(lex_cal, ycal)

    # P1 direct three-way parent.
    direct = clf(20260814); direct.fit(Xdev, ydev)
    pdir_cal = direct.predict_proba(Xcal)
    direct_tau, pred_dir_cal, m_dir_cal = choose_direct(pdir_cal, direct.classes_, ycal)

    # Factorised candidate heads.
    rel_dev = np.array([1 if labels_dc[i]["relation"] >= 2.0 else 0 for i in bypart["DEV"]], dtype=int)
    ent_dev = np.array([1 if labels_dc[i]["entity"] <= 1.0 else 0 for i in bypart["DEV"]], dtype=int)
    rel = clf(20260814); ent = clf(20260815)
    rel.fit(Xdev, rel_dev); ent.fit(Xdev, ent_dev)
    prel_cal = rel.predict_proba(Xcal)[:, list(rel.classes_).index(1)]
    pent_cal = ent.predict_proba(Xcal)[:, list(ent.classes_).index(1)]
    factor = choose_factor(prel_cal, pent_cal, ycal)
    if factor is None:
        receipt = {
            "schema_version":"paper2-storyanalogy-factorized-result-v1",
            "terminal":"DEVELOPMENT_NEGATIVE_NO_SAFE_THRESHOLD",
            "source_sha256":source_sha,"n_rows":len(rows),"partitions":{k:len(v) for k,v in bypart.items()},
            "parent_calibration":{"P0_LEXICAL":m_lex_cal,"P1_DIRECT_TEXT":m_dir_cal},
            "grants_scientific_authority":False,
        }
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        return 1
    tr, te, pred_fac_cal, m_fac_cal = factor

    if m_lex_cal["exact3"] >= m_dir_cal["exact3"] - 1e-15:
        parent_name, parent_cal_pred, parent_cal_m = "P0_LEXICAL", pred_lex_cal, m_lex_cal
    else:
        parent_name, parent_cal_pred, parent_cal_m = "P1_DIRECT_TEXT", pred_dir_cal, m_dir_cal

    # Falsifiability battery on calibration only.
    rng = np.random.default_rng(2026081401)
    s1 = np.array([stories[i][0] for i in bypart["CALIBRATION"]], dtype=object)
    s2 = np.array([stories[i][1] for i in bypart["CALIBRATION"]], dtype=object)
    dtext = [pair_surface(a,b) for a,b in zip(s1[rng.permutation(len(s1))], s2[rng.permutation(len(s2))])]
    Xdestroy = vec.transform(dtext)
    p_rel_d = rel.predict_proba(Xdestroy)[:, list(rel.classes_).index(1)]
    p_ent_d = ent.predict_proba(Xdestroy)[:, list(ent.classes_).index(1)]
    pred_destroy = factor_predict(p_rel_d,p_ent_d,tr,te)
    text_drop = m_fac_cal["exact3"] - metrics(ycal,pred_destroy)["exact3"]

    rrng=np.random.default_rng(2026081402); pred_rshuffle=factor_predict(prel_cal[rrng.permutation(len(prel_cal))],pent_cal,tr,te)
    erng=np.random.default_rng(2026081403); pred_eshuffle=factor_predict(prel_cal,pent_cal[erng.permutation(len(pent_cal))],tr,te)
    pred_swap=factor_predict(pent_cal,prel_cal,tr,te)
    rel_change=float(np.mean(pred_rshuffle!=pred_fac_cal)); ent_change=float(np.mean(pred_eshuffle!=pred_fac_cal)); swap_change=float(np.mean(pred_swap!=pred_fac_cal))
    grng=np.random.default_rng(2026081404); yshuf=ycal[grng.permutation(len(ycal))]
    shuffled_adv=float(np.mean(pred_fac_cal==yshuf)-np.mean(parent_cal_pred==yshuf))
    constants={name:metrics(ycal,np.full(len(ycal),L2I[name],dtype=int)) for name in LABELS}
    trivial_pass=not any(m["valid_accept"]>=0.65 and m["invalid_false_accept"]<=0.15 for m in constants.values())
    probes={
        "TEXT_DESTRUCTION":{"drop":text_drop,"pass":text_drop>=0.10-1e-15},
        "RELATION_HEAD_SHUFFLE":{"changed_fraction":rel_change,"pass":rel_change>=0.05-1e-15},
        "ENTITY_HEAD_SHUFFLE":{"changed_fraction":ent_change,"pass":ent_change>=0.05-1e-15},
        "HEAD_SWAP":{"changed_fraction":swap_change,"pass":swap_change>=0.05-1e-15},
        "GOLD_SHUFFLE":{"advantage":shuffled_adv,"pass":shuffled_adv<0.02},
        "TRIVIAL_CONTROLS":{"metrics":constants,"pass":trivial_pass},
    }
    if not all(x["pass"] for x in probes.values()):
        receipt={"schema_version":"paper2-storyanalogy-factorized-result-v1","terminal":"INSTRUMENT_NOT_FALSIFIABLE","source_sha256":source_sha,"n_rows":len(rows),"partitions":{k:len(v) for k,v in bypart.items()},"frozen_candidate":{"tau_rel":tr,"tau_ent":te},"strongest_parent":parent_name,"calibration":{"candidate":m_fac_cal,"parent":parent_cal_m},"falsifiability":probes,"grants_scientific_authority":False}
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
        return 2

    # Only now are confirmatory labels parsed/used.
    conf_set=set(bypart["CONFIRMATORY"])
    labels_c=load_labels(raw,conf_set)
    yconf=np.array([L2I[labels_c[i]["gold"]] for i in bypart["CONFIRMATORY"]],dtype=int)
    Xconf=vec.transform([surfaces[i] for i in bypart["CONFIRMATORY"]])
    prel=rel.predict_proba(Xconf)[:,list(rel.classes_).index(1)]; pent=ent.predict_proba(Xconf)[:,list(ent.classes_).index(1)]
    pred_fac=factor_predict(prel,pent,tr,te)
    if parent_name=="P0_LEXICAL":
        sc=np.array([lexical_score(*stories[i]) for i in bypart["CONFIRMATORY"]])
        pred_parent=np.where(sc<=lex_lo,L2I["REJECT"],np.where(sc>=lex_hi,L2I["ACCEPT"],L2I["CANNOT_CHECK"]))
    else:
        pred_parent=direct_predict(direct.predict_proba(Xconf),direct.classes_,direct_tau)
    m_fac=metrics(yconf,pred_fac); m_parent=metrics(yconf,pred_parent)
    point,ci=bootstrap_diff(pred_fac==yconf,pred_parent==yconf)
    dom={}
    for d in sorted(set(domains[i] for i in bypart["CONFIRMATORY"])):
        pos=np.array([j for j,i in enumerate(bypart["CONFIRMATORY"]) if domains[i]==d],dtype=int)
        dom[d]={"candidate":metrics(yconf[pos],pred_fac[pos]),"parent":metrics(yconf[pos],pred_parent[pos])}

    gate={
        "minimum_confirmatory_n":len(yconf)>=1000,
        "all_three_gold_classes_present":len(set(yconf))==3,
        "candidate_minus_parent_point_min":point>=0.02-1e-15,
        "candidate_minus_parent_ci_lower_gt":ci[0]>0,
        "valid_accept_min":m_fac["valid_accept"]>=0.65-1e-15,
        "invalid_false_accept_max":m_fac["invalid_false_accept"]<=0.15+1e-15,
        "cannot_check_recall_min":m_fac["cannot_check_recall"]>=0.40-1e-15,
        "falsifiability":all(x["pass"] for x in probes.values()),
    }
    if all(gate.values()): terminal="PROMOTE_CONDITIONALLY_EXTERNAL_HUMAN_STRUCTURAL_ANALOGY_FACTORISATION_V1"
    elif m_fac["invalid_false_accept"]>0.15: terminal="NEGATIVE_FACTORISATION_UNSAFE_FALSE_ACCEPT"
    elif m_fac["valid_accept"]<0.65: terminal="NEGATIVE_FACTORISATION_OVERREFUSES_VALID_ANALOGIES"
    else: terminal="NEGATIVE_FACTORISATION_NO_RESIDUAL_OVER_STRONGEST_TEXT_PARENT"
    receipt={
      "schema_version":"paper2-storyanalogy-factorized-result-v1","terminal":terminal,"source_url":URL,"source_sha256":source_sha,"n_rows":len(rows),"quarantined_rows":[0,99],
      "partitions":{k:len(v) for k,v in bypart.items()},"components":{"n":len(components),"max_rows":max(x[2] for x in components)},
      "development":{"gold_counts":dict(Counter(LABELS[i] for i in ydev))},
      "calibration":{"P0_LEXICAL":{"lo":lex_lo,"hi":lex_hi,"metrics":m_lex_cal},"P1_DIRECT_TEXT":{"tau":direct_tau,"metrics":m_dir_cal},"E_FACTORISED_STRUCTURAL":{"tau_rel":tr,"tau_ent":te,"metrics":m_fac_cal},"strongest_parent":parent_name},
      "falsifiability":probes,
      "confirmatory":{"candidate":m_fac,"parent_name":parent_name,"parent":m_parent,"paired_exact3_advantage":point,"bootstrap_95ci":ci,"bootstrap_repetitions":10000,"domain_breakdown":dom},
      "promotion_gate":gate,
      "claim_boundary":"External-human StoryAnalogy discrimination only; no source-span witness, universal transfer, end-to-end ORION utility or scientific authority.",
      "grants_scientific_authority":False
    }
    (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    return 0 if terminal.startswith("PROMOTE_") else 1

if __name__ == "__main__":
    raise SystemExit(main())
