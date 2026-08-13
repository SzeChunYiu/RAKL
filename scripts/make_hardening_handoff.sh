#!/bin/bash
# Package the current hardening state as an AI-session handoff zip.
# Contents: patch vs the declared base, both hostile audits, the open-gaps register,
# verification commands, and checksums — same shape as prior Orion handoff bundles.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BASE="${1:-origin/main}"
STAMP=$(date -u +%Y%m%d)
OUT_DIR="/tmp/orion_hardening_handoff_$STAMP"
BUNDLE="$OUT_DIR/handoff_bundle"
rm -rf "$OUT_DIR"; mkdir -p "$BUNDLE/generated"

HEAD_SHA=$(git rev-parse HEAD)
BASE_SHA=$(git rev-parse "$BASE")

git diff "$BASE_SHA"..HEAD > "$BUNDLE/orion-hardening-$STAMP.diff"
git diff "$BASE_SHA"..HEAD --stat > "$BUNDLE/DIFF_STAT.txt"
git log "$BASE_SHA"..HEAD --oneline > "$BUNDLE/COMMITS.txt"

cp research/unified_problem_solving_v1/HOSTILE_MATH_AUDIT.md "$BUNDLE/" 2>/dev/null || true
cp research/unified_problem_solving_v1/HOSTILE_ENGINEERING_AUDIT.md "$BUNDLE/" 2>/dev/null || true
cp research/unified_problem_solving_v1/OPEN_GAPS_REGISTER.md "$BUNDLE/" 2>/dev/null || true
cp research/unified_problem_solving_v1/results/CLOSURE_LEDGER.json "$BUNDLE/generated/" 2>/dev/null || true

cat > "$BUNDLE/HANDOFF_SUBJECT.txt" <<EOF
repository=SzeChunYiu/RAKL
base_sha=$BASE_SHA
head_sha=$HEAD_SHA
date=$STAMP
EOF

cat > "$BUNDLE/HANDOFF_HARDENING.md" <<'EOF'
# Orion recursive-hardening handoff

Apply `orion-hardening-<date>.diff` onto `base_sha` (3-way). Then work the
OPEN_GAPS_REGISTER.md top-to-bottom until empty. Rules:
1. Every fix gets a regression test citing the finding ID (tests/test_audit_regressions.py).
2. Never weaken a gate to make a test pass; grants_scientific_authority stays false everywhere.
3. After each batch: run the verification block below; then re-run a fresh hostile audit
   (math + engineering lenses, as in the audit files) on the changed surfaces — recursive
   hardening means new fixes are themselves audited.
4. Frozen provenance is immutable: research/ receipts, RAKL_* identifiers, paper2/3 trees.

## Verification block
  pip install -e . pytest && PYTHONHASHSEED=0 python -m pytest -q \
    tests/test_unified_solver_framework.py tests/test_unified_solver_registry.py \
    tests/test_vtg_closure_contracts.py tests/test_formal_laws.py \
    tests/test_audit_regressions.py tests/test_exposure_executor.py tests/test_metrics_kpi.py
  PYTHONPATH=src python scripts/audit_unified_framework.py       # expect PASS, authority=false
  PYTHONPATH=src python scripts/closure_ledger.py                # expect CLOSED_AT_CUTOFF
  PYTHONPATH=src python research/unified_problem_solving_v1/run_known_world_stress.py
EOF

( cd "$OUT_DIR" && find handoff_bundle -type f -exec sha256sum {} \; > handoff_bundle/CHECKSUMS.sha256 )
ZIP="/tmp/orion_hardening_handoff_${STAMP}_${HEAD_SHA:0:12}.zip"
( cd "$OUT_DIR" && zip -qr "$ZIP" handoff_bundle )
echo "WROTE=$ZIP"
