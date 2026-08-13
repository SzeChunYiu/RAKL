# Hostile engineering audit — Orion unified problem-solving framework

- **Audit subject**: commit `1bdf91018a05faa06f94a72dfc6d040986154db6` (working tree clean at audit time).
- **Auditor stance**: hostile senior AI engineers + reproducibility reviewers evaluating adoption. Engineering gaps with real consequences only; no style findings.
- **Verification environment**: `/tmp/orion-venv/bin/python` (CPython 3.11.14), `PYTHONPATH=src`, Linux x86_64. Every finding marked VERIFIED was reproduced by execution against the audited tree; commands are quoted verbatim.
- **Concurrency caveat**: the tree was actively modified by a concurrent session during this audit (all eight `src/rakl` mechanic files were rewritten mid-audit, commits `f422f728`/`f7495741`/`75f3bce4`/`1bdf9101`). Every finding below was re-verified against the final state at HEAD `1bdf9101`. File digests at audit time:
  - `src/rakl/operational_map.py` sha256 `7318229c…35833`
  - `src/rakl/path_equivalence.py` sha256 `58554bbd…adf0c7`
  - `src/rakl/path_cost.py` sha256 `4c6c7167…37479f`
  - `experiments/training_ladder/generator_v2.py` sha256 `79e12702…6057f5`
  - `research/unified_problem_solving_v1/path_quotient_experiment.py` sha256 `9dd32386…36ba8432`
- **Authority note**: this document grants no scientific authority; it is an engineering defect ledger. Do not treat it as passing or failing any RAKL evidence gate.

**Gap count by severity**: BREAKS_REPRODUCIBILITY 3 · BREAKS_ADOPTER 6 · PERF_CLIFF 2 · CI_DRIFT 3 · MINOR 4 — 18 findings total.

---

## BREAKS_REPRODUCIBILITY

### R1. `generator_v2.generate` seeds its RNG with the PYTHONHASHSEED-salted tuple hash — every process gets different training/probe data under identical arguments

- **Where**: `experiments/training_ladder/generator_v2.py:144`
  ```python
  rng = random.Random((seed, family, regime, style, tag).__hash__() & 0xFFFFFFFF)
  ```
- **What breaks, for whom**: `tuple.__hash__` over `str` elements inherits CPython's per-process SipHash salt (randomized unless `PYTHONHASHSEED` is fixed *before interpreter start*). Two runs of `phase1_v2.py` with the same `--seed`, same packet, same flags train on **different case content**. Anyone attempting to replicate a Phase-1 v2 run — including the paper authors — cannot. The manifest records `"seed": 461` as if it pinned the data; it does not.
- **Aggravator**: case ids are index-based (`balv2-base-0-train`), so the *ids are identical across runs while the content differs*. Any artifact keyed by case_id (outcome rows, leakage checks, cross-run comparisons) silently refers to different problems in different runs.
- **VERIFIED** (three separate interpreter processes, identical call):
  ```
  $ for i in 1 2 3; do /tmp/orion-venv/bin/python -c "import generator_v2 as G, hashlib; \
      cases = G.generate('balance_conservation', 4, seed=461, regime='base', tag='train'); \
      print(hashlib.sha256('|'.join(c.prompt for c in cases).encode()).hexdigest()[:16], cases[0].case_id)"; done
  4a54ccf4407f0c79 balv2-base-0-train        # run 1
  2e8211f9d685b48b balv2-base-0-train        # run 2  <- same id, different content
  c313cc2809ee0487 balv2-base-0-train        # run 3
  ```
  With `PYTHONHASHSEED=0` exported before launch the digest is stable across processes (`4fe8d83a5b751471` twice), proving the tuple hash is the sole source of nondeterminism.
- **Fix sketch**: derive the seed the way `exposure_executor.py:371` already does two directories over:
  ```python
  salt = int.from_bytes(sha256(f"{seed}|{family}|{regime}|{style}|{tag}".encode()).digest()[:4], "big")
  rng = random.Random(salt)
  ```
- **Severity**: BREAKS_REPRODUCIBILITY (headline).

### R2. `seed_everything`'s `os.environ.setdefault("PYTHONHASHSEED", …)` is a no-op for the running interpreter — the determinism guard documents a protection it does not provide

- **Where**: `experiments/training_ladder/exposure_executor.py:468` (inside `seed_everything`, called from `lora_finetune` and `run`).
- **What breaks, for whom**: setting `PYTHONHASHSEED` after interpreter start does not affect `str`/`tuple` hashing in the current process (CPython reads it once at startup). The line only influences *future subprocesses*, none of which are spawned here. An engineer reading `seed_everything` reasonably concludes builtin-hash-derived values are pinned; they are not — which is exactly the hole R1 falls through, because `phase1_v2.run()` builds its pools via `generator_v2.generate` in the same process.
- **VERIFIED**:
  ```
  $ /tmp/orion-venv/bin/python -c "import os; os.environ.setdefault('PYTHONHASHSEED','461'); \
      print(hash('balance_conservation') & 0xFFFF)"
  12892   # run 1
  25879   # run 2  <- setdefault had no effect on in-process hashing
  ```
- **Fix sketch**: either fail fast (`if os.environ.get("PYTHONHASHSEED") != str(seed): raise/re-exec`) or delete the line and ban builtin `hash()` from anything seed-bearing (R1 fix makes it moot). Comment at `exposure_executor.py:370` already states the correct rule; enforce it.
- **Severity**: BREAKS_REPRODUCIBILITY.

### R3. Committed `results/path_quotient_savings.json` is unreproducible at HEAD: `path_equivalence` semantics changed underneath the experiment, and the experiment's own consistency gauge now fails

- **Where**:
  - API change: `src/rakl/path_equivalence.py:116-171` (`equivalent_under_declared_partial_order` now returns `True` only when histories differ by adjacent swaps each certified by a `TransitionIndependenceWitness`; commit `f7495741 "framework: require certified independence for path quotienting"`).
  - Stale caller: `research/unified_problem_solving_v1/path_quotient_experiment.py:215-217` calls the predicate **without witnesses**; `path_quotient_experiment.py:329-339` (`api_notes`) documents the *previous* semantics ("reflexive only on dependency-respecting histories…").
  - Timeline proof: `git log` shows the experiment last committed at `067d41c2`, *before* `f7495741`.
- **What breaks, for whom**: the committed result JSON records `equivalence_spot_failures = 0` across all 3,200 instances and the Paper V figure `unified_path_quotient` is generated from this experiment family. Re-running the experiment at HEAD produces nonzero spot failures — i.e., the published mechanism-consistency claim ("signature identity agrees with the API's pairwise equivalence predicate") is false against the current API. A reviewer re-running the pipeline gets numbers that contradict the committed artifact; the experiment's honesty instrument correctly detects the break, but nothing runs it (see C2).
- **VERIFIED**:
  ```
  $ PYTHONPATH=src /tmp/orion-venv/bin/python -c "import sys; sys.path.insert(0,'research/unified_problem_solving_v1'); \
      import random; from path_quotient_experiment import run_instance; \
      print(run_instance(4, 1.0, 0, random.Random(123)))"
  ... 'spot_checks': 6, 'spot_failures': 4 ...     # committed JSON: 0 failures total
  ```
- **Fix sketch**: update the experiment to register `TransitionIndependenceWitness` objects from its executed commutation checks (it already has exactly the right evidence in `witness_phase`) and pass them via `independence_witnesses=…, context_hash=…`; regenerate the JSON; update the stale `api_notes`; and add the experiment to CI (C2) so API/caller divergence fails loudly next time.
- **Severity**: BREAKS_REPRODUCIBILITY.

---

## BREAKS_ADOPTER

### A1. The `orion`→`rakl` alias loads every submodule TWICE; enum identity (`is`) checks fail across the boundary — verified silent bypass of the preservation-receipt invariant

- **Where**: `src/orion/__init__.py:18` (`sys.modules[__name__] = _impl`). Victim example: `src/rakl/solver_compilation.py:131` (`if self.status is CompilationStatus.VALIDATED_FOR_ROUTING:`). The same `is`-based pattern guards invariants in `operational_map.py:96`, `path_equivalence.py:64-66`, `mechanic_diagnosis.py:63`, `solution_assembly.py:80`.
- **What breaks, for whom**: replacing `sys.modules["orion"]` with the `rakl` module object makes `import orion.solver_compilation` re-execute `src/rakl/solver_compilation.py` under the name `orion.solver_compilation`, producing a **second, distinct module object** with its own enum classes. The handoff brief says "New code should import `orion`", while the entire test suite, research scripts, and internals import `rakl` — so a mixed codebase is the *expected* state for an adopter. Any enum value that crosses the boundary fails `is` checks silently. Consequence is not a crash: dataclass `__post_init__` invariants that gate on `is` simply don't fire.
- **VERIFIED**:
  ```
  $ PYTHONPATH=src /tmp/orion-venv/bin/python -c "
  import orion.solver_compilation as osc, rakl.solver_compilation as rsc
  print(osc is rsc)                                    # False  <- double-loaded
  c = rsc.SolverCompilationCandidate('c1','ph','sh','qoi','rep','tr','sol',None,'ver',
      claimed_effects=(rsc.TransformationEffect.RELAX,),
      status=osc.CompilationStatus.VALIDATED_FOR_ROUTING)   # orion-side enum
  print(c.status, c.preservation_receipt)"
  CompilationStatus.VALIDATED_FOR_ROUTING None
  ```
  A candidate claiming `VALIDATED_FOR_ROUTING` **with no preservation receipt** is accepted — the exact invariant commit `1bdf9101`'s hardening pass added. Same test with the rakl-side enum raises `ValueError` as intended. Also verified: `orion.operational_map.MapEdgeStatus is rakl.operational_map.MapEdgeStatus` → `False`.
- **Fix sketch**: alias at the submodule level instead of swapping the package object — install a `importlib.abc.MetaPathFinder` that maps `orion.X` → the already-imported `rakl.X` module object (`sys.modules[f"orion.{x}"] = sys.modules[f"rakl.{x}"]`), guaranteeing one module object per file. Alternatively compare enums with `==` (they are `str` enums) everywhere invariants gate behavior — but single-load is the sound fix.
- **Severity**: BREAKS_ADOPTER (silently defeats freshly-hardened safety invariants).

### A2. NaN passes every cost guard and *wins* path selection

- **Where**: `src/rakl/path_cost.py:87-89` (`any(getattr(self, name) < 0 …)` — `NaN < 0` is `False`), `path_cost.py:134-147` (`dominates`/`admissible_pareto_frontier` — NaN never dominates and is never dominated), `path_cost.py:158` (`min(…)` over tuples containing NaN is order-dependent), `src/rakl/fieldability.py:110-112` and `126-132`, `src/rakl/solver_compilation.py:125-126`.
- **What breaks, for whom**: one upstream `0/0` (e.g., a rate computed over an empty window) yields a NaN cost that (a) constructs successfully, (b) permanently pollutes the Pareto frontier, and (c) can be *selected* by `explicit_lexicographic_select` — the framework's registered tie-break-safe chooser routes to a path with undefined cost, silently. `amortization_break_even_queries(build_cost=nan, …)` returns `nan` instead of raising, poisoning downstream comparisons (`nan <= threshold` is `False` in every direction).
- **VERIFIED**:
  ```
  $ PYTHONPATH=src /tmp/orion-venv/bin/python -c "…"
  frontier: ['good', 'nan-path']       # NaN option kept on the frontier
  lex pick: nan-path                    # NaN option WINS lexicographic selection
  break_even with NaN build: nan        # fieldability silently propagates NaN
  ```
- **Fix sketch**: in each numeric `__post_init__`/function guard, replace `x < 0` with `not (x >= 0)` (catches NaN) or explicit `math.isnan` rejection; add a NaN case to `tests/test_unified_solver_framework.py`.
- **Severity**: BREAKS_ADOPTER (violates the module's own "noncompensatory admissibility before comparison" contract: an *undefined* cost buys selection).

### A3. Training-ladder v2 "disjoint by construction" is ID-disjoint only; verified exact-prompt leakage from train pool into the SAME_STRUCTURE probe, and the runtime leakage check is vacuous

- **Where**: claim at `experiments/training_ladder/generator_v2.py:14` ("train and probe instances are DISJOINT by construction"); check at `experiments/training_ladder/phase1_v2.py:65-69` compares `case_id` sets whose `-train`/`-probe` tag suffixes make collision *impossible by construction* — the `raise` is unreachable.
- **What breaks, for whom**: train and probe pools are independent draws from the same finite distribution (e.g., `balance_conservation` base regime has ≲ 40·39·7 ≈ 10k distinct renderings but heavy mass on small values). Identical prompts can (and do) appear in both pools; the "held-out" SAME_STRUCTURE accuracy — the learnability gate and mastery signal for the whole Phase-1 v2 terminal classification (`phase1_v2.py:73-107`) — is partially memorization-measurable. This is precisely the failure class the v2 rewrite claims to have fixed after the v1 retraction.
- **VERIFIED** (content comparison under `PYTHONHASHSEED=0` for determinism):
  ```
  balance_conservation train_unique_prompts= 63 probe_in_train= 1 ['balv2-base-10-probe']
  ```
  One of 16 SAME_STRUCTURE probe prompts is byte-identical to a training prompt at the frozen seed 461 / max_exposure 64 configuration; the training pool itself contains a duplicate (63/64 unique).
- **Fix sketch**: make `assert`/leakage checks compare rendered `(prompt, gold)` content, not ids; enforce disjointness constructively (generate probe instances by rejection against the train prompt set); dedupe the train pool.
- **Severity**: BREAKS_ADOPTER (instrument-validity defect in the corrected instrument; also undermines any reproduced result's interpretation).

### A4. `diagnose_mechanic_signals` silently swallows unrecognized signal names — a one-character typo flips the verdict with no indication anything was ignored

- **Where**: `src/rakl/mechanic_diagnosis.py:103` (`_SIGNAL_RULES.get(signal, (MechanicCause.UNKNOWN,))`); registry at `mechanic_diagnosis.py:75` is a plain mutable module-level `dict`.
- **What breaks, for whom**: signals are free-form strings (not an enum). Any unmapped string — typo, renamed telemetry key, adopter's raw observation — degrades to `UNKNOWN` and dilutes or replaces the verdict, without any field in the receipt recording that inputs were unrecognized. The diagnosis experiment itself documents this as a limitation, but the API offers no strict mode. Separately, extending the vocabulary requires mutating the module-global `dict` (process-global, no registration API, not coordinated across threads or across the orion/rakl double-load from A1 — the two copies of `_SIGNAL_RULES` can diverge).
- **VERIFIED**:
  ```
  signals=('portal_roundtrip_failed',)  -> MECHANIC_GAP_IDENTIFIED ['PORTAL_GAP']
  signals=('portal_roundtrip_faild',)   -> CANNOT_CHECK ['UNKNOWN']   # typo, no error, no warning
  ```
- **Fix sketch**: add `unrecognized_signals: Tuple[str, ...]` to `MechanicDiagnosisReceipt` and populate it; optional `strict: bool = False` kwarg that raises on unmapped names; freeze `_SIGNAL_RULES` behind `types.MappingProxyType` with an explicit `register_signal(...)` function.
- **Severity**: BREAKS_ADOPTER.

### A5. `phase1_v2.run()` calls `git rev-parse HEAD` unguarded — crashes on any non-git deployment, including the project's own handoff zip

- **Where**: `experiments/training_ladder/phase1_v2.py:114` (`subprocess.check_output(["git","rev-parse","HEAD"], cwd=str(HERE))`); contrast with the guarded `exposure_executor.py:839-850` (`_git_sha` with `try/except → "unknown"`), which phase1_v2 does not use.
- **What breaks, for whom**: `.github/workflows/unified-framework-handoff-zip.yml:44` builds the adopter bundle via `git archive` — the extracted tree has no `.git`. Any adopter (or SLURM scratch deployment, or Docker COPY of the source dir) running `phase1_v2.py` gets `CalledProcessError` at run start, after packet validation but before any training.
- **VERIFIED**: `git rev-parse HEAD` raises `subprocess.CalledProcessError` (exit 128, "not a git repository") when `cwd` is outside a repo; the call site has no handler.
- **Fix sketch**: `from exposure_executor import _git_sha; git_sha = _git_sha()`.
- **Severity**: BREAKS_ADOPTER.

### A6. No usable adoption surface for the unified mechanics: `import orion` exposes none of them, nothing re-exports them, and there is no worked example

- **Where**: `src/rakl/__init__.py` (no imports of `operational_map`, `path_equivalence`, `path_cost`, `fieldability`, `mechanic_diagnosis`, `solver_compilation`, `solution_assembly`, `unified_solver_registry` — verified by grep); `QUICKSTART.md` (covers only the CLI runtime); `HANDOFF_UNIFIED_FRAMEWORK.md:15-25` (lists files, zero usage code); `examples/minimal/` (CLI runner only). Additionally `src/rakl/unified_solver_registry.py:23,27` validates `module_path.startswith("src/rakl/")` and `test_paths` under `tests/` — repo-relative paths that are meaningless for an installed distribution (`pip install orion` ships no `src/` or `tests/` directories), so registry self-validation is unusable at exactly the point an adopter would run it.
- **What breaks, for whom**: an engineer told "adopt the 7 mechanics" gets `AttributeError` from every natural entry point and must reverse-engineer usage from `tests/test_unified_solver_framework.py` and research scripts — one of which (`field_hypothesis_experiment.py`) never imports the framework at all despite testing its central hypothesis, so it models the *wrong* integration pattern. Combined with A1 (the recommended `import orion` path is the one that double-loads), the first hour of any adoption fails.
- **VERIFIED**:
  ```
  import orion
  hasattr(orion, 'operational_map')                    # False
  hasattr(orion, 'OperationalMapReceipt')              # False
  hasattr(orion, 'validate_unified_solver_registry')   # False
  ```
- **Fix sketch**: re-export the seven mechanics' public names from `rakl/__init__.py` (they are small, dependency-light modules); add one end-to-end example script (map → reachability → cost/admissibility → diagnosis → compilation → assembly) under `examples/`; make registry path validation relative-to-package (e.g., validate `rakl/<module>.py` resolvable via `importlib.util.find_spec`).
- **Severity**: BREAKS_ADOPTER.

---

## PERF_CLIFF

### P1. `add_edge` is O(n) per call with full receipt re-validation — incremental map construction is quadratic and measured at seconds by 8k edges

- **Where**: `src/rakl/operational_map.py:188-191` (`{item.edge_id for item in receipt.edges}` set rebuild + tuple concat per call) plus `OperationalMapReceipt.__post_init__` (`operational_map.py:111-129`) re-running the O(n) uniqueness scan on every `replace`.
- **What breaks, for whom**: the only mutation API for the map. An agent materializing a real operational map edge-by-edge (the intended usage: register each verified transition as it is replay-verified) hits a quadratic wall. Measured: 1k edges 0.02 s, 2k 0.14 s, 4k 0.47 s, 8k 2.36 s (clean ~4× per doubling). Extrapolation: 50k edges ≈ 90 s, 200k ≈ 25 min — for *map construction alone*, before any BFS.
- **VERIFIED**: timing loop above run against HEAD code (function body unchanged by the mid-audit rewrite).
- **Fix sketch**: an `add_edges(receipt, edges: Iterable)` bulk constructor validating once; or an internal builder carrying a frozen `frozenset` of edge ids so both the duplicate check and `__post_init__` are O(new edges).
- **Severity**: PERF_CLIFF.

### P2. The path-quotient usage pattern enumerates all k! orderings even on the "quotient-aware" side — the API offers no way to enumerate equivalence classes without a full factorial sweep

- **Where**: `research/unified_problem_solving_v1/path_quotient_experiment.py:188-196` (the quotient searcher iterates `permutations(range(k))` and calls `canonical_partial_order_trace` per ordering; only *world executions* are saved, never enumeration); no class-representative enumerator exists in `src/rakl/path_equivalence.py`.
- **What breaks, for whom**: this experiment is the sole worked exemplar of the path-equivalence mechanic, and it teaches an O(k!) pattern. Measured: `canonical_partial_order_trace` ≈ 10 µs/history at k=8 → 40,320 orderings in 0.4 s; extrapolated k=10 ≈ 1 min, k=12 ≈ 1.6 h+ (and per-trace cost grows with k²). Any adopter applying "quotient the interleavings" to a 12-step trace with the demonstrated pattern hits hours; at k=15 it is unreachable. The paper-level savings framing ("net saving = naive − (classes + witness_checks)") counts world executions only and hides the factorial enumeration cost entirely.
- **VERIFIED**: timing sweep at k=8 with chain dependencies, extrapolation stated above.
- **Fix sketch**: add a generator of canonical class representatives (topological linear extensions of the dependency poset — e.g., Varol–Rotem enumeration, or Foata normal form per trace-monoid class) so class count/classes are produced in output-polynomial time; document the enumeration cost in the experiment's `net_saving_definition`.
- **Severity**: PERF_CLIFF.

---

## CI_DRIFT

### C1. The hardening workflow regenerates figures into `paper/figures/generated/` but compiles the papers from committed per-paper copies — "receipt-bound publication figures" are not actually bound to the shipped PDFs

- **Where**: `.github/workflows/unified-framework-hardening.yml:59-70` (regenerate + existence asserts on `paper/figures/generated/*`) vs. `publication/papers/paper-05-verified-discovery-in-mathematics/sections/11_verified_transformation_geometry.tex:143-144` (`\includegraphics{figures/unified_local_vs_closed_loop.pdf}` — the paper's own `figures/` directory). Papers are now self-contained (`publication/papers/*/figures/` hold committed copies); the workflow has **no step** copying regenerated figures into them and **no diff** between regenerated and committed copies.
- **What breaks, for whom**: if experiment results or figure code change, CI regenerates fresh figures, asserts they exist, then compiles PDFs embedding the *stale committed* copies — and passes. The uploaded artifact bundle contains both, silently inconsistent. Same gap for data: step 57-58 recomputes `known_world_stress.json` but never runs `git diff --exit-code` against the committed file (it happens to byte-match today — verified — but nothing enforces it).
- **Fix sketch**: after regeneration, `cp` the unified figure set into each paper's `figures/` and `git diff --exit-code -- publication/papers/*/figures paper/figures/generated research/unified_problem_solving_v1/results/known_world_stress.json`.
- **Severity**: CI_DRIFT.

### C2. The workflow claims to harden `research/unified_problem_solving_v1/**` but never executes the three experiments; registry-declared test files are neither run nor in the trigger paths

- **Where**: `.github/workflows/unified-framework-hardening.yml:15` (trigger on `research/unified_problem_solving_v1/**`) vs. steps 51-58 which run only `run_known_world_stress.py` — `path_quotient_experiment.py`, `diagnosis_accuracy_experiment.py`, `field_hypothesis_experiment.py` are never executed by any workflow (verified by grep across `.github/workflows/`). Also: `src/rakl/unified_solver_registry.py:59-63` now registers `navigation_quotient_validation` with tests in `tests/test_vtg_closure_contracts.py`, but the workflow's pytest step (line 54) runs only `tests/test_unified_solver_framework.py tests/test_unified_solver_registry.py`, and the trigger `paths` block (lines 5-14) lists neither `src/rakl/navigation_quotient.py` nor `tests/test_vtg_closure_contracts.py`.
- **What breaks, for whom**: this is precisely how R3 shipped — the API changed, the experiment's built-in consistency check now fails, and no CI job noticed, while the workflow's name and trigger paths advertise coverage of exactly those files. A change to `navigation_quotient.py` does not even *trigger* the hardening job, let alone run its declared tests.
- **Fix sketch**: run the three experiment scripts (or a `--n-instances`-reduced smoke mode) and assert `EQUIVALENCE_SPOT_FAILURES=0` / `CLASS_OUTCOME_MISMATCHES=0` from their stdout; derive the pytest file list from `UNIFIED_SOLVER_MECHANICS[*].test_paths` instead of hardcoding; add the two missing paths to the trigger.
- **Severity**: CI_DRIFT.

### C3. The Phase-1 v2 instrument (generator_v2 / phase1_v2) has zero test and zero CI coverage

- **Where**: no reference to `generator_v2` or `phase1_v2` anywhere in `tests/` or `.github/workflows/` (verified by grep). The v1 instrument's defects motivated a retraction (`generator_v2.py:1-18` docstring); the corrected instrument shipped with no regression guard, which is how R1 (non-reproducible seeding) and A3 (vacuous leakage check) exist simultaneously in the "fixed" version.
- **Fix sketch**: unit tests asserting (a) two fresh subprocesses produce identical `generate(...)` output (cross-process determinism — catches R1 by construction), (b) rendered train/probe prompt sets are disjoint (catches A3), (c) pools are label-balanced; wire into `test.yml`.
- **Severity**: CI_DRIFT.

---

## MINOR

### M1. `verified_reachability` never checks that start/target belong to the map — a typo'd state id on a certificate-bearing map returns the strongest negative verdict instead of `CANNOT_CHECK`

- **Where**: `src/rakl/operational_map.py:194-257`; no membership test against edge endpoints or `coverage_coordinates`.
- **Consequence**: `start_state_id="s1 "` (trailing whitespace) on a certified-complete map yields `NO_VERIFIED_ROUTE_COVERAGE_COMPLETE` with `establishes_no_route_under_registered_map=True`. The mid-audit hardening already demoted `establishes_mathematical_impossibility` to constant `False` (good), but the registered-map-closure claim is still mintable from an id that the map has never seen.
- **Fix**: return `CANNOT_CHECK (unknown_state_id)` when start/target appear in neither edge endpoints nor coverage coordinates.

### M2. Content-hash conventions are internally inconsistent and insertion-order-sensitive

- **Where**: `src/rakl/operational_map.py:12` hashes with `ensure_ascii=False`; `src/rakl/path_equivalence.py:11` and `src/rakl/solution_assembly.py:18` use the default `ensure_ascii=True` — the same logical payload hashes differently depending on which module's `_hash` it flows through whenever non-ASCII appears in ids/scopes. `OperationalMapReceipt.content_hash` (`operational_map.py:136-159`) serializes `edges` in insertion order, so two maps with identical edge *sets* built in different orders get different content hashes (dedup/idempotency misses; `solution_assembly.proof_dag_content_hash` sorts its nodes/edges, showing the intended convention). All hashes are stable within one convention (json float repr is deterministic in CPython 3); this is an interop wart, not R1-class.
- **Fix**: one shared `canonical_sha256` helper; sort edges by `edge_id` in the content-hash payload.

### M3. `_evaluate`'s `(0.0, 0)` "no measurement" convention leaks into persisted rows

- **Where**: `experiments/training_ladder/exposure_executor.py:531-544` documents that `(0.0, 0)` must never be read as a real zero; `phase1_v2.py:131-137` and `exposure_executor.run` still *emit* rows with `accuracy: 0.0, n: 0` into the outcome JSONL. In-repo consumers filter `n<=0`, but the JSONL is the exchange format — any external consumer averaging `accuracy` inherits fake zeros.
- **Fix**: emit `accuracy: null` when `n == 0` (and teach `validate_outcome_row` the pairing).

### M4. Two silent-degradation spots in the generators/frontier

- `experiments/training_ladder/generator_v2.py:105-124`: after 200 failed rejection-sampling attempts the reachability generator falls back to `target = nodes[-1]` regardless of the requested class — label balance and the length-matching guarantee can silently degrade (gold stays correct; the *distribution* contract doesn't).
- `src/rakl/path_cost.py:144`: options sharing a `path_id` never dominate each other (`other.path_id != candidate.path_id`), so duplicate-id options with strictly ordered costs both survive the frontier silently; `admissible_pareto_frontier` is also O(n²), fine at experiment sizes but worth a note at ≥10⁴ options.
- **Fix**: count fallbacks and surface them in the manifest; raise on duplicate `path_id` inputs.

---

## Adoption verdict (engineering only)

The eight mechanic modules at HEAD are small, invariant-dense, and test-covered, and the mid-audit hardening (coverage certificates, witness-gated quotienting, preservation receipts) meaningfully tightened the semantics. But an adopter today inherits: a recommended import path that double-loads the library and silently disarms those same invariants (A1), a training instrument whose runs cannot be replicated (R1/R2) and whose held-out claim leaks (A3), a published experiment artifact the current API can no longer reproduce (R3) with the CI that advertises exactly that coverage not running it (C2), and no worked entry point (A6). All of R1, A1, A2 and R3 have one-day fixes; C2's test-path derivation and the figure-sync gate (C1) would have caught most of them automatically.
