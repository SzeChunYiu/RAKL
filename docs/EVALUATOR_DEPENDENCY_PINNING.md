# Evaluator Dependency Pinning

Status: one-time protected evaluator trust-root migration  
Date: 2026-08-09

## Problem

A workflow file can be byte-stable while its referenced action implementation changes if it uses a mutable tag such as `actions/checkout@v4`. RAKL therefore distinguishes:

```text
workflow source identity
!=
resolved action implementation identity
```

Round 026 freezes a one-time migration from the four protected mutable action references to the exact full action commit SHAs that were already observed in successful evaluator executions.

## Frozen migration

Only these substitutions are authorized:

```text
actions/checkout@v4
→ actions/checkout@11d5960a326750d5838078e36cf38b85af677262

actions/setup-python@v5
→ actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
```

The first SHA was independently resolved in the official `actions/checkout` repository and the second in the official `actions/setup-python` repository. They match the concrete action revisions recorded by the prior successful GitHub Actions execution logs.

The migration changes four `uses:` references in total:

- one checkout reference in `.github/workflows/test.yml`;
- one setup-python reference in `.github/workflows/test.yml`;
- two checkout references in `.github/workflows/trusted-parent-evaluator.yml`.

No workflow trigger, permission, runner image, Python version, checkout ref/path/credential setting, pip command, pytest command, parent-evaluator command, evaluator code, promotion code, `pyproject.toml`, or pre-existing test is permitted to change under this migration.

## Why the existing parent evaluator rejects the candidate

`src/rakl/parent_evaluator.py` treats the protected workflows as immutable evaluator inputs. That is intentional. A protected trust-root change must not become ordinary merely because the proposed change is security-motivated.

The Round-026 PR therefore exercises the unchanged parent evaluator and expects it to report:

```text
REJECT
protected input changed: .github/workflows/test.yml
protected input changed: .github/workflows/trusted-parent-evaluator.yml
```

That rejection is preserved as evidence that the protected-input firewall remains operational. RAKL does not edit the parent evaluator or relabel this rejection as a passing parent check.

## Migration authority

This Class-B migration is authorized only by the conjunction of:

1. explicit user authorization to complete the engineering/trust chain;
2. a benchmark frozen before the workflow edits;
3. an exact transformation whitelist;
4. official-repository verification of both full action SHAs;
5. the fact that the pinned SHAs match the already observed successful action resolutions;
6. an exact-SHA candidate test run;
7. measured meta-QoI improvement;
8. preservation of the expected parent-evaluator rejection;
9. an immediate `main` identity recheck before a non-forced fast-forward.

This is a one-time trust-root migration rule, not a general exception allowing future protected workflow changes.

## Registered meta-QoIs

Before migration:

```text
mutable action references in protected workflows = 4
full-SHA action references in protected workflows = 0
```

Required candidate state:

```text
mutable action references = 0
full-SHA action references = 4
non-dependency workflow semantic changes = false
```

Thus the security/reproducibility benefit is separately measurable rather than inferred from intent.

## Upgrade lifecycle after pinning

Full-SHA pinning intentionally stops automatic action updates. Future action upgrades should therefore be explicit method/evaluator changes:

```text
current pinned action SHA
→ security/bug/update residual
→ candidate new action SHA
→ source/repository verification
→ frozen evaluator migration benchmark
→ exact candidate tests
→ protected migration authorization
→ supersession receipt
```

RAKL should never silently move a pinned SHA merely because a major-version tag changed.

## Authority boundary

Pinning evaluator dependencies strengthens the identity of the code used to run evaluation. It does not establish that the test suite is scientifically sufficient, that the runner image is immutable, that package dependencies are fully pinned, or that the model/scientific conclusion is true.

Those remain separate coordinates in evaluator influence closure.
