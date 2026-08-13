# Security, supply-chain, and migration hardening

## Commitment invariants

A commitment used as an integrity boundary must be independent of ambient interpreter state that is not explicitly part of the domain.

The canonical commitment here therefore:

- rejects non-finite floats;
- encodes finite floats by IEEE-754 binary64 bits;
- encodes Decimal numeric values without arithmetic/context rounding;
- rejects cycles and unsupported types;
- types list/tuple/set/mapping/dataclass rather than flattening them;
- uses explicit Unicode policy;
- uses domain-separated digests.

Do not call the RAKL NFC-normalizing legacy scheme “RFC 8785/JCS”. If JCS is required at an interoperability boundary, implement/verify JCS separately.

## Legacy identity migration

Never replace a historical hash in place merely because the new hash is stronger.

Recommended sequence:

```text
release N:   compute legacy + new canonical commitment; verify linkage
release N+1: make new commitment mandatory for new assurance-bearing artifacts
release N+2: retire legacy only after all consumers/manifests migrate
```

Every migration receipt should include old digest, new digest, object/schema identity, base commit, builder version and verification outcome.

## Authority roots

Internal regression HMAC keys/manifest entries are fixtures. Production authority requires externally governed key custody or attestation service and explicit trust-policy versioning.

Rules:

- proposer cannot authorize its own promotion;
- runtime caller cannot add a trust root by supplying a key;
- subject/evidence/evaluator bytes are content-bound;
- chronology is checked;
- revocation/supersession are authority-bearing transitions too;
- derived views do not inherit authority by name alone.

## Build provenance

For release-bearing generated artifacts, bind at least:

```text
source commit/tree
builder code hash
builder/config parameters
input content roots
environment/toolchain identity
output digest
build timestamp/clock semantics
```

Prefer repository-native/SLSA-compatible provenance rather than inventing a second incompatible build-attestation system.

## CI integration

Do not overwrite current workflows from an old packet. The receiving AI should:

1. inspect current workflow paths/triggers;
2. add focused tests for the new contracts;
3. retain experiment byte/staleness gates already on `main`;
4. add migration-drift tests for legacy/new commitments;
5. fail closed on changed generated artifacts;
6. run full native suite and paper builds.
