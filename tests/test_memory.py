import pytest

from rakl.memory import (
    MemoryAuthority,
    MemoryKind,
    MemoryRecord,
    ResearchMemory,
)


def rec(record_id, kind=MemoryKind.EXPERIMENT, *, parents=(), tags=()):
    return MemoryRecord(
        record_id=record_id,
        kind=kind,
        payload_hash=f"hash-{record_id}",
        context_id="ctx",
        authority=MemoryAuthority.RAW,
        semantic_tags=tuple(tags),
        parent_ids=tuple(parents),
    )


def test_supersession_hides_old_record_without_deleting_history():
    memory = ResearchMemory()
    memory.append(rec("old"))
    memory.append(rec("new", parents=("old",)))
    memory.supersede("old", "new", reason="repaired estimand", evidence_id="receipt")

    assert set(memory.records) == {"old", "new"}
    assert [record.record_id for record in memory.active_records()] == ["new"]
    assert memory.supersession_chain("old") == ["old", "new"]


def test_refuted_failure_remains_searchable_after_successor():
    memory = ResearchMemory()
    memory.append(rec("failure", MemoryKind.FAILURE, tags=("clock", "leakage")))
    memory.append(rec("successor", parents=("failure",)))
    memory.supersede("failure", "successor", reason="new versioned method")

    assert [r.record_id for r in memory.failure_records()] == ["failure"]
    assert memory.records_with_tag("clock")[0].record_id == "failure"


def test_parent_must_exist_before_child_append():
    memory = ResearchMemory()
    with pytest.raises(KeyError):
        memory.append(rec("child", parents=("missing",)))


def test_ambiguous_supersession_is_not_silently_selected():
    memory = ResearchMemory()
    for name in ("old", "new-a", "new-b"):
        memory.append(rec(name))
    memory.supersede("old", "new-a", reason="branch A")
    memory.supersede("old", "new-b", reason="branch B")
    with pytest.raises(ValueError, match="ambiguous supersession"):
        memory.supersession_chain("old")
