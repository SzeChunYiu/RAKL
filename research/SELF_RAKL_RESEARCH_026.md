# Self-RAKL Round 026 — Protected Evaluator Dependency Pinning

Date: 2026-08-09  
Starting main: `11c8ccbffa65c4ef2922d85e5dcfc966f17fe7de`  
Class: B protected workflow trust-root migration  
Constitutional change: none

## Native residual

Previous successful GitHub Actions logs showed that stable workflow text still resolved `actions/checkout@v4` and `actions/setup-python@v5` dynamically to concrete action commits. Thus evaluator identity was under-typed: protecting workflow bytes did not protect the complete executable action dependency identity.

The incumbent parent evaluator correctly treats both workflow files as protected inputs. This makes N029 a trust-root migration problem rather than an ordinary implementation change.

## Frozen migration before workflow edits

`research/SELF_RAKL_RESEARCH_026_FROZEN_BENCHMARK.json` freezes:

- the exact parent workflow blob identities;
- the two official action commit SHAs already observed in successful runs;
- exactly four allowed `uses:` substitutions;
- unchanged triggers, permissions, runner image, Python version, checkout semantics, installation/test commands, parent-evaluator command, evaluator code, promotion code, `pyproject.toml`, tests and acceptance thresholds;
- security/reproducibility meta-QoIs;
- the expected **REJECT** outcome from the unchanged parent evaluator.

## Exact dependency identities

The migration pins:

```text
actions/checkout@11d5960a326750d5838078e36cf38b85af677262
actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
```

Both commits were verified to exist in the official GitHub action repositories and match the concrete action revisions in previous successful RAKL logs.

GitHub's current guidance treats a full-length action commit SHA as the immutable reference form and recommends verifying that the SHA belongs to the intended action repository rather than a fork. Therefore RAKL is adopting an established supply-chain practice, not claiming pinning as a novel method contribution.

## Meta-QoI change

Frozen baseline:

```text
mutable protected action references = 4
full-SHA protected action references = 0
```

Candidate:

```text
mutable protected action references = 0
full-SHA protected action references = 4
```

No other workflow semantic coordinate is authorized to change.

## Candidate execution

PR #3 was opened so the ordinary candidate test and unchanged parent evaluator could both observe the protected migration.

The exact candidate PR test on workflow head `194d96401a8cc64b59fa5e68d4a2887604680151` completed successfully with 303 tests. Its log shows the two candidate test action steps running at the frozen full SHAs.

The trusted parent evaluator then executed from parent revision `11c8ccbffa65c4ef2922d85e5dcfc966f17fe7de`, checked out exact candidate `194d964...` only as passive data, and returned the preregistered result:

```text
REJECT
protected input changed: .github/workflows/test.yml
protected input changed: .github/workflows/trusted-parent-evaluator.yml
```

The parent evaluator itself was not edited. This rejection is preserved as evidence that the protected-input firewall remains intact. It is not counted as a passing parent check.

## Why promotion can still be considered

An evaluator that can never change cannot receive security fixes. Conversely, letting the candidate weaken its own checker destroys the trust root. The migration therefore uses a narrower authority path that was frozen before the edits:

```text
external user authorization
+ exact old/new trust-root transformation
+ official dependency identity evidence
+ positive registered security meta-QoI
+ exact candidate execution
+ expected incumbent parent rejection
+ exact diff review
+ immediate main recheck
→ one-time protected trust-root supersession
```

This does not create a general mechanism by which future candidates can bypass the parent evaluator. A separate child fiber (`META_N089_EVALUATOR_TRUST_ROOT_MIGRATION_PROTOCOL`) must formalize or replace this migration procedure before another protected trust-root upgrade.

## Apple / atlas interpretation

The workflow file and the resolved action implementations are compatible local descriptions of one evaluator only through explicit resolution maps:

```text
workflow uses reference
→ action repository
→ exact action commit
→ runner image/toolchain
→ executed evaluator observation
```

Pinning closes the action-commit coordinate but does not force the whole chain into one falsely complete identity. Hosted runner image, dependencies and service behavior remain separate open coordinates.

## Remaining trust residual

`ubuntu-latest` remains a mutable evaluator dependency. Round 026 therefore opens `META_N090_EVALUATOR_RUNNER_IMAGE_IDENTITY`. The next step should benchmark whether hosted image identity needs stronger freezing/containerization or whether exact observed image/version metadata is sufficient for the registered evaluator decisions.

## Novelty boundary

Do not claim full-SHA dependency pinning, action supply-chain provenance or immutable software references as RAKL novelty. The potentially interesting RAKL governance question is how a recursively self-improving scientific method can migrate a protected evaluator trust root while preserving the old checker, frozen falsifiers and supersession history.

## Saturation

Engineering lane remains `ACTIVE_NON_FLAT`. Same-context flat rounds = 0 and independent flat rounds = 0 because evaluator dependency identity improved while the runner/toolchain trust boundary reopened as a native residual.
