"""Known-answer validation of the external-corpus instrument BEFORE real data.

Validates the checker first (planted worlds), per the programme's rule that a
new instrument must succeed, fail and fail-closed in controlled worlds before
its native run is trusted. The planted-pass world is constructed so that the
witness arm separates structure the lexical control cannot (identical token
sets, different relation order), with a hard stratum keeping per-item loss
variance nonzero; the shuffled-gold negative control is exercised inside the
runner's own battery (B3).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from rakl.narrative_reducer import reduce_narrative
from rakl.reduction_validation import (
    PARITY_CALIBRATION_SOURCE,
    AdmissionVerdict,
    ReducerProfile,
    admit_reducer,
)
from scripts.paper2_external_corpus_confirmatory import (
    bind_mapping,
    build_pairs_m3,
    run,
)


def test_reducer_surfaces_parity_obstruction() -> None:
    reduced = reduce_narrative(PARITY_CALIBRATION_SOURCE)
    assert reduced.structure.obstructions, "parity source must yield an obstruction"


def test_reducer_reads_text() -> None:
    a = reduce_narrative("The engineer routes water through the northern channel gates.")
    b = reduce_narrative("gg ee tt hh nn rr aa uu oo ii ss dd ll mm pp qq ww xx yy zz")
    assert a.roles != b.roles


def test_reducer_is_admitted_with_arn_label_author() -> None:
    profile = ReducerProfile(
        reducer_id="narrative_reducer_v1",
        author="RAKL programme (same-context; LLM-assisted)",
        external_label_author="Sourati, Ilievski, Sommerauer, Jiang (ARN, TACL 2024)",
    )
    sources = [
        "The farmer stored grain before the flood season arrived and the barn "
        "held because the beams carried the weight into the foundation.",
        "A courier chooses the mountain path although the river road looks "
        "shorter, because the bridge cannot carry the loaded cart.",
    ]
    report = admit_reducer(profile, reduce_narrative, sources)
    assert report.verdict is AdmissionVerdict.ADMITTED


def test_m3_binding_and_pair_construction() -> None:
    header = [
        "id", "proverb", "query_narrative", "first_choice", "second_choice",
        "distractor_similarity", "analogy_level", "correct_answer",
    ]
    mapping = bind_mapping(header)
    assert mapping is not None and mapping["mode"] == "M3"
    rows = [
        {"id": "1", "proverb": "p1", "query_narrative": "q one",
         "first_choice": "the analogy", "second_choice": "the decoy",
         "distractor_similarity": "high", "analogy_level": "far",
         "correct_answer": "1"},
        {"id": "2", "proverb": "p2", "query_narrative": "q two",
         "first_choice": "the decoy", "second_choice": "the analogy",
         "distractor_similarity": "low", "analogy_level": "near",
         "correct_answer": "2"},
        {"id": "3", "proverb": "p3", "query_narrative": "q three",
         "first_choice": "a", "second_choice": "b",
         "distractor_similarity": "high", "analogy_level": "far",
         "correct_answer": "weird"},
    ]
    pairs, skipped = build_pairs_m3(rows, mapping)
    assert skipped == 1
    assert [(p.gold, p.candidate_text, p.band) for p in pairs] == [
        ("ACCEPT", "the analogy", "far"),
        ("REJECT", "the decoy", "near"),
        ("ACCEPT", "the analogy", "near"),
        ("REJECT", "the decoy", "far"),
    ]
    assert {p.group for p in pairs} == {"p1", "p2"}


def _planted_row(index: int, hard: bool) -> dict[str, str]:
    a, b, c = f"alpha{index}", f"beta{index}", f"gamma{index}"
    if hard:
        # One short clause: too little structure -> witness must abstain.
        query = f"The {a} meets the {b}."
        analogy = f"The {a} meets the {b}."
        distractor = f"The {b} meets the {a}."
    else:
        query = (
            f"The {a} pushes the {b} forward. Then the {b} pushes the {c} forward. "
            f"So the {a} moves the whole {c} chain."
        )
        analogy = query  # identical structure and tokens
        distractor = (
            # same token multiset, relation order broken
            f"The {b} pushes the {a} forward. Then the {c} pushes the {b} forward. "
            f"So the {c} moves the whole {a} chain."
        )
    return {
        "query narrative": query,
        "far analogy": analogy,
        "near distractor": distractor,
        "query_id": f"g{index}",
    }


def test_planted_world_end_to_end(tmp_path: Path) -> None:
    csv_path = tmp_path / "planted.csv"
    rows = [_planted_row(i, hard=(i % 7 == 0)) for i in range(60)]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    mapping = bind_mapping(list(rows[0]))
    assert mapping is not None and mapping["mode"] == "M1"

    result = run(csv_path, tmp_path / "out")
    (tmp_path / "out" / "RESULT.json").write_text(json.dumps(result, indent=2))

    assert result["admission"]["verdict"] == "ADMITTED"
    battery = result["battery"]
    assert battery["B2_text_destruction"]["pass"], battery["B2_text_destruction"]
    assert battery["B3_shuffled_gold"]["g1_fails_as_required"], battery["B3_shuffled_gold"]
    assert battery["B4_pass"]
    assert battery["B5_paired_variance"]["pass"], battery["B5_paired_variance"]
    # The planted world is built for the witness to win: structure separates,
    # lexicon cannot (identical token sets on the easy stratum).
    assert result["terminal"] == "POSITIVE_SCOPED__EXTERNAL_LABEL", result["gates"]
