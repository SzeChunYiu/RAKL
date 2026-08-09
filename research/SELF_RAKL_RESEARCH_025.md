# Self-RAKL Round 025 — Token Budget Authority and Release Artifact Identity

Date: 2026-08-09  
Starting main: `70b3ae7489e0c288c80dd006344f8634ee80bb0b`  
Class: A supporting implementation plus research  
Constitutional change: none

## Residual

By Round 024, RAKL could initialize a project, content-address evidence, compile a bounded task packet, execute a local/provider adapter through a governed envelope, archive raw outputs, and replay completed local invocations. Two package-level authority gaps remained:

1. context/token metadata was useful for planning but not an exact measurement tied to the actual tokenizer/counter used by a model family;
2. source revision did not by itself identify built wheels, papers, benchmark packets, results, or other detached release artifacts.

These gaps affect reproducibility, but neither should be allowed to become scientific truth authority.

## Panel

The same-context panel used five engineering projections plus an adversarial reviewer:

- LLM/tokenization systems engineer;
- prompt/context-budget engineer;
- software supply-chain/provenance engineer;
- Python packaging/release engineer;
- research-artifact reproducibility engineer;
- adversarial path/tamper/authority reviewer.

These role-separated passes are not independent review.

## Frozen benchmark

`research/SELF_RAKL_RESEARCH_025_FROZEN_BENCHMARK.json` was committed before implementation. It registers twenty worlds covering exact counter identity, counter failures, strict `CANNOT_CHECK`, budget boundaries, shell safety, deterministic manifest construction, file tamper/missing detection, symlink/path escape, duplicate identity, source revision format, manifest self-integrity, real wheel build identity, and engineering/scientific authority separation.

## Token measurement calculus

RAKL now distinguishes an estimate from an executed measurement. `TokenCountCertificate` binds exact packet bytes to a counter ID, counter revision, argv digest and measured integer token count. Its authority is `EXACT_EXECUTED_COUNTER` with scope `ENGINEERING_TOKEN_MEASUREMENT_ONLY`.

Strict packet certification refuses to treat existing declared `token_cost` metadata as exact. With no exact counter, the result is `CANNOT_CHECK`. With an exact certificate, the packet is compared to the selected reference profile's registered input plus protocol reserve and returns `WITHIN_BUDGET` or `OVER_BUDGET`.

This intentionally avoids a universal tokenizer assumption. A hosted provider whose actual tokenizer implementation cannot be established remains a scoped/partially identified transition rather than being equated to a local counter by model name.

## Release artifact identity

`ReleaseManifest` binds a full 40-hex source revision to deterministic artifact entries containing role, relative path, exact SHA-256, and byte size. The manifest has its own self-digest and explicitly carries authority `ENGINEERING_ARTIFACT_IDENTITY_ONLY`.

Manifest construction and verification reject absolute paths, `.`/`..` components, path escape, symlinks, non-files, and duplicate role/path identities. Verification re-hashes exact bytes and reports changed or missing artifacts rather than repairing them.

A known-answer test builds a real wheel with the repository's current build backend, places the wheel in a release root, creates the manifest, and verifies the exact distribution artifact. This demonstrates identity of that built wheel, not bit-for-bit reproducibility across independent build environments.

## User-facing commands

```text
python -m rakl certify-packet ...
python -m rakl release-manifest ...
python -m rakl verify-release ...
```

The runtime remains standard-library only. Model/tokenizer implementations remain external adapters.

## External prior art and novelty boundary

Hugging Face's tokenizer architecture makes tokenizer pipelines/models/configuration explicit; RAKL therefore does not claim tokenizer-specific counting as novel. SLSA build provenance and Python packaging standards already use output artifact identities and reproducible environment/distribution concepts. Release digests, wheels, provenance, tokenizers, and manifests are infrastructure, not headline RAKL novelty.

The RAKL-specific research question is whether keeping token/artifact authority explicitly scoped and connected to context compilation, execution receipts, evidence governance and separately controlled promotion reduces hidden reproducibility/authority errors in scientific-agent workflows.

## Executed support evidence

Implementation candidate `38eb2141cc7b9cfb1c9c6211d2809231122f5fa8` passed 303 tests in 8.13 seconds on its exact GitHub Actions checkout, including the real wheel-build identity test.

The final research candidate must be retested after all documentation/receipt commits before promotion.

## Remaining engineering closure

The largest trust gap is now `META_N029_EVALUATOR_DEPENDENCY_PINNING`: protected workflow text still references mutable action tags rather than exact action commit SHAs. Other open engineering residuals are runner artifact/environment attestation, real model/tokenizer compatibility, independent/reproducible distribution builds, archival release identity, and workflow-level durable research execution.

## Scientific closure boundary

Token and release identity improvements do not close RAKL's scientific evidence case. Exact claim-evidence provenance, real matched baselines/ablations, historical cutoff evaluation and independent formal/adversarial/artifact review remain necessary before broad superiority/closure claims.

## Saturation

`ACTIVE_NON_FLAT`. Same-context flat rounds = 0 and independent flat rounds = 0 because Round 025 retained new executable engineering authority distinctions and opened concrete model/build/archive residuals.
