# Release Artifact Identity

Status: supporting publication/reproducibility contract  
Date: 2026-08-09

## Purpose

A publishable RAKL artifact needs an exact answer to the question:

> Which files, built distributions, benchmark packets, paper/support files, and result artifacts does this release claim refer to?

Git commit identity alone does not identify a wheel built later, a generated PDF, or a detached benchmark/result file. RAKL therefore provides a deterministic release-artifact manifest.

## Manifest object

A manifest binds:

```text
manifest protocol version
full 40-hex source revision
artifact role
relative artifact path
exact file SHA-256
exact byte size
authority scope
manifest self-digest
```

The manifest authority scope is:

```text
ENGINEERING_ARTIFACT_IDENTITY_ONLY
```

A verified digest establishes identity/integrity of the measured bytes. It does not establish scientific correctness of those bytes.

## Path safety

Release artifacts are evaluated under an explicit release root. The implementation rejects:

- absolute artifact paths;
- empty, `.` or `..` components;
- path traversal outside the release root;
- symlink artifacts or symlink path components;
- non-regular files.

This prevents the manifest from appearing self-contained while actually measuring a mutable external target through a symlink or escaped path.

## Determinism

Artifact role/path pairs are unique and sorted canonically before hashing. Supplying the same artifact set in a different input order produces the same canonical manifest bytes and self-digest.

The manifest itself is hashed over the unsigned canonical identity object. Verification recomputes this self-digest and then independently re-hashes every referenced artifact.

## Commands

Create a release manifest:

```bash
python -m rakl release-manifest ./release \
  --source-revision <40-hex-git-sha> \
  --artifact python-wheel:rakl-0.1.0-py3-none-any.whl \
  --artifact paper:RAKL-paper.pdf \
  --artifact benchmark:raklbench.json \
  --output ./release/RAKL_RELEASE_MANIFEST.json
```

Verify later:

```bash
python -m rakl verify-release ./release ./release/RAKL_RELEASE_MANIFEST.json
```

A changed or missing artifact returns `FAILED`; RAKL never repairs release bytes during verification.

## Relationship to supply-chain provenance

The current manifest is deliberately smaller than a full build-provenance system. It binds source revision and output artifacts by digest, but it does not yet establish builder identity, exact dependency resolution, hermeticity, or signed provenance.

Those concerns remain connected to RAKL's evaluator-dependency and runner-attestation fibers. Where a stronger SLSA/in-toto style attestation is available, it should be related to this local manifest through an explicit transition map rather than being conflated with scientific evidence.

## Wheel conformance

The test suite builds a real non-editable Python wheel from the repository using the current build backend, inserts that exact wheel into a release manifest, and verifies the artifact bytes. This tests distribution-artifact identity, not bit-for-bit reproducibility across two independent build environments.

Bit-reproducible distribution builds remain a distinct benchmarkable question.
