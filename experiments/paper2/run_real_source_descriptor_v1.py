from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "research" / "paper2_real_source_descriptor_v1" / "PROTOCOL.json"
EXPECTED_KEYS = {
    "family",
    "qoi",
    "boundary_markers",
    "mapping_status",
    "application_preconditions_status",
    "source_span_sha256",
}

SYSTEM = """You are a fail-closed structural source descriptor extractor.
Extract only what is explicit in the supplied source span. Never invent a source-to-target mapping or application precondition. If those are absent, emit UNKNOWN exactly. Return one JSON object and no prose."""

INSTRUCTION = """Return exactly these keys:
family: one of flow|logic|units|state|sched|stat
qoi: concise registered descriptor token
boundary_markers: JSON array of explicit structural/boundary markers
mapping_status: UNKNOWN
application_preconditions_status: UNKNOWN
source_span_sha256: copy the supplied exact digest
Do not use the paper title or source identifier as a substitute for reading the span."""


def _blocked(outdir: Path, terminal: str, reason: str) -> int:
    receipt = {
        "schema_version": "paper2-real-source-descriptor-result-v1",
        "terminal": terminal,
        "reason": reason,
        "grants_scientific_authority": False,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 2


def _check_capability(path: Path, protocol: dict) -> dict:
    receipt = json.loads(path.read_text())
    required = protocol["execution_subject"]
    if receipt.get("terminal") != required["requires_terminal"]:
        raise ValueError("capability_terminal_not_authorized")
    model = receipt.get("model", {})
    if model.get("model_id") != required["required_model_id"]:
        raise ValueError("capability_model_id_mismatch")
    if model.get("revision") != required["required_model_revision"]:
        raise ValueError("capability_model_revision_mismatch")
    return receipt


def _parse(raw: str) -> dict | None:
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        return None
    if value.get("family") not in {"flow", "logic", "units", "state", "sched", "stat"}:
        return None
    if not isinstance(value.get("qoi"), str) or not value["qoi"].strip():
        return None
    if not isinstance(value.get("boundary_markers"), list) or any(
        not isinstance(item, str) for item in value["boundary_markers"]
    ):
        return None
    if value.get("mapping_status") != "UNKNOWN":
        return None
    if value.get("application_preconditions_status") != "UNKNOWN":
        return None
    if not isinstance(value.get("source_span_sha256"), str):
        return None
    return value


def run(outdir: Path, *, capability_receipt: Path | None, model_path: str | None, dry_run: bool) -> int:
    protocol = json.loads(PROTOCOL.read_text())
    for source in protocol["sources"]:
        digest = hashlib.sha256(source["span"].encode()).hexdigest()
        if digest != source["span_sha256"]:
            return _blocked(outdir, "SOURCE_PACKET_INVALID", f"source_span_hash_mismatch:{source['source_ref']}")
    if dry_run:
        print(json.dumps({"dry_run": True, "n_sources": len(protocol["sources"]), "capability_required": protocol["execution_subject"]}, indent=2))
        return 0
    if capability_receipt is None or not capability_receipt.exists():
        return _blocked(outdir, "BLOCKED_CAPABILITY", "CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3_missing")
    try:
        capability = _check_capability(capability_receipt, protocol)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        return _blocked(outdir, "BLOCKED_CAPABILITY", str(exc))
    if not model_path:
        return _blocked(outdir, "RESOURCE_BLOCKED", "model_path_missing")

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        return _blocked(outdir, "RESOURCE_BLOCKED", f"runtime_import_failed:{type(exc).__name__}:{exc}")
    if not torch.cuda.is_available():
        return _blocked(outdir, "RESOURCE_BLOCKED", "cuda_unavailable")

    model_root = Path(model_path)
    if not (model_root / "config.json").exists():
        matches = list(model_root.glob("**/config.json"))
        if len(matches) != 1:
            return _blocked(outdir, "RESOURCE_BLOCKED", f"model_config_resolution_count:{len(matches)}")
        model_root = matches[0].parent

    tokenizer = AutoTokenizer.from_pretrained(str(model_root), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(model_root), local_files_only=True, torch_dtype=torch.bfloat16
    ).to("cuda").eval()

    outdir.mkdir(parents=True, exist_ok=True)
    raw_path = outdir / "RAW_OUTPUTS.jsonl"
    raw_path.unlink(missing_ok=True)
    rows = []
    start = time.perf_counter()
    for source in protocol["sources"]:
        user = (
            INSTRUCTION
            + "\n\nSource span SHA-256: "
            + source["span_sha256"]
            + "\nSource span:\n"
            + source["span"]
        )
        if getattr(tokenizer, "chat_template", None):
            input_ids = tokenizer.apply_chat_template(
                [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                tokenize=True, add_generation_prompt=True, return_tensors="pt"
            ).to("cuda")
        else:
            input_ids = tokenizer(SYSTEM + "\n\n" + user, return_tensors="pt").input_ids.to("cuda")
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_new_tokens=192,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        raw = tokenizer.decode(output[0, input_ids.shape[1]:], skip_special_tokens=True)
        parsed = _parse(raw)
        gold = source["gold"]
        exact = parsed is not None and (
            parsed["family"] == source["family"]
            and parsed["qoi"] == gold["qoi"]
            and set(parsed["boundary_markers"]) == set(gold["boundary_markers"])
            and parsed["mapping_status"] == "UNKNOWN"
            and parsed["application_preconditions_status"] == "UNKNOWN"
            and parsed["source_span_sha256"] == source["span_sha256"]
        )
        row = {
            "source_ref": source["source_ref"],
            "raw": raw,
            "parsed": parsed,
            "exact": exact,
        }
        rows.append(row)
        with raw_path.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    exact = sum(row["exact"] for row in rows) / len(rows)
    receipt = {
        "schema_version": "paper2-real-source-descriptor-result-v1",
        "terminal": "DEVELOPMENT_DESCRIPTOR_SCHEMA_WORKS" if exact == 1.0 else "RSHEA_SUCCESSOR_REQUIRED",
        "n_sources": len(rows),
        "exact_descriptor_rate": exact,
        "capability_subject": {
            "terminal": capability["terminal"],
            "model": capability["model"],
        },
        "development_only": True,
        "authorizes_natural_domain_claim": False,
        "next_if_green": protocol["fresh_successor_if_schema_works"],
        "wall_seconds": time.perf_counter() - start,
        "grants_scientific_authority": False,
    }
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if exact == 1.0 else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--capability-receipt", type=Path)
    ap.add_argument("--model-path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    raise SystemExit(run(args.outdir, capability_receipt=args.capability_receipt, model_path=args.model_path, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
